# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import frappe
from frappe.utils import nowdate, flt, cstr, get_datetime
from frappe import _
from erpnext.accounts.doctype.loyalty_program.loyalty_program import (
    get_loyalty_program_details_with_points,
)
from frappe.utils.caching import redis_cache
from posawesome.posawesome.api import customer
from .utils import get_active_pos_profile
from .vehicles import create_vehicle, get_vehicles_by_customer, _sync_vehicle_doctype
from frappe.exceptions import ValidationError, LinkValidationError, DoesNotExistError, NameError
from frappe.model.rename_doc import rename_doc as model_rename_doc

from decimal import Decimal, InvalidOperation

# Clarify doctypes:
VEHICLE_DOCTYPE = "Vehicle"  # ERPNext Vehicle doctype
VM_DOCTYPE = "Vehicle Master"  # Your custom Vehicle Master doctype (linked to Vehicle)


GCC_PHONE_RULES = {
    "BH": {"dial": "973", "len": 8},
    "KW": {"dial": "965", "len": 8},
    "OM": {"dial": "968", "len": 8},
    "QA": {"dial": "974", "len": 8},
    "SA": {"dial": "966", "len": 9},
    "AE": {"dial": "971", "len": 9},
}

GCC_COUNTRY_ALIASES = {
    "BH": "BH",
    "BAHRAIN": "BH",
    "KW": "KW",
    "KUWAIT": "KW",
    "OM": "OM",
    "OMAN": "OM",
    "QA": "QA",
    "QATAR": "QA",
    "SA": "SA",
    "SAUDI ARABIA": "SA",
    "SAUDI": "SA",
    "AE": "AE",
    "UAE": "AE",
    "UNITED ARAB EMIRATES": "AE",
}


def _resolve_gcc_iso(country_value, fallback_iso="BH"):
    key = cstr(country_value or "").strip().upper()
    if key in GCC_COUNTRY_ALIASES:
        return GCC_COUNTRY_ALIASES[key]
    return fallback_iso if fallback_iso in GCC_PHONE_RULES else "BH"


def _normalize_mobile_no(raw_value, country_value=None, fallback_iso="BH"):
    """Normalize mobile to E.164-style format using GCC country rules."""
    raw = cstr(raw_value or "").strip()
    if not raw:
        return ""

    digits = "".join(ch for ch in raw if ch.isdigit())
    if not digits:
        return ""

    iso = _resolve_gcc_iso(country_value, fallback_iso=fallback_iso)
    rule = GCC_PHONE_RULES.get(iso)
    dial = rule["dial"]
    national_len = int(rule["len"])

    if digits.startswith("00"):
        digits = digits[2:]

    national = digits
    if digits.startswith(dial) and len(digits) > len(dial):
        national = digits[len(dial) :]
    elif digits.startswith("0") and len(digits) == national_len + 1:
        national = digits[1:]

    if len(national) != national_len:
        country_label = iso
        for label, mapped_iso in GCC_COUNTRY_ALIASES.items():
            if mapped_iso == iso and len(label) > 2:
                country_label = label.title()
                break
        frappe.throw(
            _("Mobile number for {0} must be exactly {1} digits").format(country_label, national_len),
            ValidationError,
        )

    return f"+{dial}{national}"


# ---------------- LOYALTY POINTS FUNCTIONS ----------------
def auto_assign_loyalty_program(customer_doc):
    if customer_doc.loyalty_program:
        return customer_doc.loyalty_program

    program = frappe.db.get_value(
        "Loyalty Program",
        {
            "docstatus": 1,
            "auto_opt_in": 1,
            "company": frappe.defaults.get_user_default("Company"),
        },
        "name",
    )

    if program:
        frappe.db.set_value("Customer", customer_doc.name, "loyalty_program", program)
        return program

    return None


def get_loyalty_points(customer_name, loyalty_program=None, company_name=None):
    """Get current loyalty points balance for a customer"""
    try:
        # Build flexible query that works with or without loyalty_program/company
        conditions = ["customer = %(customer)s"]
        params = {"customer": customer_name}

        if loyalty_program:
            conditions.append(
                "(loyalty_program = %(loyalty_program)s OR loyalty_program IS NULL OR loyalty_program = '')"
            )
            params["loyalty_program"] = loyalty_program

        if company_name:
            conditions.append("(company = %(company)s OR company IS NULL OR company = '')")
            params["company"] = company_name

        # Include both draft (0) and submitted (1) entries
        conditions.append("docstatus = 1")

        where_clause = " AND ".join(conditions)

        query = f"""
            SELECT IFNULL(SUM(loyalty_points), 0) as total_points
            FROM `tabLoyalty Point Entry`
            WHERE {where_clause}
        """

        points_data = frappe.db.sql(query, params, as_dict=1)
        total_points = flt(points_data[0].total_points) if points_data else 0

        frappe.logger().debug(f"Loyalty Points - Customer: {customer_name}, Points: {total_points}")

        return total_points

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Get Loyalty Points Error"))
        frappe.logger().error(f"Error getting loyalty points: {str(e)}")
        return 0


@frappe.whitelist()
def update_loyalty_points(customer_name, company_name, points_amount):
    """
    Redeem customer loyalty points ONLY.
    Earning is handled via Sales Invoice on_submit hook.
    """
    try:
        # Validate inputs
        points_amount = flt(points_amount)
        if points_amount <= 0:
            return {
                "status": "error",
                "message": _("Points amount must be greater than 0"),
            }

        #  Get customer & loyalty program
        customer = frappe.get_doc("Customer", customer_name)

        if not customer.loyalty_program:
            return {
                "status": "error",
                "message": _("Customer {0} does not have a loyalty program assigned").format(customer_name),
            }

        loyalty_program = customer.loyalty_program
        loyalty_program_doc = frappe.get_doc("Loyalty Program", loyalty_program)

        redemption_amount = flt(points_amount)

        if flt(loyalty_program_doc.conversion_factor):
            redemption_amount = flt(points_amount * loyalty_program_doc.conversion_factor)

        # Check available points (Redeem ONLY)

        current_points = get_loyalty_points(customer_name, loyalty_program, company_name)

        frappe.logger().info(
            f"Redemption Check - Customer: {customer_name}, "
            f"Available: {current_points}, Requested: {points_amount}"
        )

        if current_points < points_amount:
            frappe.throw(
                _("Insufficient loyalty points. Available: {0}, Requested: {1}").format(
                    current_points, points_amount
                ),
                frappe.ValidationError,
            )

        #   Loyalty Point Entry (NEGATIVE only)

        loyalty_point_entry = frappe.get_doc(
            {
                "doctype": "Loyalty Point Entry",
                "customer": customer_name,
                "loyalty_program": loyalty_program,
                "company": company_name,
                "loyalty_points": -points_amount,
                "purchase_amount": redemption_amount,
                "expiry_date": frappe.utils.add_days(
                    frappe.utils.nowdate(),
                    loyalty_program_doc.expiry_duration or 365,
                ),
                "posting_date": frappe.utils.nowdate(),
                "posting_time": frappe.utils.nowtime(),
            }
        )

        loyalty_point_entry.insert(ignore_permissions=True)
        loyalty_point_entry.submit()
        frappe.db.commit()

        #  Return updated balance

        new_balance = get_loyalty_points(customer_name, loyalty_program, company_name)

        frappe.logger().info(
            f"Loyalty redeemed - Entry: {loyalty_point_entry.name}, New Balance: {new_balance}"
        )

        return {
            "status": "success",
            "message": _("Loyalty points redeemed successfully"),
            "points_redeemed": points_amount,
            "redemption_amount": redemption_amount,
            "new_balance": new_balance,
            "loyalty_point_entry": loyalty_point_entry.name,
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), _("Loyalty Points Redemption Error"))

        return {
            "status": "error",
            "message": _("Error redeeming loyalty points: {0}").format(str(e)),
        }


# ---------------- POS Customer Utilities ----------------


def get_customer_groups(pos_profile):
    """Return list of all child customer groups for a POS profile"""
    if isinstance(pos_profile, str):
        try:
            if not pos_profile.strip() or pos_profile.strip() in ['""', "''"]:
                pos_profile = {}
            else:
                pos_profile = json.loads(pos_profile)
        except json.JSONDecodeError:
            frappe.throw(_("Invalid POS Profile data passed to get_customer_groups"))

    customer_groups = []
    if pos_profile.get("customer_groups"):
        for data in pos_profile.get("customer_groups"):
            customer_groups.extend(
                [
                    "%s" % frappe.db.escape(d.get("name"))
                    for d in get_child_nodes("Customer Group", data.get("customer_group"))
                ]
            )
    return list(set(customer_groups))


def get_child_nodes(group_type, root):
    lft, rgt = frappe.db.get_value(group_type, root, ["lft", "rgt"])
    return frappe.get_all(
        group_type,
        filters={"lft": [">=", lft], "rgt": ["<=", rgt]},
        fields=["name", "lft", "rgt"],
        order_by="lft",
    )


def get_customer_group_condition(pos_profile):
    """Return SQL condition for customer groups based on POS profile."""
    cond = "disabled = 0"
    customer_groups = get_customer_groups(pos_profile)
    if customer_groups:
        escaped_groups = [frappe.db.escape_value(group) for group in customer_groups]
        cond = f" customer_group in ({', '.join(escaped_groups)})"
    return cond


# ---------------- POS Customer APIs ----------------


