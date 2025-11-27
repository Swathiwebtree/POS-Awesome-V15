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
from .utils import get_active_pos_profile
from .vehicles import create_vehicle
from frappe.exceptions import ValidationError, LinkValidationError, DoesNotExistError

from decimal import Decimal, InvalidOperation

# Clarify doctypes:
VEHICLE_DOCTYPE = "Vehicle"          # ERPNext Vehicle doctype
VM_DOCTYPE = "Vehicle Master"        # Your custom Vehicle Master doctype (linked to Vehicle)

# ---------------- LOYALTY POINTS FUNCTIONS ----------------


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
        conditions.append("docstatus IN (0, 1)")

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
def update_loyalty_points(customer_name, company_name, points_amount, entry_type="Earn"):
    """
    Update customer loyalty points
    Args:
        customer_name: Customer ID
        company_name: Company name
        points_amount: Number of points to add/redeem
        entry_type: "Earn" or "Redeem"
    """
    try:
        # Validate inputs
        points_amount = flt(points_amount)
        if points_amount <= 0:
            return {"status": "error", "message": _("Points amount must be greater than 0")}

        # Get customer details
        customer = frappe.get_doc("Customer", customer_name)

        if not customer.loyalty_program:
            return {
                "status": "error",
                "message": _("Customer {0} does not have a loyalty program assigned").format(customer_name),
            }

        loyalty_program = customer.loyalty_program

        # Get loyalty program details for conversion factor
        loyalty_program_doc = frappe.get_doc("Loyalty Program", loyalty_program)
        conversion_factor = flt(loyalty_program_doc.conversion_factor) or 1

        # Calculate redemption amount
        redemption_amount = points_amount * conversion_factor

        # Check if customer has enough points for redemption
        if entry_type == "Redeem":
            current_points = get_loyalty_points(customer_name, loyalty_program, company_name)

            frappe.logger().info(
                f"Redemption Check - Customer: {customer_name}, Current: {current_points}, Requested: {points_amount}"
            )

            if current_points < points_amount:
                return {
                    "status": "error",
                    "message": _("Insufficient loyalty points. Available: {0}, Requested: {1}").format(
                        flt(current_points, 2), flt(points_amount, 2)
                    ),
                    "available_points": current_points,
                    "requested_points": points_amount,
                }

        # Create Loyalty Point Entry
        loyalty_point_entry = frappe.get_doc(
            {
                "doctype": "Loyalty Point Entry",
                "customer": customer_name,
                "loyalty_program": loyalty_program,
                "company": company_name,
                "loyalty_points": points_amount if entry_type == "Earn" else -points_amount,
                "purchase_amount": redemption_amount if entry_type == "Redeem" else 0,
                "expiry_date": frappe.utils.add_days(
                    frappe.utils.nowdate(), loyalty_program_doc.expiry_duration or 365
                ),
                "posting_date": frappe.utils.nowdate(),
                "posting_time": frappe.utils.nowtime(),
            }
        )

        loyalty_point_entry.insert(ignore_permissions=True)
        loyalty_point_entry.submit()

        frappe.db.commit()

        # Get updated balance
        new_balance = get_loyalty_points(customer_name, loyalty_program, company_name)

        frappe.logger().info(
            f"Loyalty points updated - Entry: {loyalty_point_entry.name}, New Balance: {new_balance}"
        )

        return {
            "status": "success",
            "message": _("Loyalty points updated successfully"),
            "points": points_amount,
            "redemption_amount": redemption_amount,
            "new_balance": new_balance,
            "loyalty_point_entry": loyalty_point_entry.name,
        }

    except Exception as e:
        frappe.db.rollback()
        error_msg = str(e)
        frappe.log_error(frappe.get_traceback(), _("Loyalty Points Update Error"))
        frappe.logger().error(f"Loyalty points update failed: {error_msg}")

        # Return error response instead of throwing
        return {"status": "error", "message": _("Error updating loyalty points: {0}").format(error_msg)}


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

        customers = frappe.get_all(
            "Customer",
            filters=filters,
            fields=[
                "name",
                "mobile_no",
                "email_id",
                "tax_id",
                "customer_name",
                "primary_address",
            ],
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


@frappe.whitelist()
def get_customer_info(customer):
    """Get comprehensive customer information including vehicles (defensive about missing fields)."""
    customer_doc = frappe.get_doc("Customer", customer)

    res = {"loyalty_points": 0, "conversion_factor": 0}

    # --- Standard fields ---
    res["email_id"] = getattr(customer_doc, "email_id", None)
    res["mobile_no"] = getattr(customer_doc, "mobile_no", None)
    res["image"] = getattr(customer_doc, "image", None)
    res["loyalty_program"] = getattr(customer_doc, "loyalty_program", None)
    res["customer_price_list"] = getattr(customer_doc, "default_price_list", None)
    res["customer_group"] = getattr(customer_doc, "customer_group", None)
    res["customer_type"] = getattr(customer_doc, "customer_type", None)
    res["territory"] = getattr(customer_doc, "territory", None)
    res["birthday"] = getattr(customer_doc, "posa_birthday", None)
    res["gender"] = getattr(customer_doc, "gender", None)
    res["tax_id"] = getattr(customer_doc, "tax_id", None)
    res["posa_discount"] = getattr(customer_doc, "posa_discount", None)
    res["name"] = customer_doc.name
    res["customer_name"] = customer_doc.customer_name
    res["customer_group_price_list"] = frappe.get_value(
        "Customer Group", customer_doc.customer_group, "default_price_list"
    )

    # Loyalty Points
    if customer_doc.loyalty_program:
        current_company = frappe.db.get_single_value("Global Defaults", "default_company") or "webtree"
        conversion_factor = frappe.db.get_value(
            "Loyalty Program", customer_doc.loyalty_program, "conversion_factor"
        )
        res["conversion_factor"] = flt(conversion_factor) or 1
        res["loyalty_points"] = get_loyalty_points(customer_doc.name, customer_doc.loyalty_program, current_company)

    # --- Address Query (unchanged) ---
    addresses = frappe.db.sql(
        """
        SELECT
            address.name as address_name,
            address.address_line1,
            address.address_line2,
            address.city,
            address.state,
            address.country,
            address.address_type
        FROM `tabAddress` address
        INNER JOIN `tabDynamic Link` link
            ON (address.name = link.parent)
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

    # --- Vehicles with customer details (defensive) ---
    candidates = ["name", "vehicle_no", "model", "make", "odometer", "chasis_no"]

    vehicles = []
    # Try VM_DOCTYPE first (Vehicle Master)
    try:
        fields = _existing_fields(VM_DOCTYPE, candidates)
        if fields:
            vehicles = frappe.get_all(VM_DOCTYPE, filters={"customer": customer_doc.name}, fields=fields, limit_page_length=10)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Error fetching vehicles from VM_DOCTYPE")
        vehicles = []

    # Fallback: try standard VEHICLE_DOCTYPE
    if not vehicles:
        try:
            fallback_doctype = VEHICLE_DOCTYPE or "Vehicle"
            fields = _existing_fields(fallback_doctype, candidates)
            if fields:
                vehicles = frappe.get_all(fallback_doctype, filters={"customer": customer_doc.name}, fields=fields, limit_page_length=10)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Error fetching vehicles from fallback Vehicle doctype")
            vehicles = []

    # Normalize response
    res["vehicles"] = []
    for v in vehicles:
        vehicle_no = v.get("vehicle_no") or v.get("name")
        if not vehicle_no:
            continue
        res["vehicles"].append({
            "name": v.get("name"),
            "vehicle_no": vehicle_no,
            "model": v.get("model", "") if isinstance(v, dict) else "",
            "make": v.get("make", "") if isinstance(v, dict) else "",
            "odometer": v.get("odometer", "") if isinstance(v, dict) else "",
            "chasis_no": v.get("chasis_no", "") if isinstance(v, dict) else "",
            "customer_name": customer_doc.customer_name,
            "mobile_no": customer_doc.mobile_no,
            "customer": customer_doc.name,
        })

    if res["vehicles"]:
        res["vehicle_no"] = res["vehicles"][0].get("vehicle_no")

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
        rows = frappe.db.sql(
            """
            SELECT name
            FROM `tabCustomer`
            WHERE (LOWER(customer_name) LIKE LOWER(%s) OR mobile_no LIKE %s)
            ORDER BY customer_name ASC
            LIMIT %s
            """,
            (search_term, search_term, limit),
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
    Reuse or replace this with your existing builder if you already have one.
    """
    customer_doc = frappe.get_doc("Customer", customer_name)

    res = {"loyalty_points": 0, "conversion_factor": 0}

    # --- Standard fields ---
    res["email_id"] = customer_doc.email_id
    res["mobile_no"] = customer_doc.mobile_no
    # res["image"] = customer_doc.image
    res["loyalty_program"] = customer_doc.loyalty_program
    # res["customer_price_list"] = customer_doc.default_price_list
    # res["customer_group"] = customer_doc.customer_group
    res["customer_type"] = customer_doc.customer_type
    res["territory"] = customer_doc.territory
    # res["birthday"] = customer_doc.posa_birthday
    # res["gender"] = customer_doc.gender
    # res["tax_id"] = customer_doc.tax_id
    # res["posa_discount"] = customer_doc.posa_discount
    res["name"] = customer_doc.name
    res["customer_name"] = customer_doc.customer_name
    res["customer_group_price_list"] = frappe.get_value(
        "Customer Group", customer_doc.customer_group, "default_price_list"
    )

    # Loyalty Points
    if customer_doc.loyalty_program:
        current_company = frappe.db.get_single_value("Global Defaults", "default_company") or "webtree"

        conversion_factor = frappe.db.get_value(
            "Loyalty Program", customer_doc.loyalty_program, "conversion_factor"
        )
        res["conversion_factor"] = flt(conversion_factor) or 1

        loyalty_points = get_loyalty_points(customer_doc.name, customer_doc.loyalty_program, current_company)
        res["loyalty_points"] = loyalty_points

    # --- Address Query (shipping) ---
    addresses = frappe.db.sql(
        """
        SELECT
            address.name as address_name,
            address.address_line1,
            address.address_line2,
            address.city,
            address.state,
            address.country,
            address.address_type
        FROM `tabAddress` address
        INNER JOIN `tabDynamic Link` link
            ON (address.name = link.parent)
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

    # --- Vehicles with customer details ---
    vehicles = frappe.get_all(
        VM_DOCTYPE,
        filters={"customer": customer_doc.name},
        fields=["name", "vehicle_no", "model", "make", "chasis_no", "odometer"],
        limit_page_length=10,
    )

    res["vehicles"] = [
        {
            "name": v.name,
            "vehicle_no": v.vehicle_no,
            "model": v.get("model", ""),
            "make": v.get("make", ""),
            "chasis_no": v.get("chasis_no", ""),
            "odometer": v.get("odometer", ""),
            "customer_name": customer_doc.customer_name,
            "mobile_no": customer_doc.mobile_no,
            "customer": customer_doc.name,
        }
        for v in vehicles
        if v.get("vehicle_no")
    ]

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
            "mobile_no": customer_doc.mobile_no,
            "email_id": customer_doc.email_id,
            "tax_id": customer_doc.tax_id,
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
                    "chasis_no": vehicle.get("chasis_no"),
                },
                "customer": {
                    "name": cust_doc.name,
                    "customer_name": cust_doc.customer_name,
                    "email_id": getattr(cust_doc, "email_id", ""),
                    "mobile_no": getattr(cust_doc, "mobile_no", ""),
                    "tax_id": getattr(cust_doc, "tax_id", ""),
                    "customer_group": cust_doc.customer_group,
                    "territory": cust_doc.territory,
                    "posa_discount": cust_doc.posa_discount,
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

        method = (customer_data.get("method") or "create").lower()
        customer_id = customer_data.get("customer_id") or None
        vehicle_no_from_payload = (vehicle_data or {}).get("vehicle_no") or None

        # ---------- UPDATE OR CREATE CUSTOMER ----------
        if method == "update" and customer_id:
            cust = frappe.get_doc("Customer", customer_id)
            # update safe fields if provided
            for fld in [
                "customer_name",
                "tax_id",
                "mobile_no",
                "email_id",
                "customer_type",
                "gender",
                "referral_code",
            ]:
                if fld in customer_data and customer_data.get(fld) is not None:
                    setattr(cust, fld, customer_data.get(fld))
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
        else:
            # create
            cd = customer_data
            customer_doc = frappe.new_doc("Customer")
            customer_doc.customer_name = cd.get("customer_name")
            customer_doc.customer_type = cd.get("customer_type", "Individual")
            customer_doc.customer_group = cd.get(
                "customer_group"
            ) or frappe.defaults.get_user_default("Customer Group")
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
            try:
                customer_doc.insert(ignore_permissions=True)
                frappe.db.commit()
            except Exception:
                frappe.log_error(frappe.get_traceback(), "Customer create error")
                raise

        # ---------- VEHICLE (existing or create) ----------
        vehicle_doc = None
        vm_doc = None

        # determine effective vehicle identifier to operate on
        effective_vehicle_no = vehicle_no_from_payload
        if not effective_vehicle_no:
            # prefer custom_vehicle_no or vehicle_no fields on customer if present
            if hasattr(customer_doc, "custom_vehicle_no") and getattr(customer_doc, "custom_vehicle_no"):
                effective_vehicle_no = getattr(customer_doc, "custom_vehicle_no")
            elif hasattr(customer_doc, "vehicle_no") and getattr(customer_doc, "vehicle_no"):
                effective_vehicle_no = getattr(customer_doc, "vehicle_no")

        # only act on vehicles if we have an identifier
        if effective_vehicle_no:
            try:
                # --- EXISTING ERPNext Vehicle ---
                if frappe.db.exists(VEHICLE_DOCTYPE, effective_vehicle_no):
                    vehicle_doc = frappe.get_doc(VEHICLE_DOCTYPE, effective_vehicle_no)
                    try:
                        # defensive updates
                        if vehicle_data.get("make") is not None and hasattr(vehicle_doc, "make"):
                            vehicle_doc.make = vehicle_data.get("make")
                        if vehicle_data.get("model") is not None:
                            try:
                                if frappe.db.exists("Vehicle Model", vehicle_data.get("model")):
                                    vehicle_doc.model = vehicle_data.get("model")
                                else:
                                    if hasattr(vehicle_doc, "model"):
                                        vehicle_doc.model = vehicle_data.get("model")
                            except Exception:
                                if hasattr(vehicle_doc, "model"):
                                    vehicle_doc.model = vehicle_data.get("model")
                        if vehicle_data.get("mobile_no") is not None:
                            if hasattr(vehicle_doc, "tel_mobile"):
                                vehicle_doc.tel_mobile = vehicle_data.get("mobile_no")
                            elif hasattr(vehicle_doc, "mobile_no"):
                                vehicle_doc.mobile_no = vehicle_data.get("mobile_no")
                        # odometer
                        od_val = _extract_odometer_from_payload_or_doc(vehicle_data, vehicle_doc)
                        if od_val is not None:
                            _set_odometer_on_doc(vehicle_doc, od_val)

                        # ensure stable identifier and link to customer before saving
                        if effective_vehicle_no:
                            if hasattr(vehicle_doc, "vehicle_no"):
                                vehicle_doc.vehicle_no = effective_vehicle_no
                            elif hasattr(vehicle_doc, "license_plate"):
                                vehicle_doc.license_plate = effective_vehicle_no
                        if hasattr(vehicle_doc, "customer"):
                            vehicle_doc.customer = customer_doc.name

                        vehicle_doc.save(ignore_permissions=True)
                        frappe.db.commit()
                    except Exception:
                        frappe.log_error(frappe.get_traceback(), "Vehicle update error")

                else:
                    # --- CREATE ERPNext Vehicle ---
                    v = frappe.new_doc(VEHICLE_DOCTYPE)
                    try:
                        if vehicle_data.get("make") is not None and hasattr(v, "make"):
                            v.make = vehicle_data.get("make")
                        if vehicle_data.get("model") is not None and hasattr(v, "model"):
                            v.model = vehicle_data.get("model")
                        if vehicle_data.get("mobile_no") is not None:
                            if hasattr(v, "tel_mobile"):
                                v.tel_mobile = vehicle_data.get("mobile_no")
                            elif hasattr(v, "mobile_no"):
                                v.mobile_no = vehicle_data.get("mobile_no")

                        # set obvious identifier fields if they exist
                        if effective_vehicle_no:
                            if hasattr(v, "vehicle_no"):
                                v.vehicle_no = effective_vehicle_no
                            elif hasattr(v, "license_plate"):
                                try:
                                    v.license_plate = effective_vehicle_no
                                except Exception:
                                    pass

                        # link to customer if possible
                        if hasattr(v, "customer"):
                            v.customer = customer_doc.name

                        # odometer
                        od_val = _extract_odometer_from_payload_or_doc(vehicle_data, None)
                        if od_val is not None:
                            _set_odometer_on_doc(v, od_val)

                        # attempt to set name if autoname uses a field that matches
                        try:
                            meta = frappe.get_meta(VEHICLE_DOCTYPE)
                            if getattr(meta, "autoname", "").startswith("field:"):
                                name_field = meta.autoname.split(":", 1)[1]
                                if name_field in ("license_plate", "vehicle_no", "plate", "plate_no"):
                                    v.name = effective_vehicle_no
                        except Exception:
                            pass

                        v.insert(ignore_permissions=True)
                        frappe.db.commit()
                        vehicle_doc = v
                    except Exception:
                        frappe.log_error(frappe.get_traceback(), "Vehicle create error")
                        vehicle_doc = None

                # --- VEHICLE MASTER (VM) create/update ---
                try:
                    if vehicle_doc and frappe.db.exists(VM_DOCTYPE, vehicle_doc.name):
                        vm_doc = frappe.get_doc(VM_DOCTYPE, vehicle_doc.name)
                        try:
                            if vehicle_data.get("make") is not None and hasattr(vm_doc, "make"):
                                vm_doc.make = vehicle_data.get("make")
                            if vehicle_data.get("model") is not None and hasattr(vm_doc, "model"):
                                try:
                                    if frappe.db.exists("Vehicle Model", vehicle_data.get("model")):
                                        vm_doc.model = vehicle_data.get("model")
                                    else:
                                        vm_doc.model = vehicle_data.get("model")
                                except Exception:
                                    vm_doc.model = vehicle_data.get("model")
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
                                vm_doc.vehicle_no = getattr(vehicle_doc, "vehicle_no", getattr(vehicle_doc, "name", None))
                            if hasattr(vm_doc, "customer"):
                                vm_doc.customer = customer_doc.name

                            vm_doc.save(ignore_permissions=True)
                            frappe.db.commit()
                        except Exception:
                            frappe.log_error(frappe.get_traceback(), "VM update error")
                    elif vehicle_doc:
                        # create new VM from vehicle_doc
                        vm = frappe.new_doc(VM_DOCTYPE)
                        try:
                            vm.name = vehicle_doc.name
                            if hasattr(vm, "vehicle_no"):
                                vm.vehicle_no = getattr(vehicle_doc, "vehicle_no", getattr(vehicle_doc, "name", None))
                            if hasattr(vm, "customer"):
                                vm.customer = customer_doc.name
                            if vehicle_data.get("make") is not None and hasattr(vm, "make"):
                                vm.make = vehicle_data.get("make")
                            if vehicle_data.get("model") is not None and hasattr(vm, "model"):
                                vm.model = vehicle_data.get("model")
                            if vehicle_data.get("mobile_no") is not None and hasattr(vm, "tel_mobile"):
                                vm.tel_mobile = vehicle_data.get("mobile_no")
                            od_val = _extract_odometer_from_payload_or_doc(vehicle_data, vehicle_doc)
                            if od_val is not None:
                                _set_odometer_on_doc(vm, od_val)
                            vm.insert(ignore_permissions=True)
                            frappe.db.commit()
                            vm_doc = vm
                        except Exception:
                            frappe.log_error(frappe.get_traceback(), "VM create error")
                            vm_doc = None
                    else:
                        # fallback: VM exists by effective_vehicle_no
                        if effective_vehicle_no and frappe.db.exists(VM_DOCTYPE, effective_vehicle_no):
                            vm_doc = frappe.get_doc(VM_DOCTYPE, effective_vehicle_no)
                            try:
                                od_val = _extract_odometer_from_payload_or_doc(vehicle_data, None)
                                if od_val is not None:
                                    _set_odometer_on_doc(vm_doc, od_val)
                                # ensure vm is linked to customer
                                if hasattr(vm_doc, "customer"):
                                    vm_doc.customer = customer_doc.name
                                if hasattr(vm_doc, "vehicle_no"):
                                    vm_doc.vehicle_no = effective_vehicle_no
                                vm_doc.save(ignore_permissions=True)
                                frappe.db.commit()
                            except Exception:
                                frappe.log_error(frappe.get_traceback(), "VM update fallback error")
                except Exception:
                    frappe.log_error(frappe.get_traceback(), "Vehicle Master logic error")

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

        # Build response
        customer_response = {
            "name": customer_doc.name,
            "customer_name": customer_doc.customer_name,
            "mobile_no": customer_doc.mobile_no,
            "email_id": customer_doc.email_id,
            "tax_id": customer_doc.tax_id,
            "customer_group": getattr(customer_doc, "customer_group", None),
            "territory": getattr(customer_doc, "territory", None),
        }

        vehicle_response = None
        if vm_doc:
            vehicle_response = {
                "name": getattr(vm_doc, "name", None),
                "vehicle_no": getattr(vm_doc, "vehicle_no", None) or getattr(vm_doc, "name", None),
                "make": getattr(vm_doc, "make", None),
                "model": getattr(vm_doc, "model", None),
                "mobile_no": getattr(vm_doc, "tel_mobile", None) or getattr(vm_doc, "mobile_no", None),
                "customer": getattr(vm_doc, "customer", None),
                "odometer": getattr(vm_doc, "odometer", None),
            }
        elif vehicle_doc:
            vehicle_response = {
                "name": getattr(vehicle_doc, "name", None),
                "vehicle_no": getattr(vehicle_doc, "vehicle_no", None) or getattr(vehicle_doc, "name", None),
                "make": getattr(vehicle_doc, "make", None),
                "model": getattr(vehicle_doc, "model", None),
                "mobile_no": getattr(vehicle_doc, "tel_mobile", None) or getattr(vehicle_doc, "mobile_no", None),
                "customer": getattr(vehicle_doc, "customer", None),
                "odometer": getattr(vehicle_doc, "odometer", None),
            }

        return {"customer": customer_response, "vehicle": vehicle_response}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "create_customer_with_vehicle - Unexpected")
        frappe.throw(_("Failed to create/update customer: {0}").format(str(e)))


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
        return create_customer_with_vehicle(json.dumps(c), json.dumps(vehicle or {}), "", pos_profile_doc or "{}")
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "update_customer_api error")
        return {"error": True, "message": str(e)}


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
        return create_customer_with_vehicle(json.dumps(c), json.dumps(vehicle or {}), "", pos_profile_doc or "{}")
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
    Returns list of dict: {name, customer_name, mobile_no, email_id, tax_id, vehicle_no}
    """
    search_term = (search_term or "").strip()
    limit = int(limit or 20)
    if not search_term:
        # if no search term, return limited recent active customers
        return frappe.get_all(
            "Customer",
            filters=[["disabled", "=", 0]],
            fields=["name", "customer_name", "mobile_no", "email_id", "tax_id", "vehicle_no"],
            limit_page_length=limit,
            order_by="modified desc",
        )

    # Build SQL-style like pattern safely
    like = "%%%s%%" % frappe.db.escape(search_term).replace("%", "").replace("'", "")

    # Use SQL for OR across many fields (more reliable & fast)
    rows = frappe.db.sql(
        """
        SELECT name, customer_name, mobile_no, email_id, COALESCE(tax_id, '') AS tax_id, COALESCE(vehicle_no, '') AS vehicle_no
        FROM `tabCustomer`
        WHERE disabled = 0
        AND (
            name LIKE %(like)s
            OR customer_name LIKE %(like)s
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


# ==============================================================================
# FILE 1: posawesome/posawesome/api/customers.py
# ==============================================================================
# Add this new function after the existing search_customers function

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
    limit = int(limit or 20)
    
    if not search_term:
        # Return recent customers
        return frappe.get_all(
            "Customer",
            filters=[["disabled", "=", 0]],
            fields=["name", "customer_name", "mobile_no", "email_id", "tax_id"],
            limit_page_length=limit,
            order_by="modified desc",
        )

    # Build safe LIKE pattern
    like_pattern = "%%%s%%" % frappe.db.escape(search_term).replace("%", "").replace("'", "")

    # STEP 1: Search Customers Directly
    customer_results = frappe.db.sql(
        """
        SELECT 
            c.name,
            c.customer_name,
            c.mobile_no,
            c.email_id,
            c.tax_id,
            NULL as vehicle_no,
            NULL as vehicle_model,
            NULL as vehicle_make,
            'customer' as match_source
        FROM `tabCustomer` c
        WHERE c.disabled = 0
        AND (
            c.name LIKE %(like)s
            OR c.customer_name LIKE %(like)s
            OR c.mobile_no LIKE %(like)s
            OR c.email_id LIKE %(like)s
            OR c.tax_id LIKE %(like)s
        )
        LIMIT %(limit)s
        """,
        {"like": like_pattern, "limit": limit},
        as_dict=1,
    )

    # STEP 2: Search Vehicle Master for matching vehicle numbers
    vehicle_results = []
    try:
        vehicle_matches = frappe.db.sql(
            """
            SELECT 
                vm.name as vehicle_id,
                vm.vehicle_no,
                vm.customer,
                vm.model,
                vm.make
            FROM `tabVehicle Master` vm
            WHERE vm.vehicle_no LIKE %(like)s
            AND vm.customer IS NOT NULL
            AND vm.customer != ''
            LIMIT %(limit)s
            """,
            {"like": like_pattern, "limit": limit},
            as_dict=1,
        )
        
        # Get customer details for each vehicle match
        for vehicle in vehicle_matches:
            if not vehicle.get("customer"):
                continue
                
            try:
                customer_data = frappe.db.get_value(
                    "Customer",
                    vehicle.customer,
                    ["name", "customer_name", "mobile_no", "email_id", "tax_id"],
                    as_dict=1
                )
                
                if customer_data:
                    vehicle_results.append({
                        "name": customer_data.name,
                        "customer_name": customer_data.customer_name,
                        "mobile_no": customer_data.mobile_no or "",
                        "email_id": customer_data.email_id or "",
                        "tax_id": customer_data.tax_id or "",
                        "vehicle_no": vehicle.vehicle_no,
                        "vehicle_model": vehicle.model or "",
                        "vehicle_make": vehicle.make or "",
                        "match_source": "vehicle"
                    })
            except Exception as e:
                frappe.log_error(
                    f"Error fetching customer {vehicle.customer} for vehicle {vehicle.vehicle_no}: {str(e)}",
                    "Vehicle Search Error"
                )
                continue
                
    except Exception as e:
        frappe.log_error(
            f"Error searching vehicles: {str(e)}",
            "Vehicle Search Error"
        )

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


# ==============================================================================
# ALSO UPDATE THE EXISTING search_customers FUNCTION
# Replace the existing search_customers function with this enhanced version:
# ==============================================================================

@frappe.whitelist()
def search_customers(search_term="", pos_profile=None, limit=20):
    """
    ENHANCED: Now calls search_customers_with_vehicles for unified search
    """
    return search_customers_with_vehicles(search_term, pos_profile, limit)


# ==============================================================================
# FILE 2: posawesome/posawesome/api/vehicles.py
# ==============================================================================
# Add this new function to vehicles.py

@frappe.whitelist()
def search_vehicles(search_term="", limit=20):
    """
    Search vehicles by vehicle number, model, make, or customer
    Returns vehicles with customer information
    """
    search_term = (search_term or "").strip()
    limit = int(limit or 20)
    
    if not search_term:
        return []
    
    like_pattern = "%%%s%%" % frappe.db.escape(search_term).replace("%", "").replace("'", "")
    
    try:
        vehicles = frappe.db.sql(
            """
            SELECT 
                vm.name,
                vm.vehicle_no,
                vm.model,
                vm.make,
                vm.customer,
                vm.odometer,
                vm.chasis_no,
                c.customer_name,
                c.mobile_no
            FROM `tabVehicle Master` vm
            LEFT JOIN `tabCustomer` c ON vm.customer = c.name
            WHERE (
                vm.vehicle_no LIKE %(like)s
                OR vm.model LIKE %(like)s
                OR vm.make LIKE %(like)s
                OR c.customer_name LIKE %(like)s
            )
            ORDER BY vm.modified DESC
            LIMIT %(limit)s
            """,
            {"like": like_pattern, "limit": limit},
            as_dict=1
        )
        
        return vehicles
        
    except Exception as e:
        frappe.log_error(
            f"Error searching vehicles: {str(e)}",
            "Vehicle Search Error"
        )
        return []


@frappe.whitelist()
def get_vehicles_by_search(search_term="", customer=None, limit=20):
    """
    Get vehicles filtered by search term and optionally by customer
    """
    search_term = (search_term or "").strip()
    limit = int(limit or 20)
    
    filters = {}
    if customer:
        filters["customer"] = customer
    
    if not search_term:
        return frappe.get_all(
            "Vehicle Master",
            filters=filters,
            fields=["name", "vehicle_no", "model", "make", "customer", "odometer"],
            limit_page_length=limit,
            order_by="modified desc"
        )
    
    like_pattern = "%%%s%%" % frappe.db.escape(search_term).replace("%", "").replace("'", "")
    
    where_clause = "1=1"
    if customer:
        where_clause += f" AND vm.customer = '{frappe.db.escape(customer)}'"
    
    try:
        vehicles = frappe.db.sql(
            f"""
            SELECT 
                vm.name,
                vm.vehicle_no,
                vm.model,
                vm.make,
                vm.customer,
                vm.odometer,
                vm.chasis_no
            FROM `tabVehicle Master` vm
            WHERE {where_clause}
            AND (
                vm.vehicle_no LIKE %(like)s
                OR vm.model LIKE %(like)s
                OR vm.make LIKE %(like)s
            )
            ORDER BY vm.modified DESC
            LIMIT %(limit)s
            """,
            {"like": like_pattern, "limit": limit},
            as_dict=1
        )
        
        return vehicles
        
    except Exception as e:
        frappe.log_error(
            f"Error searching vehicles: {str(e)}",
            "Vehicle Search Error"
        )
        return []