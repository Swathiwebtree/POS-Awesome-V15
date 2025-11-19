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

# Define the DocType here too for the get_customer_info function
VEHICLE_DOCTYPE = "Vehicle Master"


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


@frappe.whitelist()
def get_customer_info(customer):
    """Get comprehensive customer information including vehicles"""
    customer_doc = frappe.get_doc("Customer", customer)

    res = {"loyalty_points": 0, "conversion_factor": 0}

    # --- Standard fields ---
    res["email_id"] = customer_doc.email_id
    res["mobile_no"] = customer_doc.mobile_no
    res["image"] = customer_doc.image
    res["loyalty_program"] = customer_doc.loyalty_program
    res["customer_price_list"] = customer_doc.default_price_list
    res["customer_group"] = customer_doc.customer_group
    res["customer_type"] = customer_doc.customer_type
    res["territory"] = customer_doc.territory
    res["birthday"] = customer_doc.posa_birthday
    res["gender"] = customer_doc.gender
    res["tax_id"] = customer_doc.tax_id
    res["posa_discount"] = customer_doc.posa_discount
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

        # Get loyalty points using the helper function
        loyalty_points = get_loyalty_points(customer_doc.name, customer_doc.loyalty_program, current_company)
        res["loyalty_points"] = loyalty_points

    # --- Address Query ---
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
        VEHICLE_DOCTYPE,
        filters={"customer": customer_doc.name},
        fields=["name", "vehicle_no"],
        limit_page_length=10,
    )

    res["vehicles"] = [
        {
            "name": v.name,
            "vehicle_no": v.vehicle_no,
            "model": v.get("model", ""),
            "make": v.get("make", ""),
            "chasis_no": v.get("chasis_no", ""),
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
    """Return customer + vehicle details using exact vehicle_no match."""

    # Fetch vehicle from Vehicle Master
    vehicle_data = frappe.get_all(
        "Vehicle Master",
        filters={"vehicle_no": vehicle_no},
        fields=["name", "customer", "model", "chasis_no", "tel_mobile", "vehicle_no"],
        limit_page_length=1,
        as_dict=True,
    )

    # If no vehicle found
    if not vehicle_data:
        return {"message": "No vehicle found", "vehicle": {}, "customer": {}}

    vehicle = vehicle_data[0]

    # If vehicle exists but no customer linked
    if not vehicle.get("customer"):
        return {"message": "Vehicle found but no customer linked", "vehicle": vehicle, "customer": {}}

    # Fetch customer doc
    try:
        cust_doc = frappe.get_doc("Customer", vehicle.customer)

        customer = {
            "name": cust_doc.name,
            "customer_name": cust_doc.customer_name,
            "email_id": cust_doc.email_id,
            "mobile_no": cust_doc.mobile_no,
            "tax_id": cust_doc.tax_id,
            "customer_group": cust_doc.customer_group,
            "territory": cust_doc.territory,
            "posa_discount": getattr(cust_doc, "posa_discount", 0),
        }

        return {
            "message": "Success",
            "vehicle": vehicle,
            "customer": customer,
        }

    except frappe.DoesNotExistError:
        return {
            "message": "Vehicle found but linked customer does not exist",
            "vehicle": vehicle,
            "customer": {},
        }


def _parse_numeric(value):
    """Convert value to Decimal (preferred) or float/int fallback; return None if invalid."""
    if value is None or value == "":
        return None
    # already numeric
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))
    # try to parse strings
    try:
        # strip commas and whitespace
        s = str(value).replace(",", "").strip()
        return Decimal(s)
    except (InvalidOperation, ValueError, TypeError):
        try:
            return Decimal(str(float(s)))
        except Exception:
            return None


def _set_odometer_on_doc(doc, od_value):
    """
    Write odometer value to doc on common odometer-like fields that exist.
    Returns True if any field was set.
    """
    if od_value is None:
        return False

    set_any = False
    # prefer a canonical 'odometer' field if present
    for fname in ("odometer", "odometer_value_last", "odometer_value", "odometer_reading"):
        if hasattr(doc, fname):
            try:
                # use Decimal for numeric precision
                setattr(doc, fname, od_value)
                set_any = True
            except Exception:
                # if direct set fails (rare), skip it
                pass

    # if there is a generic numeric field (like Float or Int), try 'odometer' fallback
    if not set_any and hasattr(doc, "odometer"):
        try:
            doc.odometer = od_value
            set_any = True
        except Exception:
            pass

    return set_any