@frappe.whitelist()
def get_customer_names(pos_profile=None, limit=200, start_after=None, modified_after=None):
    """Fetch customers filtered by POS profile with pagination and optional caching"""

    if not pos_profile:
        active_profile_doc = get_active_pos_profile()
        pos_profile = active_profile_doc.as_json() if active_profile_doc else "{}"

    _pos_profile = json.loads(pos_profile)
    ttl = _pos_profile.get("posa_server_cache_duration")
    if ttl:
        ttl = int(ttl) * 60

    @redis_cache(ttl=ttl or 1800)
    def __get_customer_names(pos_profile, limit, start_after, modified_after):
        return _get_customer_names(pos_profile, limit, start_after, modified_after)

    def _get_customer_names(pos_profile, limit, start_after, modified_after):
        if isinstance(pos_profile, str):
            pos_profile = json.loads(pos_profile)

        filters = {"disabled": 0}
        customer_groups = get_customer_groups(pos_profile)
        if customer_groups:
            filters["customer_group"] = ["in", customer_groups]

        if modified_after:
            try:
                parsed_modified_after = get_datetime(modified_after)
            except Exception:
                frappe.throw(_("modified_after must be a valid ISO datetime"))
            filters["modified"] = [">", parsed_modified_after.isoformat()]

        if start_after:
            filters["name"] = [">", start_after]

        # Build a safe fields list — include is_company only if the DB actually has that column.
        base_fields = [
            "name",
            "mobile_no",
            "email_id",
            "tax_id",
            "customer_name",
            "primary_address",
        ]

        try:
            if frappe.db.has_column("tabCustomer", "custom_display_name"):
                base_fields.append("custom_display_name")
            # check for actual DB column. Use table name 'tabCustomer'
            if frappe.db.has_column("tabCustomer", "is_company"):
                base_fields.append("is_company")
        except Exception:
            # If has_column fails for any reason, skip optional fields (fail-safe)
            pass

        customers = frappe.get_all(
            "Customer",
            filters=filters,
            fields=base_fields,
            order_by="name",
            limit_page_length=limit,
        )
        return customers

    if _pos_profile.get("posa_use_server_cache") and not (start_after or modified_after):
        return __get_customer_names(pos_profile, limit, start_after, modified_after)
    else:
        return _get_customer_names(pos_profile, limit, start_after, modified_after)


@frappe.whitelist()
def get_customers_count(pos_profile=None):
    """
    Safely get customer count for POS Awesome.
    Prevents crash when no active POS profile is found.
    Returns: int (count only)
    """
    try:
        if not pos_profile:
            active_profile_doc = get_active_pos_profile()
            if not active_profile_doc:
                frappe.log_error(
                    "No active POS Profile found for current session.", "POS Awesome - get_customers_count"
                )
                return 0

        filters = {"disabled": 0}
        customer_groups = get_customer_groups(pos_profile or active_profile_doc.as_json())
        if customer_groups:
            filters["customer_group"] = ["in", customer_groups]

        count = frappe.db.count("Customer", filters)
        return count

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "POS Awesome - get_customers_count Error")
        return 0


def _existing_fields(doctype, candidates):
    """
    Return a list of candidate fieldnames that actually exist on the given doctype.
    Prevents SQL errors when different sites have slightly different doctype schemas.
    """
    try:
        meta = frappe.get_meta(doctype)
        existing = {f.fieldname for f in meta.fields}
        return [f for f in candidates if f in existing]
    except Exception:
        # be conservative: if meta lookup fails, only allow 'name'
        return [f for f in candidates if f == "name"] or ["name"]


def _resolve_customer_doc_for_pos(customer):
    """Resolve Customer doc safely for POS without throwing not-found errors."""
    customer_key = cstr(customer or "").strip()
    if not customer_key:
        return None

    # 1) Direct lookup by Customer.name
    try:
        if frappe.db.exists("Customer", customer_key):
            return frappe.get_doc("Customer", customer_key)
    except Exception:
        pass

    # 2) Fallback by customer_name (stale ID race after rename)
    try:
        alt_name = frappe.db.get_value("Customer", {"customer_name": customer_key}, "name")
        if alt_name:
            return frappe.get_doc("Customer", alt_name)
    except Exception:
        pass

    # 3) Optional fallback by custom_display_name
    try:
        if frappe.db.has_column("tabCustomer", "custom_display_name"):
            alt_name = frappe.db.get_value("Customer", {"custom_display_name": customer_key}, "name")
            if alt_name:
                return frappe.get_doc("Customer", alt_name)
    except Exception:
        pass

    return None


@frappe.whitelist()
def get_customer_info(customer):
    """Get comprehensive customer information including vehicles."""
    customer_doc = _resolve_customer_doc_for_pos(customer)
    if not customer_doc:
        fallback_name = cstr(customer or "").strip()
        return {
            "name": fallback_name,
            "customer_name": fallback_name,
            "custom_display_name": fallback_name,
            "email_id": "",
            "mobile_no": "",
            "image": None,
            "loyalty_program": None,
            "customer_price_list": None,
            "customer_group": None,
            "customer_type": None,
            "territory": None,
            "is_corporate": False,
            "is_company": False,
            "birthday": None,
            "gender": None,
            "tax_id": None,
            "posa_discount": None,
            "vehicles": [],
            "vehicle_no": "",
            "loyalty_points": 0,
            "conversion_factor": 0,
        }

    res = {"loyalty_points": 0, "conversion_factor": 0}

    # --- Standard fields ---
    res["email_id"] = getattr(customer_doc, "email_id", None)
    res["mobile_no"] = getattr(customer_doc, "mobile_no", None)
    res["image"] = getattr(customer_doc, "image", None)
    loyalty_program = auto_assign_loyalty_program(customer_doc)
    res["loyalty_program"] = loyalty_program
    res["customer_price_list"] = getattr(customer_doc, "default_price_list", None)
    res["customer_group"] = getattr(customer_doc, "customer_group", None)
    res["customer_type"] = getattr(customer_doc, "customer_type", None)
    res["territory"] = getattr(customer_doc, "territory", None)

    is_company_val = getattr(customer_doc, "is_company", 0)
    res["is_corporate"] = bool(is_company_val)
    res["is_company"] = bool(is_company_val)

    res["birthday"] = getattr(customer_doc, "posa_birthday", None)
    res["gender"] = getattr(customer_doc, "gender", None)
    res["tax_id"] = getattr(customer_doc, "tax_id", None)
    res["posa_discount"] = getattr(customer_doc, "posa_discount", None)
    res["name"] = customer_doc.name
    res["customer_name"] = customer_doc.customer_name
    res["custom_display_name"] = (
        getattr(customer_doc, "custom_display_name", None) or customer_doc.customer_name
    )

    res["customer_group_price_list"] = frappe.get_value(
        "Customer Group", customer_doc.customer_group, "default_price_list"
    )

    # --- Loyalty Points ---
    if customer_doc.loyalty_program:
        current_company = frappe.db.get_single_value("Global Defaults", "default_company") or "webtree"
        conversion_factor = frappe.db.get_value(
            "Loyalty Program", customer_doc.loyalty_program, "conversion_factor"
        )
        res["conversion_factor"] = flt(conversion_factor) or 1
        res["loyalty_points"] = get_loyalty_points(
            customer_doc.name, customer_doc.loyalty_program, current_company
        )

    # --- Address (unchanged) ---
    addresses = frappe.db.sql(
        """
        SELECT
            address.address_line1,
            address.address_line2,
            address.city,
            address.state,
            address.country
        FROM `tabAddress` address
        INNER JOIN `tabDynamic Link` link
            ON address.name = link.parent
        WHERE
            link.link_doctype = 'Customer'
            AND link.link_name = %s
            AND address.disabled = 0
            AND address.address_type = 'Shipping'
        ORDER BY address.creation DESC
        LIMIT 1
        """,
        (customer_doc.name,),
        as_dict=True,
    )

    if addresses:
        addr = addresses[0]
        res["address_line1"] = addr.address_line1 or ""
        res["address_line2"] = addr.address_line2 or ""
        res["city"] = addr.city or ""
        res["state"] = addr.state or ""
        res["country"] = addr.country or ""

    # Reuse vehicles API so make/model fallback behavior is consistent across POS screens.
    res["vehicles"] = get_vehicles_by_customer(customer_doc.name, limit=10) or []

    if res["vehicles"]:
        res["vehicle_no"] = res["vehicles"][0]["vehicle_no"]

    return res


@frappe.whitelist()
def search_customers_new(query=None, limit=20):
    """
    Search customers by partial name or mobile number and return
    the FULL detailed customer object (same shape as get_customer_info)
    for each match.

    - query: partial search string (required)
    - limit: max number of customers to return (default 20, capped at 200)
    """
    if not query:
        return {"customers": [], "count": 0}

    # sanitize and cap limit
    q = str(query).strip()
    try:
        limit = min(200, abs(int(limit)))
    except Exception:
        limit = 20

    search_term = f"%{q}%"

    try:
        has_custom_display_name = False
        try:
            has_custom_display_name = frappe.db.has_column("tabCustomer", "custom_display_name")
        except Exception:
            has_custom_display_name = False

        where_parts = [
            "LOWER(customer_name) LIKE LOWER(%s)",
            "mobile_no LIKE %s",
        ]
        values = [search_term, search_term]
        if has_custom_display_name:
            where_parts.insert(1, "LOWER(custom_display_name) LIKE LOWER(%s)")
            values.insert(1, search_term)

        rows = frappe.db.sql(
            f"""
            SELECT name
            FROM `tabCustomer`
            WHERE ({' OR '.join(where_parts)})
            ORDER BY customer_name ASC
            LIMIT %s
            """,
            tuple(values + [limit]),
            as_dict=True,
        )
    except Exception:
        frappe.log_error(frappe.get_traceback(), "search_customers - sql error")
        return {"customers": [], "count": 0}

    if not rows:
        return {"customers": [], "count": 0}

    customers = []
    for r in rows:
        cust_name = r.get("name")
        try:
            customers.append(_build_customer_info(cust_name))
        except Exception:
            # log but continue; skip problematic customers
            frappe.log_error(frappe.get_traceback(), f"search_customers - building info for {cust_name}")
            continue

    return {"customers": customers, "count": len(customers)}


def _build_customer_info(customer_name):
    """
    Helper: build the same detailed customer response you used in get_customer_info.
    """
    customer_doc = frappe.get_doc("Customer", customer_name)

    res = {"loyalty_points": 0, "conversion_factor": 0}

    # --- Standard fields ---
    res["email_id"] = customer_doc.email_id
    res["mobile_no"] = customer_doc.mobile_no
    res["loyalty_program"] = customer_doc.loyalty_program
    res["customer_type"] = customer_doc.customer_type
    res["territory"] = customer_doc.territory
    res["is_corporate"] = bool(getattr(customer_doc, "is_company", False))
    res["name"] = customer_doc.name
    res["customer_name"] = customer_doc.customer_name
    res["custom_display_name"] = (
        getattr(customer_doc, "custom_display_name", None) or customer_doc.customer_name
    )

    res["customer_group_price_list"] = frappe.get_value(
        "Customer Group", customer_doc.customer_group, "default_price_list"
    )

    # --- Loyalty Points ---
    if customer_doc.loyalty_program:
        current_company = frappe.db.get_single_value("Global Defaults", "default_company") or "webtree"
        conversion_factor = frappe.db.get_value(
            "Loyalty Program", customer_doc.loyalty_program, "conversion_factor"
        )
        res["conversion_factor"] = flt(conversion_factor) or 1
        res["loyalty_points"] = get_loyalty_points(
            customer_doc.name, customer_doc.loyalty_program, current_company
        )

    # --- Address (unchanged) ---
    addresses = frappe.db.sql(
        """
        SELECT
            address.address_line1,
            address.address_line2,
            address.city,
            address.state,
            address.country
        FROM `tabAddress` address
        INNER JOIN `tabDynamic Link` link
            ON address.name = link.parent
        WHERE
            link.link_doctype = 'Customer'
            AND link.link_name = %s
            AND address.disabled = 0
            AND address.address_type = 'Shipping'
        ORDER BY address.creation DESC
        LIMIT 1
        """,
        (customer_doc.name,),
        as_dict=True,
    )

    if addresses:
        addr = addresses[0]
        res["address_line1"] = addr.address_line1 or ""
        res["address_line2"] = addr.address_line2 or ""
        res["city"] = addr.city or ""
        res["state"] = addr.state or ""
        res["country"] = addr.country or ""

    # Keep search endpoint aligned with get_customer_info output.
    res["vehicles"] = get_vehicles_by_customer(customer_doc.name, limit=10) or []

    if res["vehicles"]:
        res["vehicle_no"] = res["vehicles"][0].get("vehicle_no")

    return res


@frappe.whitelist()
def get_customer_by_mobile(mobile_no):
    """
    Get customer details by mobile number for quick lookup in POS.
    Used when a user enters a mobile number in the Vehicle No. field.
    """
    if not mobile_no:
        return None

    # Try to find the customer where the mobile_no matches
    customer_name = frappe.db.get_value("Customer", {"mobile_no": mobile_no}, "name")

    if customer_name:
        # Fetch key details needed by the frontend
        customer_doc = frappe.get_doc("Customer", customer_name)
        return {
            "name": customer_doc.name,
            "customer_name": customer_doc.customer_name,
            "custom_display_name": getattr(customer_doc, "custom_display_name", None)
            or customer_doc.customer_name,
            "mobile_no": customer_doc.mobile_no,
            "email_id": customer_doc.email_id,
            "tax_id": customer_doc.tax_id,
            "is_corporate": bool(getattr(customer_doc, "is_company", False)),
        }

    return None


@frappe.whitelist()
def get_customer_by_vehicle(vehicle_no):
    """Return customer details for a vehicle number (exact match) with mobile info"""

    if not vehicle_no:
        frappe.throw(_("Vehicle number is required"))

    try:
        vehicle_data = frappe.get_all(
            VM_DOCTYPE,
            filters={"vehicle_no": vehicle_no},
            fields=["name", "customer", "model", "chasis_no", "vehicle_no"],
            limit_page_length=1,
        )

        if not vehicle_data:
            return {}

        vehicle = vehicle_data[0]
        cust_name = vehicle.get("customer")

        if not cust_name:
            return {"vehicle": vehicle, "customer": {}}

        # Retrieve customer details including mobile number
        try:
            cust_doc = frappe.get_doc("Customer", cust_name)
            return {
                "vehicle": {
                    "name": vehicle.get("name"),
                    "vehicle_no": vehicle.get("vehicle_no"),
                    "model": vehicle.get("model"),
                    "make": vehicle.get("make"),
                    "chasis_no": vehicle.get("chasis_no"),
                },
                "customer": {
                    "name": cust_doc.name,
                    "customer_name": cust_doc.customer_name,
                    "custom_display_name": getattr(cust_doc, "custom_display_name", None)
                    or cust_doc.customer_name,
                    "email_id": getattr(cust_doc, "email_id", ""),
                    "mobile_no": getattr(cust_doc, "mobile_no", ""),
                    "tax_id": getattr(cust_doc, "tax_id", ""),
                    "customer_group": cust_doc.customer_group,
                    "territory": cust_doc.territory,
                    "posa_discount": cust_doc.posa_discount,
                    "is_corporate": bool(getattr(cust_doc, "is_company", False)),
                },
            }
        except frappe.DoesNotExistError:
            return {"vehicle": vehicle, "customer": {}}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Vehicle Lookup Error")
        return {}


def _parse_numeric(value):
    if value is None or value == "":
        return None
    try:
        s = str(value).replace(",", "").strip()
        return Decimal(s)
    except Exception:
        try:
            return Decimal(str(float(s)))
        except Exception:
            return None


def _set_odometer_on_doc(doc, od_value):
    if od_value is None:
        return False
    set_any = False
    for fname in ("odometer", "odometer_value_last", "odometer_value", "odometer_reading"):
        if hasattr(doc, fname):
            try:
                setattr(doc, fname, od_value)
                set_any = True
            except Exception:
                pass
    if not set_any and hasattr(doc, "odometer"):
        try:
            doc.odometer = od_value
            set_any = True
        except Exception:
            pass
    return set_any


def _extract_odometer_from_payload_or_doc(vehicle_data, vehicle_doc=None):
    """
    Return a Decimal/number odometer candidate found either in vehicle_data
    (payload) or on an existing vehicle_doc. Returns None if nothing found.
    """
    candidates = ["odometer", "odometer_value_last", "odometer_value", "odometer_last", "odometer_reading"]
    for k in candidates:
        if vehicle_data and vehicle_data.get(k) not in (None, ""):
            parsed = _parse_numeric(vehicle_data.get(k))
            if parsed is not None:
                return parsed
    if vehicle_doc:
        for k in candidates:
            v = getattr(vehicle_doc, k, None)
            if v not in (None, ""):
                parsed = _parse_numeric(v)
                if parsed is not None:
                    return parsed
    return None