@frappe.whitelist()
def create_customer_with_vehicle(customer, vehicle, company, pos_profile_doc):
    """
    Create/update Customer and create Vehicle (ERPNext) + Vehicle Master safely,
    link Vehicle Master to Customer.custom_vehicle_no, and robustly write odometer
    into both Vehicle and Vehicle Master when present.
    """

    import json
    from decimal import Decimal, InvalidOperation
    from frappe.exceptions import ValidationError, LinkValidationError

    def _clear_vehicle_links_on_customer(doc):
        try:
            meta = frappe.get_meta("Customer")
            for f in meta.fields:
                if f.fieldtype == "Link" and (f.options or "").strip() in ("Vehicle", "Vehicle Master"):
                    if getattr(doc, f.fieldname, None):
                        setattr(doc, f.fieldname, None)
            if hasattr(doc, "custom_vehicle_no") and getattr(doc, "custom_vehicle_no", None):
                setattr(doc, "custom_vehicle_no", None)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "clear_vehicle_links_on_customer error")

    def _parse_numeric(value):
        """Convert value to Decimal. Return None if not parseable."""
        if value is None or value == "":
            return None
        # if already numeric
        if isinstance(value, (int, float, Decimal)):
            try:
                return Decimal(str(value))
            except Exception:
                return None
        s = str(value).strip()
        # remove common thousand separators
        s = s.replace(",", "")
        try:
            return Decimal(s)
        except (InvalidOperation, ValueError, TypeError):
            try:
                return Decimal(str(float(s)))
            except Exception:
                return None

    def _set_odometer_on_doc(doc, od_value):
        """
        Write odometer value to doc on common odometer-like fields that exist.
        Returns True if any field was set.
        """
        if od_value is None:
            return False

        set_any = False
        for fname in ("odometer", "odometer_value_last", "odometer_value", "odometer_reading"):
            if hasattr(doc, fname):
                try:
                    setattr(doc, fname, od_value)
                    set_any = True
                except Exception:
                    # skip failing writes
                    pass

        # fallback try 'odometer' if no named fields were present
        if not set_any and hasattr(doc, "odometer"):
            try:
                doc.odometer = od_value
                set_any = True
            except Exception:
                pass

        return set_any

    def _extract_odometer_from_payload_or_doc(vehicle_data, vehicle_doc=None):
        """Try payload keys first, then vehicle_doc fields as fallback. Returns Decimal or None."""
        candidates = [
            "odometer",
            "odometer_value_last",
            "odometer_value",
            "odometer_last",
            "odometer_reading",
        ]
        for k in candidates:
            if vehicle_data and vehicle_data.get(k) not in (None, ""):
                parsed = _parse_numeric(vehicle_data.get(k))
                if parsed is not None:
                    return parsed
        # fallback to vehicle_doc if provided
        if vehicle_doc:
            for k in candidates + ["odometer", "odometer_value_last"]:
                v = getattr(vehicle_doc, k, None)
                if v not in (None, ""):
                    parsed = _parse_numeric(v)
                    if parsed is not None:
                        return parsed
        return None

    try:
        customer_data = json.loads(customer) if isinstance(customer, str) else (customer or {})
        vehicle_data = json.loads(vehicle) if isinstance(vehicle, str) else (vehicle or {})
        pos_profile = (
            json.loads(pos_profile_doc) if isinstance(pos_profile_doc, str) else (pos_profile_doc or {})
        )

        method = (customer_data.pop("method", "create") or "create").lower()
        customer_id = customer_data.get("customer_id")
        vehicle_no = (vehicle_data or {}).get("vehicle_no")

        # ---------- UPDATE ----------
        if method == "update" and customer_id:
            customer_doc = frappe.get_doc("Customer", customer_id)
            for fld in [
                "customer_name",
                "tax_id",
                "mobile_no",
                "email_id",
                "customer_group",
                "territory",
                "customer_type",
                "gender",
                "referral_code",
            ]:
                if fld in customer_data and customer_data.get(fld) is not None:
                    setattr(customer_doc, fld, customer_data.get(fld))
            if customer_data.get("birthday"):
                customer_doc.posa_birthday = customer_data.get("birthday")

            _clear_vehicle_links_on_customer(customer_doc)
            customer_doc.save(ignore_permissions=True)
            frappe.db.commit()

        # ---------- CREATE ----------
        else:
            customer_doc = frappe.new_doc("Customer")
            customer_doc.customer_name = customer_data.get("customer_name")
            customer_doc.customer_type = customer_data.get("customer_type", "Individual")
            customer_doc.customer_group = customer_data.get("customer_group")
            customer_doc.territory = customer_data.get("territory")

            if customer_data.get("tax_id"):
                customer_doc.tax_id = customer_data.get("tax_id")
            if customer_data.get("mobile_no"):
                customer_doc.mobile_no = customer_data.get("mobile_no")
            if customer_data.get("email_id"):
                customer_doc.email_id = customer_data.get("email_id")
            if customer_data.get("gender"):
                customer_doc.gender = customer_data.get("gender")
            if customer_data.get("referral_code"):
                customer_doc.posa_referral_code = customer_data.get("referral_code")
            if customer_data.get("birthday"):
                customer_doc.posa_birthday = customer_data.get("birthday")

            if hasattr(customer_doc, "custom_vehicle_no"):
                customer_doc.custom_vehicle_no = None
            _clear_vehicle_links_on_customer(customer_doc)

            customer_doc.insert(ignore_permissions=True)
            frappe.db.commit()

            if customer_data.get("address_line1"):
                try:
                    create_customer_address(
                        customer_doc.name,
                        customer_data.get("address_line1"),
                        customer_data.get("city"),
                        customer_data.get("country", "Pakistan"),
                    )
                except Exception:
                    frappe.log_error(frappe.get_traceback(), "create_customer_address error")

        # ---------- VEHICLE (ERPNext) creation — create Vehicle first ----------
        vehicle_doc = None
        vm_doc = None

        if vehicle_no:
            try:
                # fetch existing Vehicle if present
                if frappe.db.exists("Vehicle", vehicle_no):
                    vehicle_doc = frappe.get_doc("Vehicle", vehicle_no)
                    # if incoming odometer present, write it to existing Vehicle
                    od_val_existing = _extract_odometer_from_payload_or_doc(vehicle_data, vehicle_doc)
                    if od_val_existing is not None:
                        if _set_odometer_on_doc(vehicle_doc, od_val_existing):
                            vehicle_doc.save(ignore_permissions=True)
                            frappe.db.commit()
                else:
                    v = frappe.new_doc("Vehicle")

                    # map incoming fields (defensively)
                    if vehicle_data.get("make") is not None:
                        v.make = vehicle_data.get("make")
                    if vehicle_data.get("model") is not None:
                        # check existence of Vehicle Model link before assigning if it's Link
                        if frappe.db.exists("Vehicle Model", vehicle_data.get("model")):
                            v.model = vehicle_data.get("model")
                        else:
                            # leave blank rather than assigning invalid link
                            pass

                    if vehicle_data.get("mobile_no") is not None:
                        if hasattr(v, "tel_mobile"):
                            v.tel_mobile = vehicle_data.get("mobile_no")
                        elif hasattr(v, "mobile_no"):
                            v.mobile_no = vehicle_data.get("mobile_no")

                    # fill required fields defensively from meta
                    try:
                        vehicle_meta = frappe.get_meta("Vehicle")
                    except Exception:
                        vehicle_meta = None

                    if vehicle_meta:
                        for f in vehicle_meta.fields:
                            if getattr(f, "reqd", False):
                                fname = f.fieldname
                                if fname == "name":
                                    continue
                                if vehicle_data and vehicle_data.get(fname) not in (None, ""):
                                    # if Link, verify existence
                                    if f.fieldtype == "Link":
                                        if frappe.db.exists(f.options, vehicle_data.get(fname)):
                                            setattr(v, fname, vehicle_data.get(fname))
                                        else:
                                            # skip invalid link
                                            pass
                                    else:
                                        setattr(v, fname, vehicle_data.get(fname))
                                    continue
                                if fname in ("license_plate", "plate_no", "plate", "vehicle_no"):
                                    setattr(v, fname, vehicle_no)
                                    continue
                                if fname in ("odometer_value_last", "odometer"):
                                    od_tmp = _extract_odometer_from_payload_or_doc(vehicle_data, None)
                                    setattr(v, fname, od_tmp if od_tmp is not None else 0)
                                    continue
                                if fname in ("fuel_uom", "fuel_type"):
                                    setattr(v, fname, vehicle_data.get(fname) or "L")
                                    continue
                                setattr(v, fname, vehicle_data.get(fname) or "")

                    # minimal defaults
                    if not getattr(v, "make", None):
                        v.make = vehicle_data.get("make") or "Unknown"
                    if not getattr(v, "model", None):
                        v.model = vehicle_data.get("model") or None
                    if not getattr(v, "license_plate", None) and not getattr(v, "vehicle_no", None):
                        try:
                            v.license_plate = vehicle_no
                        except Exception:
                            pass

                    # attempt to set name if Vehicle autoname expects a field that matches vehicle_no
                    try:
                        vehicle_autoname = (vehicle_meta.autoname or "").strip() if vehicle_meta else ""
                        if vehicle_autoname.startswith("field:"):
                            name_field = vehicle_autoname.split(":", 1)[1]
                            if name_field in ("license_plate", "vehicle_no", "plate", "plate_no"):
                                v.name = vehicle_no
                    except Exception:
                        pass

                    # write odometer values robustly
                    od_val = _extract_odometer_from_payload_or_doc(vehicle_data, None)
                    if od_val is not None:
                        _set_odometer_on_doc(v, od_val)

                    # insert vehicle doc (tolerant strategy)
                    try:
                        v.insert(ignore_permissions=True)
                    except LinkValidationError:
                        # clear invalid link fields and retry
                        for f in vehicle_meta.fields or []:
                            if f.fieldtype == "Link":
                                val = getattr(v, f.fieldname, None)
                                if val and not frappe.db.exists(f.options, val):
                                    setattr(v, f.fieldname, None)
                        v.insert(ignore_permissions=True)
                    except Exception:
                        # retry without forced name if necessary
                        if hasattr(v, "name"):
                            try:
                                delattr(v, "name")
                            except Exception:
                                pass
                        v.insert(ignore_permissions=True)

                    frappe.db.commit()
                    vehicle_doc = v

            except Exception:
                frappe.log_error(frappe.get_traceback(), "Vehicle creation error")
                vehicle_doc = None

            # ---------- VEHICLE MASTER creation: create VM linking to Vehicle ----------
            try:
                vm_meta = None
                try:
                    vm_meta = frappe.get_meta("Vehicle Master")
                except Exception:
                    vm_meta = None

                if vehicle_doc:
                    # existing VM (same name)
                    if frappe.db.exists("Vehicle Master", vehicle_doc.name):
                        vm_doc = frappe.get_doc("Vehicle Master", vehicle_doc.name)
                        # update odometer if provided
                        od_val = _extract_odometer_from_payload_or_doc(vehicle_data, vehicle_doc)
                        if od_val is not None:
                            if _set_odometer_on_doc(vm_doc, od_val):
                                vm_doc.save(ignore_permissions=True)
                                frappe.db.commit()
                    else:
                        vm = frappe.new_doc("Vehicle Master")
                        vm.name = vehicle_doc.name
                        vm.vehicle_no = vehicle_doc.name
                        vm.customer = customer_doc.name
                        if vehicle_data.get("make") is not None:
                            vm.make = vehicle_data.get("make")
                        if vehicle_data.get("model") is not None:
                            # only set if Vehicle Model exists
                            if frappe.db.exists("Vehicle Model", vehicle_data.get("model")):
                                vm.model = vehicle_data.get("model")
                        if vehicle_data.get("mobile_no") is not None:
                            vm.tel_mobile = vehicle_data.get("mobile_no")
                        od_val = _extract_odometer_from_payload_or_doc(vehicle_data, vehicle_doc)
                        if od_val is not None:
                            _set_odometer_on_doc(vm, od_val)
                        # insert VM
                        try:
                            vm.insert(ignore_permissions=True)
                        except LinkValidationError:
                            # clear invalid link fields and retry
                            for f in vm_meta.fields or []:
                                if f.fieldtype == "Link":
                                    val = getattr(vm, f.fieldname, None)
                                    if val and not frappe.db.exists(f.options, val):
                                        setattr(vm, f.fieldname, None)
                            vm.insert(ignore_permissions=True)
                        frappe.db.commit()
                        vm_doc = vm
                else:
                    # existing VM by vehicle_no
                    if frappe.db.exists("Vehicle Master", vehicle_no):
                        vm_doc = frappe.get_doc("Vehicle Master", vehicle_no)
                        od_val = _extract_odometer_from_payload_or_doc(vehicle_data, vehicle_doc)
                        if od_val is not None:
                            if _set_odometer_on_doc(vm_doc, od_val):
                                vm_doc.save(ignore_permissions=True)
                                frappe.db.commit()

            except Exception:
                frappe.log_error(frappe.get_traceback(), "Vehicle Master creation error")
                vm_doc = None

        # ---------- LINK back to customer using custom_vehicle_no ----------
        if vm_doc:
            try:
                if hasattr(customer_doc, "custom_vehicle_no"):
                    customer_doc.custom_vehicle_no = vm_doc.name
                else:
                    customer_doc.vehicle_no = vm_doc.name
                customer_doc.save(ignore_permissions=True)
                frappe.db.commit()
            except Exception:
                frappe.log_error(frappe.get_traceback(), "Failed to link VM to Customer")

        # ---------- BUILD RESPONSE ----------
        customer_response = {
            "name": customer_doc.name,
            "customer_name": customer_doc.customer_name,
            "mobile_no": customer_doc.mobile_no,
            "email_id": customer_doc.email_id,
            "tax_id": customer_doc.tax_id,
            "customer_group": customer_doc.customer_group,
            "territory": customer_doc.territory,
            "gender": customer_doc.gender,
            "birthday": getattr(customer_doc, "posa_birthday", None),
            "referral_code": getattr(customer_doc, "posa_referral_code", None),
            "vehicle_no": getattr(customer_doc, "custom_vehicle_no", None)
            or getattr(customer_doc, "vehicle_no", None),
            "loyalty_program": getattr(customer_doc, "loyalty_program", None),
            "loyalty_points": getattr(customer_doc, "loyalty_points", None),
        }

        vehicle_response = None
        if vm_doc:
            vehicle_response = {
                "name": vm_doc.name,
                "vehicle_no": vm_doc.vehicle_no,
                "make": getattr(vm_doc, "make", None),
                "model": getattr(vm_doc, "model", None),
                "mobile_no": getattr(vm_doc, "tel_mobile", None),
                "customer": getattr(vm_doc, "customer", None),
                "odometer": getattr(vm_doc, "odometer", None),
            }

        return {"customer": customer_response, "vehicle": vehicle_response}

    except (ValidationError, LinkValidationError):
        raise

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "create_customer_with_vehicle - Unexpected")
        frappe.throw(_("Failed to create/update customer: {0}").format(str(e)))


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
def search_customers(search_term=""):
    """
    Search customers by ID or Name. Returns list for Vue Autocomplete.
    """
    filters = {}
    if search_term:
        # Search by Customer ID (name) OR Customer Name
        filters = [
            ["name", "like", f"%{search_term}%"],
            ["customer_name", "like", f"%{search_term}%"],
        ]

    # Note: 'name' is the ID/DocName, 'customer_name' is the display name.
    customers = frappe.get_list(
        "Customer",
        filters=filters,
        fields=["name", "customer_name"],
        limit_page_length=20,
        or_filters=bool(search_term),  # Use OR filtering if a search term exists
    )

    return customers


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