@frappe.whitelist()
def create_customer_with_vehicle(customer, vehicle, company=None, pos_profile_doc=None):
    """
    Create or update customer and create/update corresponding Vehicle & Vehicle Master (VM).
    Accepts JSON strings (as the frontend sends stringified JSON).
    Returns: {"customer": {...}, "vehicle": {...}} on success.
    """
    try:
        customer_data = json.loads(customer) if isinstance(customer, str) else (customer or {})
        vehicle_data = json.loads(vehicle) if isinstance(vehicle, str) else (vehicle or {})
        customer_data = customer_data or {}
        vehicle_data = vehicle_data or {}

        # Treat blank optional vehicle fields as "not provided" to avoid clearing existing values on update.
        for optional_field in ("make", "model", "mobile_no", "odometer"):
            if optional_field in vehicle_data and cstr(vehicle_data.get(optional_field)).strip() == "":
                vehicle_data[optional_field] = None

        pos_profile = {}
        try:
            pos_profile = (
                json.loads(pos_profile_doc) if isinstance(pos_profile_doc, str) else (pos_profile_doc or {})
            )
        except Exception:
            pos_profile = {}

        country_context = (
            customer_data.get("country")
            or vehicle_data.get("country")
            or pos_profile.get("posa_default_country")
            or "BH"
        )

        # Normalize mobile fields early so all downstream writes stay consistent.
        if "mobile_no" in customer_data:
            customer_data["mobile_no"] = _normalize_mobile_no(customer_data.get("mobile_no"), country_context)
        if "mobile_no" in vehicle_data:
            if vehicle_data.get("mobile_no") in (None, ""):
                vehicle_data["mobile_no"] = None
            else:
                vehicle_data["mobile_no"] = _normalize_mobile_no(
                    vehicle_data.get("mobile_no"), country_context
                )

        # ------------------ Defensive sanitization & autoname pre-check ------------------
        try:
            # ensure dicts
            customer_data = customer_data or {}
            vehicle_data = vehicle_data or {}

            # Log incoming payload for debugging (won't expose in production logs beyond configured logging)
            frappe.logger().debug(
                f"POS Awesome create_customer_with_vehicle - payload customer: {customer_data}, vehicle: {vehicle_data}"
            )

            # If frontend accidentally sends vehicle_no as the customer name/id, remove it.
            v_no = vehicle_data.get("vehicle_no")
            for suspect_key in ("name", "customer_id", "customer"):
                if suspect_key in customer_data and v_no and str(customer_data.get(suspect_key)) == str(v_no):
                    customer_data.pop(suspect_key, None)
                    frappe.logger().info(
                        f"Removed suspicious customer field '{suspect_key}' equal to vehicle_no to avoid naming collision"
                    )

            # Remove vehicle fields accidentally attached to customer payload (they shouldn't determine customer name)
            for k in ("vehicle_no", "license_plate", "plate", "plate_no"):
                if k in customer_data:
                    customer_data.pop(k, None)

            # Validate Customer.autoname if it requires a field
            try:
                meta = frappe.get_meta("Customer")
                autoname = getattr(meta, "autoname", "") or ""
                if autoname.startswith("field:"):
                    name_field = autoname.split(":", 1)[1]
                    # check payload first
                    name_value = customer_data.get(name_field) or None
                    if not name_value or str(name_value).strip() == "":
                        # fallback: try to pick a safe candidate from payload (mobile/email/vehicle)
                        candidate = (
                            customer_data.get(name_field)
                            or customer_data.get("customer_name")
                            or customer_data.get("mobile_no")
                            or customer_data.get("email_id")
                            or v_no
                        )
                        if candidate:
                            # sanitize simple dangerous chars and trim
                            safe_candidate = str(candidate).strip()[:140].replace("/", "-").replace("\\", "-")
                            customer_data[name_field] = safe_candidate
                            frappe.logger().info(
                                "Autoname required field '%s' missing — assigned fallback value '%s'"
                                % (name_field, safe_candidate)
                            )
                        else:
                            # no sensible fallback — raise clear error
                            frappe.log_error(
                                "Autoname requires field '%s' but payload is missing/empty. payload: %s"
                                % (name_field, cstr(customer_data)),
                                "POS Awesome - Customer create autoname validation",
                            )
                            frappe.throw(
                                _("Cannot create Customer: required field '{0}' is missing or empty").format(
                                    name_field
                                )
                            )
            except Exception:
                # If meta lookup fails, let Frappe attempt insert and produce its normal error
                frappe.log_error(frappe.get_traceback(), "POS Awesome - autoname pre-check error")
        except Exception:
            frappe.log_error(frappe.get_traceback(), "POS Awesome - pre-insert sanitization error")
        # -------------------------------------------------------------------------------

        method = (customer_data.get("method") or "create").lower()
        customer_id = customer_data.get("customer_id") or None
        vehicle_no_from_payload = (vehicle_data or {}).get("vehicle_no") or None

        # ---------- UPDATE OR CREATE CUSTOMER ----------
        if method == "update" and customer_id:
            cust = frappe.get_doc("Customer", customer_id)
            renamed_from = None
            previous_customer_name = cstr(getattr(cust, "customer_name", "")).strip()
            previous_display_name = cstr(getattr(cust, "custom_display_name", "")).strip()
            previous_mobile_no = cstr(getattr(cust, "mobile_no", "")).strip()
            previous_email_id = cstr(getattr(cust, "email_id", "")).strip()
            # update safe fields if provided
            for fld in [
                "customer_name",
                "custom_display_name",
                "tax_id",
                "mobile_no",
                "email_id",
                "customer_type",
                "gender",
                "referral_code",
            ]:
                if fld in customer_data and customer_data.get(fld) is not None:
                    setattr(cust, fld, customer_data.get(fld))

            incoming_customer_name = cstr(customer_data.get("customer_name") or "").strip()
            incoming_display_name = cstr(customer_data.get("custom_display_name") or "").strip()
            # Keep display name aligned with customer name by default during edits.
            if incoming_customer_name and (
                not incoming_display_name
                or incoming_display_name == previous_customer_name
                or previous_display_name == previous_customer_name
            ):
                cust.custom_display_name = incoming_customer_name
            if customer_data.get("customer_group") is not None:
                cust.customer_group = customer_data.get("customer_group")
            if customer_data.get("territory") is not None:
                cust.territory = customer_data.get("territory")
            if customer_data.get("birthday"):
                try:
                    cust.posa_birthday = customer_data.get("birthday")
                except Exception:
                    pass
            try:
                cust.save(ignore_permissions=True)
                frappe.db.commit()
            except Exception:
                frappe.log_error(frappe.get_traceback(), "Customer update save error")
            customer_doc = cust

            # Keep backend Customer ID (name) aligned with edited customer_name when changed in POS.
            # This avoids confusing cases where display name changes but ID remains old (e.g. CUST-001).
            rename_target = cstr(customer_data.get("customer_name") or "").strip()
            current_name = cstr(customer_doc.name or "").strip()
            if rename_target and current_name and rename_target != current_name:
                if frappe.db.exists("Customer", rename_target):
                    frappe.throw(
                        _("Cannot rename Customer ID to '{0}' because it already exists").format(
                            rename_target
                        )
                    )
                try:
                    model_rename_doc(
                        doctype="Customer",
                        old=current_name,
                        new=rename_target,
                        force=True,
                        ignore_permissions=True,
                        show_alert=False,
                    )
                    frappe.db.commit()
                    renamed_from = current_name
                    customer_doc = frappe.get_doc("Customer", rename_target)
                except Exception:
                    frappe.log_error(frappe.get_traceback(), "Customer ID rename error")
                    frappe.throw(
                        _("Customer was updated but failed to rename Customer ID to '{0}'").format(
                            rename_target
                        )
                    )

            # Keep Customer primary contact fields in sync (Customer form shows these).
            # Without this, mobile can update on vehicle records but remain stale on Contact.
            try:
                incoming_mobile = customer_data.get("mobile_no")
                if incoming_mobile not in (None, ""):
                    if cstr(incoming_mobile).strip() != previous_mobile_no:
                        set_customer_info(customer_doc.name, "mobile_no", incoming_mobile)

                incoming_email = customer_data.get("email_id")
                if incoming_email not in (None, ""):
                    if cstr(incoming_email).strip() != previous_email_id:
                        set_customer_info(customer_doc.name, "email_id", incoming_email)
            except Exception:
                frappe.log_error(frappe.get_traceback(), "Customer contact sync warning")
        else:
            # create
            cd = customer_data
            customer_doc = frappe.new_doc("Customer")
            customer_doc.customer_name = cd.get("customer_name")
            customer_doc.custom_display_name = cd.get("custom_display_name") or cd.get("customer_name")
            customer_doc.customer_type = cd.get("customer_type", "Individual")
            customer_doc.customer_group = cd.get("customer_group") or frappe.defaults.get_user_default(
                "Customer Group"
            )
            customer_doc.territory = cd.get("territory") or frappe.defaults.get_user_default("Territory")
            if cd.get("tax_id"):
                customer_doc.tax_id = cd.get("tax_id")
            if cd.get("mobile_no"):
                customer_doc.mobile_no = cd.get("mobile_no")
            if cd.get("email_id"):
                customer_doc.email_id = cd.get("email_id")
            if cd.get("gender"):
                customer_doc.gender = cd.get("gender")
            if cd.get("referral_code"):
                customer_doc.posa_referral_code = cd.get("referral_code")
            if cd.get("birthday"):
                try:
                    customer_doc.posa_birthday = cd.get("birthday")
                except Exception:
                    pass

            # --- Fallback ensure: if autoname requires customer_name and it's still empty, inject safe fallback ---
            try:
                if not customer_doc.customer_name or not str(customer_doc.customer_name).strip():
                    candidate = (
                        cd.get("customer_name")
                        or cd.get("mobile_no")
                        or cd.get("email_id")
                        or (vehicle_data.get("vehicle_no") if vehicle_data else None)
                    )
                    if candidate:
                        safe_candidate = str(candidate).strip()[:140].replace("/", "-").replace("\\", "-")
                        customer_doc.customer_name = safe_candidate
                        frappe.logger().info(
                            "Assigned fallback customer_name '%s' to avoid naming issues" % safe_candidate
                        )
                    else:
                        # last resort: generate a short safe id
                        customer_doc.customer_name = "POS-CUST-" + frappe.generate_hash(length=6)
                        frappe.logger().info(
                            "Assigned generated fallback customer_name for POS customer creation"
                        )
            except Exception:
                frappe.log_error(
                    frappe.get_traceback(), "POS Awesome - fallback customer_name assignment error"
                )

            try:
                # Defensive: client payloads (or internal new_doc state) sometimes carry placeholder names like
                # "New Customer 1". Frappe rejects these during insert.
                if getattr(customer_doc, "name", None) and str(customer_doc.name).startswith(
                    f"New {customer_doc.doctype}"
                ):
                    customer_doc.name = None

                customer_doc.insert(ignore_permissions=True)
                frappe.db.commit()
            except (ValidationError, LinkValidationError, DoesNotExistError, NameError):
                raise
            except Exception as e:
                frappe.log_error(frappe.get_traceback(), "POS Awesome - Customer create error")
                frappe.throw(_("Failed to create Customer: {0}").format(cstr(e)))

        # ---------- VEHICLE (existing or create) ----------
        vehicle_doc = None
        vm_doc = None

        # determine effective vehicle identifier to operate on
        effective_vehicle_no = vehicle_no_from_payload

        # Normalize early to avoid mismatches (UI/DB comparisons are case-sensitive).
        if effective_vehicle_no:
            effective_vehicle_no = str(effective_vehicle_no).strip().upper()

        def _candidate_vehicle_id_from_customer(doc):
            """Return a candidate vehicle identifier stored on the customer (if any)."""
            try:
                if hasattr(doc, "custom_vehicle_no") and getattr(doc, "custom_vehicle_no"):
                    return getattr(doc, "custom_vehicle_no")
            except Exception:
                pass
            try:
                if hasattr(doc, "vehicle_no") and getattr(doc, "vehicle_no"):
                    return getattr(doc, "vehicle_no")
            except Exception:
                pass
            return None

        def _vehicle_exists_anywhere(candidate):
            """Only accept a candidate if it already exists as Vehicle/Vehicle Master id or vehicle_no."""
            if not candidate:
                return False
            candidate = str(candidate).strip().upper()
            try:
                if frappe.db.exists(VM_DOCTYPE, candidate):
                    return True
            except Exception:
                pass
            try:
                if frappe.db.exists(VM_DOCTYPE, {"vehicle_no": candidate}):
                    return True
            except Exception:
                pass
            try:
                if frappe.db.exists(VEHICLE_DOCTYPE, candidate):
                    return True
            except Exception:
                pass
            try:
                if frappe.db.exists(VEHICLE_DOCTYPE, {"vehicle_no": candidate}):
                    return True
            except Exception:
                pass
            try:
                if frappe.db.exists(VEHICLE_DOCTYPE, {"license_plate": candidate}):
                    return True
            except Exception:
                pass
            return False

        # If frontend didn’t send vehicle_no, only use a customer-stored value when it points to an existing vehicle.
        # This prevents accidental creation of bogus "vehicles" whose id equals the customer id (e.g. "CUST-001").
        if not effective_vehicle_no:
            candidate = _candidate_vehicle_id_from_customer(customer_doc)
            if candidate and _vehicle_exists_anywhere(candidate):
                effective_vehicle_no = str(candidate).strip().upper()

        # only act on vehicles if we have an identifier
        if effective_vehicle_no:
            try:

                def _get_existing_vehicle_doc_by_number(vehicle_no: str):
                    """Return existing Vehicle doc (ERPNext) by vehicle_no/license_plate/name."""
                    if not vehicle_no:
                        return None
                    vno = str(vehicle_no).strip().upper()
                    try:
                        if frappe.db.exists(VEHICLE_DOCTYPE, vno):
                            return frappe.get_doc(VEHICLE_DOCTYPE, vno)
                    except Exception:
                        pass
                    try:
                        existing_name = frappe.db.get_value(VEHICLE_DOCTYPE, {"vehicle_no": vno}, "name")
                        if existing_name:
                            return frappe.get_doc(VEHICLE_DOCTYPE, existing_name)
                    except Exception:
                        pass
                    try:
                        existing_name = frappe.db.get_value(VEHICLE_DOCTYPE, {"license_plate": vno}, "name")
                        if existing_name:
                            return frappe.get_doc(VEHICLE_DOCTYPE, existing_name)
                    except Exception:
                        pass
                    return None

                def _get_existing_vm_doc_by_number(vehicle_no: str):
                    """Return existing Vehicle Master doc by name/vehicle_no."""
                    if not vehicle_no:
                        return None
                    vno = str(vehicle_no).strip().upper()
                    try:
                        if frappe.db.exists(VM_DOCTYPE, vno):
                            return frappe.get_doc(VM_DOCTYPE, vno)
                    except Exception:
                        pass
                    try:
                        existing_name = frappe.db.get_value(VM_DOCTYPE, {"vehicle_no": vno}, "name")
                        if existing_name:
                            return frappe.get_doc(VM_DOCTYPE, existing_name)
                    except Exception:
                        pass
                    return None

                # If a vehicle already exists with this number, reuse it (but do not silently reassign owners).
                existing_vehicle = _get_existing_vehicle_doc_by_number(effective_vehicle_no)
                if existing_vehicle:
                    existing_owner = getattr(existing_vehicle, "customer", None) or None
                    if existing_owner and existing_owner != customer_doc.name:
                        frappe.throw(
                            _("Vehicle {0} is already linked to another customer ({1}).").format(
                                effective_vehicle_no, existing_owner
                            ),
                            ValidationError,
                        )
                    vehicle_doc = existing_vehicle

                existing_vm = _get_existing_vm_doc_by_number(effective_vehicle_no)
                if existing_vm:
                    existing_owner = getattr(existing_vm, "customer", None) or None
                    if existing_owner and existing_owner != customer_doc.name:
                        frappe.throw(
                            _("Vehicle {0} is already linked to another customer ({1}).").format(
                                effective_vehicle_no, existing_owner
                            ),
                            ValidationError,
                        )
                    vm_doc = existing_vm

                # --- VEHICLE MASTER (VM) is the source of truth for POS ---
                try:
                    if vm_doc:
                        # ensure customer link is correct
                        try:
                            if hasattr(vm_doc, "customer"):
                                vm_doc.customer = customer_doc.name
                            if hasattr(vm_doc, "vehicle_no") and effective_vehicle_no:
                                vm_doc.vehicle_no = effective_vehicle_no
                            if vehicle_data.get("model") is not None:
                                for f in ("model", "vehicle_model", "model_no"):
                                    if hasattr(vm_doc, f):
                                        setattr(vm_doc, f, vehicle_data.get("model"))
                            if vehicle_data.get("make") is not None:
                                for f in ("make", "vehicle_make", "brand", "manufacturer"):
                                    if hasattr(vm_doc, f):
                                        setattr(vm_doc, f, vehicle_data.get("make"))
                            if vehicle_data.get("mobile_no") is not None:
                                if hasattr(vm_doc, "tel_mobile"):
                                    vm_doc.tel_mobile = vehicle_data.get("mobile_no")
                                elif hasattr(vm_doc, "mobile_no"):
                                    vm_doc.mobile_no = vehicle_data.get("mobile_no")
                            vm_doc.save(ignore_permissions=True)
                            frappe.db.commit()
                        except Exception:
                            frappe.log_error(frappe.get_traceback(), "VM existing save error")
                    elif vehicle_doc and frappe.db.exists(VM_DOCTYPE, vehicle_doc.name):
                        vm_doc = frappe.get_doc(VM_DOCTYPE, vehicle_doc.name)
                        try:
                            if vehicle_data.get("model") is not None and hasattr(vm_doc, "model"):
                                try:
                                    if frappe.db.exists("Vehicle Model", vehicle_data.get("model")):
                                        vm_doc.model = vehicle_data.get("model")
                                    else:
                                        vm_doc.model = vehicle_data.get("model")
                                except Exception:
                                    vm_doc.model = vehicle_data.get("model")
                            if vehicle_data.get("make") is not None:
                                for f in ("make", "vehicle_make", "brand", "manufacturer"):
                                    if hasattr(vm_doc, f):
                                        setattr(vm_doc, f, vehicle_data.get("make"))
                            if vehicle_data.get("mobile_no") is not None:
                                if hasattr(vm_doc, "tel_mobile"):
                                    vm_doc.tel_mobile = vehicle_data.get("mobile_no")
                                elif hasattr(vm_doc, "mobile_no"):
                                    vm_doc.mobile_no = vehicle_data.get("mobile_no")
                            od_val = _extract_odometer_from_payload_or_doc(vehicle_data, vehicle_doc)
                            if od_val is not None:
                                _set_odometer_on_doc(vm_doc, od_val)

                            # ensure vm has vehicle identifier and customer link
                            if hasattr(vm_doc, "vehicle_no"):
                                vm_doc.vehicle_no = effective_vehicle_no or getattr(
                                    vehicle_doc, "vehicle_no", getattr(vehicle_doc, "name", None)
                                )
                            if hasattr(vm_doc, "customer"):
                                vm_doc.customer = customer_doc.name

                            vm_doc.save(ignore_permissions=True)
                            frappe.db.commit()
                        except Exception:
                            frappe.log_error(frappe.get_traceback(), "VM update error")
                    else:
                        # create/update VM directly keyed by vehicle number (works even if ERPNext Vehicle fails)
                        vm = frappe.new_doc(VM_DOCTYPE)
                        try:
                            vm_meta = frappe.get_meta(VM_DOCTYPE)

                            # Ensure stable id: most sites use name == vehicle number for Vehicle Master.
                            vm.name = effective_vehicle_no
                            if vm_meta.has_field("vehicle_no"):
                                vm.vehicle_no = effective_vehicle_no
                            if vm_meta.has_field("customer"):
                                vm.customer = customer_doc.name
                            if vehicle_data.get("model") is not None and vm_meta.has_field("model"):
                                vm.model = vehicle_data.get("model")
                            if vehicle_data.get("make") is not None:
                                for f in ("make", "vehicle_make", "brand", "manufacturer"):
                                    if vm_meta.has_field(f):
                                        setattr(vm, f, vehicle_data.get("make"))
                            if vehicle_data.get("mobile_no") is not None:
                                if vm_meta.has_field("tel_mobile"):
                                    vm.tel_mobile = vehicle_data.get("mobile_no")
                                elif vm_meta.has_field("mobile_no"):
                                    vm.mobile_no = vehicle_data.get("mobile_no")

                            if hasattr(vm, "customer"):
                                vm.customer = customer_doc.name
                            od_val = _extract_odometer_from_payload_or_doc(vehicle_data, vehicle_doc)
                            if od_val is not None:
                                _set_odometer_on_doc(vm, od_val)
                            # Insert or update if already exists by name
                            if frappe.db.exists(VM_DOCTYPE, vm.name):
                                existing = frappe.get_doc(VM_DOCTYPE, vm.name)
                                existing_meta = frappe.get_meta(VM_DOCTYPE)
                                for fieldname in ("vehicle_no", "customer", "model"):
                                    if (
                                        existing_meta.has_field(fieldname)
                                        and getattr(vm, fieldname, None) is not None
                                    ):
                                        setattr(existing, fieldname, getattr(vm, fieldname))
                                for fieldname in ("make", "vehicle_make", "brand", "manufacturer"):
                                    if (
                                        existing_meta.has_field(fieldname)
                                        and getattr(vm, fieldname, None) is not None
                                    ):
                                        setattr(existing, fieldname, getattr(vm, fieldname))
                                for fieldname in ("tel_mobile", "mobile_no"):
                                    if (
                                        existing_meta.has_field(fieldname)
                                        and getattr(vm, fieldname, None) is not None
                                    ):
                                        setattr(existing, fieldname, getattr(vm, fieldname))
                                existing.save(ignore_permissions=True)
                                vm_doc = existing
                            else:
                                vm.insert(ignore_permissions=True)
                                vm_doc = vm
                            frappe.db.commit()
                        except Exception:
                            frappe.log_error(frappe.get_traceback(), "VM create error")
                            frappe.throw(
                                _("Failed to create Vehicle Master for {0}.").format(effective_vehicle_no)
                            )
                except Exception:
                    frappe.log_error(frappe.get_traceback(), "Vehicle Master logic error")

                # --- Best-effort sync ERPNext Vehicle (non-fatal) ---
                try:
                    if not vehicle_doc:
                        vehicle_doc = _get_existing_vehicle_doc_by_number(effective_vehicle_no)
                    if not vehicle_doc:
                        v = frappe.new_doc(VEHICLE_DOCTYPE)
                        v_meta = frappe.get_meta(VEHICLE_DOCTYPE)
                        if v_meta.has_field("vehicle_no"):
                            v.vehicle_no = effective_vehicle_no
                        if v_meta.has_field("license_plate"):
                            v.license_plate = effective_vehicle_no
                        if v_meta.has_field("customer"):
                            v.customer = customer_doc.name
                        if vehicle_data.get("model") is not None and v_meta.has_field("model"):
                            v.model = vehicle_data.get("model")
                        if vehicle_data.get("make") is not None:
                            for f in ("make", "vehicle_make", "brand", "manufacturer"):
                                if v_meta.has_field(f):
                                    setattr(v, f, vehicle_data.get("make"))
                        if vehicle_data.get("mobile_no") is not None:
                            if v_meta.has_field("tel_mobile"):
                                v.tel_mobile = vehicle_data.get("mobile_no")
                            elif v_meta.has_field("mobile_no"):
                                v.mobile_no = vehicle_data.get("mobile_no")
                        v.insert(ignore_permissions=True)
                        frappe.db.commit()
                        vehicle_doc = v
                    else:
                        # update link when safe
                        v_meta = frappe.get_meta(VEHICLE_DOCTYPE)
                        if v_meta.has_field("customer"):
                            vehicle_doc.customer = customer_doc.name
                        if vehicle_data.get("model") is not None and v_meta.has_field("model"):
                            vehicle_doc.model = vehicle_data.get("model")
                        if vehicle_data.get("make") is not None:
                            for f in ("make", "vehicle_make", "brand", "manufacturer"):
                                if v_meta.has_field(f):
                                    setattr(vehicle_doc, f, vehicle_data.get("make"))
                        if vehicle_data.get("mobile_no") is not None:
                            if v_meta.has_field("tel_mobile"):
                                vehicle_doc.tel_mobile = vehicle_data.get("mobile_no")
                            elif v_meta.has_field("mobile_no"):
                                vehicle_doc.mobile_no = vehicle_data.get("mobile_no")
                        vehicle_doc.save(ignore_permissions=True)
                        frappe.db.commit()
                except Exception:
                    frappe.log_error(frappe.get_traceback(), "Vehicle sync warning (non-fatal)")

            except Exception:
                frappe.log_error(frappe.get_traceback(), "vehicle block error")

        # Link VM back to customer in customer_doc fields (defensive)
        try:
            if vm_doc:
                if hasattr(customer_doc, "custom_vehicle_no"):
                    customer_doc.custom_vehicle_no = vm_doc.name
                elif hasattr(customer_doc, "vehicle_no"):
                    customer_doc.vehicle_no = vm_doc.name
                customer_doc.save(ignore_permissions=True)
                frappe.db.commit()
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Failed to link VM to Customer")

        # Force-sync linked vehicle data so Customer and Vehicle dialogs reflect each other immediately.
        try:
            if effective_vehicle_no:
                _sync_vehicle_doctype(
                    vehicle_name=(getattr(vehicle_doc, "name", None) if vehicle_doc else None),
                    vehicle_no=effective_vehicle_no,
                    customer=customer_doc.name,
                    model=vehicle_data.get("model"),
                    make=vehicle_data.get("make"),
                    chasis_no=vehicle_data.get("chasis_no"),
                    color=vehicle_data.get("color"),
                    registration_number=vehicle_data.get("registration_number"),
                    mobile_no=(
                        vehicle_data.get("mobile_no")
                        if vehicle_data.get("mobile_no") not in (None, "")
                        else getattr(customer_doc, "mobile_no", None)
                    ),
                )

            def _has_col(dt, fieldname):
                try:
                    return frappe.db.has_column(dt, fieldname)
                except Exception:
                    return False

            if effective_vehicle_no:
                sync_mobile = (
                    vehicle_data.get("mobile_no")
                    if vehicle_data.get("mobile_no") not in (None, "")
                    else getattr(customer_doc, "mobile_no", None)
                )
                sync_model = vehicle_data.get("model")
                sync_make = vehicle_data.get("make")

                # Sync Vehicle Master by both key patterns used across sites.
                vm_updates = {}
                if sync_model not in (None, "") and _has_col(VM_DOCTYPE, "model"):
                    vm_updates["model"] = sync_model
                if sync_make not in (None, ""):
                    if _has_col(VM_DOCTYPE, "make"):
                        vm_updates["make"] = sync_make
                    if _has_col(VM_DOCTYPE, "vehicle_make"):
                        vm_updates["vehicle_make"] = sync_make
                    if _has_col(VM_DOCTYPE, "brand"):
                        vm_updates["brand"] = sync_make
                    if _has_col(VM_DOCTYPE, "manufacturer"):
                        vm_updates["manufacturer"] = sync_make
                if sync_mobile not in (None, ""):
                    if _has_col(VM_DOCTYPE, "tel_mobile"):
                        vm_updates["tel_mobile"] = sync_mobile
                    elif _has_col(VM_DOCTYPE, "mobile_no"):
                        vm_updates["mobile_no"] = sync_mobile
                if vm_updates:
                    try:
                        frappe.db.set_value(
                            VM_DOCTYPE, {"name": effective_vehicle_no}, vm_updates, update_modified=False
                        )
                    except Exception:
                        pass
                    try:
                        if _has_col(VM_DOCTYPE, "vehicle_no"):
                            frappe.db.set_value(
                                VM_DOCTYPE,
                                {"vehicle_no": effective_vehicle_no},
                                vm_updates,
                                update_modified=False,
                            )
                    except Exception:
                        pass

                # Sync ERPNext Vehicle doctype as well.
                veh_updates = {}
                if sync_model not in (None, ""):
                    if _has_col("Vehicle", "model"):
                        veh_updates["model"] = sync_model
                    if _has_col("Vehicle", "vehicle_model"):
                        veh_updates["vehicle_model"] = sync_model
                if sync_make not in (None, ""):
                    if _has_col("Vehicle", "make"):
                        veh_updates["make"] = sync_make
                    if _has_col("Vehicle", "vehicle_make"):
                        veh_updates["vehicle_make"] = sync_make
                    if _has_col("Vehicle", "brand"):
                        veh_updates["brand"] = sync_make
                    if _has_col("Vehicle", "manufacturer"):
                        veh_updates["manufacturer"] = sync_make
                if sync_mobile not in (None, ""):
                    if _has_col("Vehicle", "mobile_no"):
                        veh_updates["mobile_no"] = sync_mobile
                    if _has_col("Vehicle", "tel_mobile"):
                        veh_updates["tel_mobile"] = sync_mobile
                if veh_updates:
                    try:
                        frappe.db.set_value(
                            "Vehicle", {"name": effective_vehicle_no}, veh_updates, update_modified=False
                        )
                    except Exception:
                        pass
                    try:
                        if _has_col("Vehicle", "vehicle_no"):
                            frappe.db.set_value(
                                "Vehicle",
                                {"vehicle_no": effective_vehicle_no},
                                veh_updates,
                                update_modified=False,
                            )
                    except Exception:
                        pass
                    try:
                        if _has_col("Vehicle", "license_plate"):
                            frappe.db.set_value(
                                "Vehicle",
                                {"license_plate": effective_vehicle_no},
                                veh_updates,
                                update_modified=False,
                            )
                    except Exception:
                        pass

                frappe.db.commit()
        except Exception:
            frappe.log_error(frappe.get_traceback(), "create_customer_with_vehicle sync warning")

        # Build response
        customer_response = {
            "name": customer_doc.name,
            "customer_name": customer_doc.customer_name,
            "custom_display_name": getattr(customer_doc, "custom_display_name", None)
            or customer_doc.customer_name,
            "renamed_from": renamed_from if method == "update" else None,
            "mobile_no": customer_doc.mobile_no,
            "email_id": customer_doc.email_id,
            "tax_id": customer_doc.tax_id,
            "customer_group": getattr(customer_doc, "customer_group", None),
            "territory": getattr(customer_doc, "territory", None),
        }

        vehicle_response = None
        # Prefer Vehicle Master in responses because POS dropdowns use Vehicle Master rows.
        if vm_doc:
            vehicle_response = {
                "name": getattr(vm_doc, "name", None),
                "vehicle_no": getattr(vm_doc, "vehicle_no", None)
                or effective_vehicle_no
                or getattr(vm_doc, "name", None),
                "make": (
                    getattr(vm_doc, "make", None)
                    or getattr(vm_doc, "vehicle_make", None)
                    or getattr(vm_doc, "brand", None)
                    or getattr(vm_doc, "manufacturer", None)
                    or vehicle_data.get("make")
                ),
                "model": (
                    getattr(vm_doc, "model", None)
                    or getattr(vm_doc, "vehicle_model", None)
                    or getattr(vm_doc, "model_no", None)
                    or vehicle_data.get("model")
                ),
                "mobile_no": getattr(vm_doc, "tel_mobile", None)
                or getattr(vm_doc, "mobile_no", None)
                or vehicle_data.get("mobile_no"),
                "customer": getattr(vm_doc, "customer", None) or customer_doc.name,
                "odometer": (
                    getattr(vm_doc, "odometer", None)
                    if hasattr(vm_doc, "odometer")
                    else vehicle_data.get("odometer")
                ),
            }
        elif vehicle_doc:
            vehicle_response = {
                "name": getattr(vehicle_doc, "name", None),
                "vehicle_no": effective_vehicle_no
                or getattr(vehicle_doc, "vehicle_no", None)
                or getattr(vehicle_doc, "license_plate", None)
                or getattr(vehicle_doc, "name", None),
                "make": getattr(vehicle_doc, "make", None)
                or getattr(vehicle_doc, "vehicle_make", None)
                or getattr(vehicle_doc, "brand", None)
                or getattr(vehicle_doc, "manufacturer", None),
                "model": getattr(vehicle_doc, "model", None)
                or getattr(vehicle_doc, "vehicle_model", None)
                or getattr(vehicle_doc, "model_no", None),
                "mobile_no": getattr(vehicle_doc, "tel_mobile", None)
                or getattr(vehicle_doc, "mobile_no", None),
                "customer": getattr(vehicle_doc, "customer", None),
                "odometer": getattr(vehicle_doc, "odometer", None),
            }

        return {"customer": customer_response, "vehicle": vehicle_response}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "create_customer_with_vehicle - Unexpected")
        frappe.throw(_("Failed to create/update customer: {0}").format(cstr(e)))


@frappe.whitelist()
def update_customer_api(customer, vehicle=None, pos_profile_doc=None):
    """
    Simple wrapper to call create_customer_with_vehicle with method=update.
    """
    try:
        c = json.loads(customer) if isinstance(customer, str) else (customer or {})
        c["method"] = "update"
        # ensure there is an identifier: accept customer_id or name
        if not (c.get("customer_id") or c.get("name") or c.get("customer")):
            frappe.throw(_("customer_id (existing Customer.name) is required for update"))
        return create_customer_with_vehicle(
            json.dumps(c), json.dumps(vehicle or {}), "", pos_profile_doc or "{}"
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "update_customer_api error")
        return {"error": True, "message": str(e)}


def create_customer_address(customer, address_line1, city, country):
    """Create a primary address for the customer."""
    try:
        address = frappe.new_doc("Address")
        address.address_line1 = address_line1
        address.city = city
        address.country = country
        address.append("links", {"link_doctype": "Customer", "link_name": customer})
        address.insert(ignore_permissions=True)
        frappe.db.commit()

        frappe.db.set_value("Customer", customer, "customer_primary_address", address.name)
        frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"Address creation failed: {str(e)}", "Address Creation Error")


@frappe.whitelist()
def create_customer(
    customer_name,
    company,
    pos_profile_doc,
    customer_id=None,
    tax_id=None,
    mobile_no=None,
    email_id=None,
    referral_code=None,
    birthday=None,
    customer_group=None,
    territory=None,
    customer_type=None,
    gender=None,
    custom_display_name=None,
    method="create",
    address_line1=None,
    city=None,
    country=None,
):
    """Create or update customer with address"""
    pos_profile = json.loads(pos_profile_doc)

    formatted_birthday = None
    if birthday:
        try:
            if "-" in birthday:
                day, month, year = birthday.split("-")
                formatted_birthday = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            elif len(birthday) == 10 and birthday[4] == "-" and birthday[7] == "-":
                formatted_birthday = birthday
        except Exception:
            frappe.log_error(f"Error formatting birthday: {birthday}", "POS Awesome")

    if method == "create":
        is_exist = frappe.db.exists("Customer", {"customer_name": customer_name})
        if pos_profile.get("posa_allow_duplicate_customer_names") or not is_exist:
            customer = frappe.get_doc(
                {
                    "doctype": "Customer",
                    "customer_name": customer_name,
                    "custom_display_name": custom_display_name or customer_name,
                    "posa_referral_company": company,
                    "tax_id": tax_id,
                    "mobile_no": mobile_no,
                    "email_id": email_id,
                    "posa_referral_code": referral_code,
                    "posa_birthday": formatted_birthday,
                    "customer_type": customer_type,
                    "gender": gender,
                }
            )
            if customer_group:
                customer.customer_group = customer_group
            else:
                customer.customer_group = "All Customer Groups"
            if territory:
                customer.territory = territory
            else:
                customer.territory = "All Territories"

            customer.insert()

            # Only create address if address_line1 has a value
            if address_line1 and address_line1.strip():
                try:
                    args = {
                        "name": f"{customer.customer_name} - Shipping",
                        "doctype": "Customer",
                        "customer": customer.name,
                        "address_line1": address_line1.strip(),
                        "address_line2": "",
                        "city": city or "",
                        "state": "",
                        "pincode": "",
                        "country": country or "",
                    }
                    make_address(json.dumps(args))
                except Exception as e:
                    frappe.log_error(
                        f"Failed to create address for customer {customer.name}: {str(e)}",
                        "Address Creation Error",
                    )

            return customer
        else:
            frappe.throw(_("Customer already exists"))

    elif method == "update":
        customer_doc = frappe.get_doc("Customer", customer_id)
        customer_doc.customer_name = customer_name
        customer_doc.custom_display_name = custom_display_name or customer_name
        customer_doc.tax_id = tax_id
        customer_doc.mobile_no = mobile_no
        customer_doc.email_id = email_id
        customer_doc.posa_referral_code = referral_code
        customer_doc.posa_birthday = formatted_birthday
        customer_doc.customer_type = customer_type
        customer_doc.gender = gender
        customer_doc.save()

        if mobile_no:
            set_customer_info(customer_doc.name, "mobile_no", mobile_no)
        if email_id:
            set_customer_info(customer_doc.name, "email_id", email_id)

        existing_address_name = frappe.db.get_value(
            "Dynamic Link",
            {
                "link_doctype": "Customer",
                "link_name": customer_id,
                "parenttype": "Address",
            },
            "parent",
        )

        if existing_address_name:
            if address_line1 and address_line1.strip():
                try:
                    address_doc = frappe.get_doc("Address", existing_address_name)
                    address_doc.address_line1 = address_line1.strip()
                    address_doc.city = city or ""
                    address_doc.country = country or ""
                    address_doc.save()
                except Exception as e:
                    frappe.log_error(
                        f"Failed to update address for customer {customer_id}: {str(e)}",
                        "Address Update Error",
                    )
        else:
            if address_line1 and address_line1.strip():
                try:
                    args = {
                        "name": f"{customer_doc.customer_name} - Shipping",
                        "doctype": "Customer",
                        "customer": customer_doc.name,
                        "address_line1": address_line1.strip(),
                        "address_line2": "",
                        "city": city or "",
                        "state": "",
                        "pincode": "",
                        "country": country or "",
                    }
                    make_address(json.dumps(args))
                except Exception as e:
                    frappe.log_error(
                        f"Failed to create address for customer {customer_doc.name}: {str(e)}",
                        "Address Creation Error",
                    )

        return customer_doc


@frappe.whitelist()
def search_customers(search_term="", pos_profile=None, limit=20):
    """
    Server-side fallback for substring search used by the POS frontend.
    Returns list of dict: {name, customer_name, custom_display_name, mobile_no, email_id, tax_id, vehicle_no}
    """
    search_term = (search_term or "").strip()
    limit = int(limit or 20)
    if not search_term:
        # if no search term, return limited recent active customers
        has_custom_display_name = False
        try:
            has_custom_display_name = bool(
                frappe.db.has_column("tabCustomer", "custom_display_name")
                and frappe.get_meta("Customer").get_field("custom_display_name")
            )
        except Exception:
            has_custom_display_name = False

        fields = ["name", "customer_name", "mobile_no", "email_id", "tax_id", "vehicle_no"]
        if has_custom_display_name:
            fields.insert(2, "custom_display_name")

        rows = frappe.get_all(
            "Customer",
            filters=[["disabled", "=", 0]],
            fields=fields,
            limit_page_length=limit,
            order_by="modified desc",
        )

        if not has_custom_display_name:
            for row in rows:
                row["custom_display_name"] = row.get("customer_name") or row.get("name") or ""

        return rows

    has_custom_display_name = False
    try:
        has_custom_display_name = bool(
            frappe.db.has_column("tabCustomer", "custom_display_name")
            and frappe.get_meta("Customer").get_field("custom_display_name")
        )
    except Exception:
        has_custom_display_name = False

    custom_display_select = (
        "COALESCE(custom_display_name, customer_name) AS custom_display_name"
        if has_custom_display_name
        else "customer_name AS custom_display_name"
    )

    # Build SQL-style like pattern safely
    like = "%%%s%%" % frappe.db.escape(search_term).replace("%", "").replace("'", "")

    # Use SQL for OR across many fields (more reliable & fast)
    rows = frappe.db.sql(
        f"""
        SELECT name, customer_name, {custom_display_select}, mobile_no, email_id, COALESCE(tax_id, '') AS tax_id, COALESCE(vehicle_no, '') AS vehicle_no
        FROM `tabCustomer`
        WHERE disabled = 0
        AND (
            name LIKE %(like)s
            OR customer_name LIKE %(like)s
            {"OR custom_display_name LIKE %(like)s" if has_custom_display_name else ""}
            OR mobile_no LIKE %(like)s
            OR email_id LIKE %(like)s
            OR tax_id LIKE %(like)s
            OR vehicle_no LIKE %(like)s
        )
        LIMIT %(limit)s
        """,
        {"like": like, "limit": limit},
        as_dict=1,
    )

    return rows


@frappe.whitelist()
def set_customer_info(customer, fieldname, value=""):
    """Update customer information and linked contacts"""
    if fieldname == "loyalty_program":
        frappe.db.set_value("Customer", customer, "loyalty_program", value)

    contact = frappe.get_cached_value("Customer", customer, "customer_primary_contact") or ""

    if contact:
        contact_doc = frappe.get_doc("Contact", contact)
        if fieldname == "email_id":
            contact_doc.set("email_ids", [{"email_id": value, "is_primary": 1}])
            frappe.db.set_value("Customer", customer, "email_id", value)
        elif fieldname == "mobile_no":
            contact_doc.set("phone_nos", [{"phone": value, "is_primary_mobile_no": 1}])
            frappe.db.set_value("Customer", customer, "mobile_no", value)
        contact_doc.save()
    else:
        contact_doc = frappe.new_doc("Contact")
        contact_doc.first_name = customer
        contact_doc.is_primary_contact = 1
        contact_doc.is_billing_contact = 1
        if fieldname == "mobile_no":
            contact_doc.add_phone(value, is_primary_mobile_no=1, is_primary_phone=1)
        if fieldname == "email_id":
            contact_doc.add_email(value, is_primary=1)
        contact_doc.append("links", {"link_doctype": "Customer", "link_name": customer})
        contact_doc.flags.ignore_mandatory = True
        contact_doc.insert()
        frappe.set_value("Customer", customer, "customer_primary_contact", contact_doc.name)


@frappe.whitelist()
def get_customer_addresses(customer):
    """Get all addresses for a customer"""
    return frappe.db.sql(
        """
        SELECT
            address.name,
            address.address_line1,
            address.address_line2,
            address.address_title,
            address.city,
            address.state,
            address.country,
            address.address_type
        FROM `tabAddress` as address
        INNER JOIN `tabDynamic Link` AS link
            ON address.name = link.parent
        WHERE link.link_doctype = 'Customer'
            AND link.link_name = '{0}'
            AND address.disabled = 0
        ORDER BY address.name
        """.format(
            customer
        ),
        as_dict=1,
    )


@frappe.whitelist()
def make_address(args):
    """Create a new address"""
    args = json.loads(args)

    # Validate that address_line1 is provided
    address_line1 = args.get("address_line1", "").strip()
    if not address_line1:
        frappe.throw(_("Address Line 1 is mandatory to create an address"))

    address = frappe.get_doc(
        {
            "doctype": "Address",
            "address_title": args.get("name"),
            "address_line1": address_line1,
            "address_line2": args.get("address_line2", ""),
            "city": args.get("city", ""),
            "state": args.get("state", ""),
            "pincode": args.get("pincode", ""),
            "country": args.get("country", ""),
            "address_type": "Shipping",
            "links": [{"link_doctype": args.get("doctype"), "link_name": args.get("customer")}],
        }
    ).insert()
    return address


@frappe.whitelist()
def get_sales_person_names():
    """Get list of sales persons for POS"""
    try:
        profile = get_active_pos_profile()
        allowed = []
        if profile:
            allowed = [
                d.get("sales_person") for d in profile.get("posa_sales_persons", []) if d.get("sales_person")
            ]
        filters = {"enabled": 1}
        if allowed:
            filters["name"] = ["in", allowed]
        sales_persons = frappe.get_list(
            "Sales Person",
            filters=filters,
            fields=["name", "sales_person_name"],
            limit_page_length=100000,
        )
        return sales_persons
    except Exception as e:
        frappe.log_error(f"Error fetching sales persons: {str(e)}", "POS Sales Person Error")
        return []


@frappe.whitelist()
def search_customers_with_vehicles(search_term="", pos_profile=None, limit=20):
    """
    Enhanced search that searches BOTH customers AND vehicles.
    When vehicle number matches, returns the customer who owns that vehicle.

    Args:
        search_term: Search string (can be customer name, mobile, vehicle number, etc.)
        pos_profile: POS Profile for filtering
        limit: Maximum results to return

    Returns:
        List of customers with vehicle information if matched via vehicle
    """
    search_term = (search_term or "").strip()
    limit = min(max(int(limit or 20), 1), 20)
    has_custom_display_name = False
    try:
        has_custom_display_name = frappe.db.has_column("tabCustomer", "custom_display_name")
    except Exception:
        has_custom_display_name = False

    if not search_term:
        # Return recent customers
        fields = ["name", "customer_name", "mobile_no"]
        if has_custom_display_name:
            fields.insert(2, "custom_display_name")
        return frappe.get_all(
            "Customer",
            filters=[["disabled", "=", 0]],
            fields=fields,
            limit_page_length=limit,
            order_by="modified desc",
        )
    if len(search_term) < 2:
        return []

    # Build safe LIKE pattern
    like_pattern = "%%%s%%" % frappe.db.escape(search_term).replace("%", "").replace("'", "")

    # STEP 1: Search Customers Directly
    custom_display_select = (
        "c.custom_display_name" if has_custom_display_name else "c.customer_name AS custom_display_name"
    )
    custom_display_where = "OR c.custom_display_name LIKE %(like)s" if has_custom_display_name else ""

    customer_results = frappe.db.sql(
        f"""
    SELECT 
        c.name,
        c.customer_name,
        {custom_display_select},
        c.mobile_no,
        '' AS email_id,
        '' AS tax_id,
        CASE 
            WHEN c.customer_type = 'Company' THEN 1 
            ELSE 0 
        END AS is_corporate,
        NULL as vehicle_no,
        NULL as vehicle_model,
        NULL as vehicle_make,
        'customer' as match_source
    FROM `tabCustomer` c
    WHERE c.disabled = 0
    AND (
        c.name LIKE %(like)s
        OR c.customer_name LIKE %(like)s
        {custom_display_where}
        OR c.mobile_no LIKE %(like)s
    )
    LIMIT %(limit)s
    """,
        {"like": like_pattern, "limit": limit},
        as_dict=1,
    )

    vehicle_results = []
    try:
        vehicle_matches = frappe.db.sql(
            """
            SELECT
                vm.name as vehicle_id,
                vm.vehicle_no,
                vm.registration_number,
                vm.plate_no,
                vm.customer,
                vm.model,
                v.make
            FROM `tabVehicle Master` vm
            LEFT JOIN `tabCustomer` c ON c.name = vm.customer
            WHERE (
                vm.vehicle_no LIKE %(like)s
                OR vm.registration_number LIKE %(like)s
                OR vm.plate_no LIKE %(like)s
                OR c.mobile_no LIKE %(like)s
            )
            AND vm.customer IS NOT NULL
            AND vm.customer != ''
            LIMIT %(limit)s
            """,
            {"like": like_pattern, "limit": limit},
            as_dict=1,
        )

        for vehicle in vehicle_matches:
            if not vehicle.get("customer"):
                continue

            try:
                customer_data = frappe.db.get_value(
                    "Customer",
                    vehicle.customer,
                    (
                        [
                            "name",
                            "customer_name",
                            "custom_display_name",
                            "mobile_no",
                            "email_id",
                            "tax_id",
                            "customer_type",
                        ]
                        if has_custom_display_name
                        else ["name", "customer_name", "mobile_no", "email_id", "tax_id", "customer_type"]
                    ),
                    as_dict=1,
                )

                if customer_data:
                    vehicle_results.append(
                        {
                            "name": customer_data.name,
                            "customer_name": customer_data.customer_name,
                            "custom_display_name": (
                                customer_data.get("custom_display_name") or customer_data.customer_name
                            ),
                            "mobile_no": customer_data.mobile_no or "",
                            "email_id": customer_data.email_id or "",
                            "tax_id": customer_data.tax_id or "",
                            "vehicle_no": vehicle.vehicle_no,
                            "vehicle_model": vehicle.model or "",
                            "vehicle_make": vehicle.make or "",
                            "is_corporate": customer_data.get("customer_type") == "Company",
                            "match_source": "vehicle",
                        }
                    )
            except Exception as e:
                frappe.log_error(
                    f"Error fetching customer {vehicle.customer} for vehicle {vehicle.vehicle_no}: {str(e)}",
                    "Vehicle Search Error",
                )
                continue

    except Exception as e:
        frappe.log_error(f"Error searching vehicles: {str(e)}", "Vehicle Search Error")

    # STEP 3: Combine and deduplicate (prioritize vehicle matches)
    seen_customers = {}
    final_results = []

    # Add vehicle matches first (they have more context)
    for row in vehicle_results:
        customer_key = row["name"]
        if customer_key not in seen_customers:
            seen_customers[customer_key] = True
            final_results.append(row)

    # Add direct customer matches that weren't found via vehicles
    for row in customer_results:
        customer_key = row["name"]
        if customer_key not in seen_customers:
            seen_customers[customer_key] = True
            final_results.append(row)

    # Return limited results
    return final_results[:limit]


@frappe.whitelist()
def search_customers(search_term="", pos_profile=None, limit=20):
    """
    ENHANCED: Now calls search_customers_with_vehicles for unified search
    """
    return search_customers_with_vehicles(search_term, pos_profile, limit)


@frappe.whitelist()
def search_vehicles(search_term="", limit=20):
    search_term = (search_term or "").strip()
    limit = int(limit or 20)

    if not search_term:
        return []

    like = "%%%s%%" % frappe.db.escape(search_term).replace("%", "").replace("'", "")

    query = """
        SELECT
            vm.name,
            vm.vehicle_no,
            vm.model,
            v.make,
            vm.customer,
            vm.odometer,
            vm.chasis_no,
            c.customer_name,
            c.mobile_no
        FROM `tabVehicle Master` vm
        LEFT JOIN `tabVehicle` v ON v.name = vm.name
        LEFT JOIN `tabCustomer` c ON vm.customer = c.name
        WHERE (
            vm.vehicle_no LIKE %(like)s
            OR vm.model LIKE %(like)s
            OR v.make LIKE %(like)s
            OR c.customer_name LIKE %(like)s
        )
        ORDER BY vm.modified DESC
        LIMIT %(limit)s
    """

    return frappe.db.sql(query, {"like": like, "limit": limit}, as_dict=1)


@frappe.whitelist()
def get_vehicles_by_search(search_term="", customer=None, limit=20):
    """
    Get vehicles filtered by search term and optionally by customer
    """
    search_term = (search_term or "").strip()
    customer = (customer or "").strip() or None
    limit = min(max(int(limit or 20), 1), 20)

    has_custom_display_name = False
    try:
        has_custom_display_name = bool(
            frappe.db.has_column("tabCustomer", "custom_display_name")
            and frappe.get_meta("Customer").get_field("custom_display_name")
        )
    except Exception:
        has_custom_display_name = False

    custom_display_select = (
        "COALESCE(c.custom_display_name, c.customer_name) AS custom_display_name"
        if has_custom_display_name
        else "c.customer_name AS custom_display_name"
    )

    def _enrich_customer_fields(rows):
        rows = rows or []
        customer_ids = list({r.get("customer") for r in rows if r.get("customer")})
        if not customer_ids:
            return rows

        customer_fields = ["name", "customer_name", "mobile_no"]
        if has_custom_display_name:
            customer_fields.insert(2, "custom_display_name")

        customer_rows = frappe.get_all(
            "Customer",
            filters={"name": ["in", customer_ids]},
            fields=customer_fields,
        )
        customer_map = {c.name: c for c in customer_rows}

        for r in rows:
            cust = customer_map.get(r.get("customer"))
            if not cust:
                r["custom_display_name"] = (
                    r.get("custom_display_name") or r.get("customer_name") or r.get("customer")
                )
                r["customer_name"] = r.get("customer_name") or ""
                r["mobile_no"] = r.get("mobile_no") or ""
                continue
            r["customer_name"] = r.get("customer_name") or cust.customer_name or ""
            r["custom_display_name"] = (
                r.get("custom_display_name")
                or getattr(cust, "custom_display_name", None)
                or cust.customer_name
                or r.get("customer")
                or ""
            )
            r["mobile_no"] = r.get("mobile_no") or cust.mobile_no or ""

        return rows

    # No search term → simple get_all
    if not search_term:
        filters = {}
        if customer:
            filters["customer"] = customer

        vehicles = frappe.get_all(
            "Vehicle Master",
            filters=filters,
            fields=[
                "name",
                "vehicle_no",
                "model",
                "customer",
                "odometer",
                "chasis_no",
            ],
            limit_page_length=limit,
            order_by="modified desc",
        )
        return _enrich_customer_fields(vehicles)
    if len(search_term) < 2:
        return []

    # Prefix + contains patterns. Prefix is cheaper; contains gives expected UX.
    like_pattern = f"{search_term}%"
    contains_pattern = f"%{search_term}%"

    params = {
        "like": like_pattern,
        "contains": contains_pattern,
        "limit": limit,
    }
    customer_clause = ""
    if customer:
        customer_clause = " AND vm.customer = %(customer)s"
        params["customer"] = customer

    try:
        # Fast path: exact match by vehicle_no (uses index if present)
        exact_params = {
            "vehicle_no": search_term,
            "limit": limit,
        }
        exact_customer_clause = ""
        if customer:
            exact_customer_clause = " AND vm.customer = %(customer)s"
            exact_params["customer"] = customer

        vehicles = frappe.db.sql(
            f"""
            SELECT
                vm.name,
                vm.vehicle_no,
                vm.model,
                vm.customer,
                vm.odometer,
                vm.chasis_no,
                c.customer_name,
                {custom_display_select},
                c.mobile_no
            FROM `tabVehicle Master` vm
            LEFT JOIN `tabCustomer` c ON c.name = vm.customer
            WHERE vm.vehicle_no = %(vehicle_no)s
            {exact_customer_clause}
            ORDER BY vm.modified DESC
            LIMIT %(limit)s
            """,
            exact_params,
            as_dict=True,
        )

        if vehicles:
            return vehicles

        # Second pass: prefix match across key searchable fields.
        vehicles = frappe.db.sql(
            f"""
            SELECT
                vm.name,
                vm.vehicle_no,
                vm.registration_number,
                vm.plate_no,
                vm.model,
                vm.customer,
                vm.odometer,
                vm.chasis_no,
                c.customer_name,
                {custom_display_select},
                c.mobile_no
            FROM `tabVehicle Master` vm
            LEFT JOIN `tabCustomer` c ON c.name = vm.customer
            WHERE (
                vm.vehicle_no LIKE %(like)s
                OR vm.registration_number LIKE %(like)s
                OR vm.plate_no LIKE %(like)s
                OR c.mobile_no LIKE %(like)s
            )
            {customer_clause}
            ORDER BY vm.modified DESC
            LIMIT %(limit)s
            """,
            params,
            as_dict=True,
        )

        if vehicles:
            return vehicles

        # Final pass: contains match for non-prefix input (e.g., middle characters)
        vehicles = frappe.db.sql(
            f"""
            SELECT
                vm.name,
                vm.vehicle_no,
                vm.registration_number,
                vm.plate_no,
                vm.model,
                vm.customer,
                vm.odometer,
                vm.chasis_no,
                c.customer_name,
                {custom_display_select},
                c.mobile_no
            FROM `tabVehicle Master` vm
            LEFT JOIN `tabCustomer` c ON c.name = vm.customer
            WHERE (
                vm.vehicle_no LIKE %(contains)s
                OR vm.registration_number LIKE %(contains)s
                OR vm.plate_no LIKE %(contains)s
                OR c.mobile_no LIKE %(contains)s
            )
            {customer_clause}
            ORDER BY vm.modified DESC
            LIMIT %(limit)s
            """,
            params,
            as_dict=True,
        )

        return vehicles

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Vehicle Search Error")
        return []
