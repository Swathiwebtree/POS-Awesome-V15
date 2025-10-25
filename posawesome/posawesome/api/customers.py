# -*- coding: utf-8 -*-
# Copyright (c) 2020, Youssef Restom and contributors
# For license information, please see license.txt

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

# Define the DocType here too for the get_customer_info function
VEHICLE_DOCTYPE = "Vehicle Master"


# ---------------- POS Customer Utilities ----------------


# (get_customer_groups, get_child_nodes, get_customer_group_condition remain the same)
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

    # --- Fix for optional pos_profile and None handling ---
    if not pos_profile:
        active_profile_doc = get_active_pos_profile()
        # FIX: Check for None explicitly before calling .as_json()
        pos_profile = active_profile_doc.as_json() if active_profile_doc else "{}"
    # ------------------------------------------------------

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
def get_customers_count(pos_profile=None, modified_after=None):
    """Return customer count for POS profile, optionally after a date"""

    # --- FIX for TypeError: 'NoneType' object is not callable ---
    if not pos_profile:
        active_profile_doc = get_active_pos_profile()
        # APPLY THE NONE CHECK HERE
        if active_profile_doc:
            pos_profile = active_profile_doc.as_json()
        else:
            # If no active profile, treat pos_profile as an empty object
            pos_profile = "{}"
    # ---------------------------------------------------------------------

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

    return frappe.db.count("Customer", filters)


@frappe.whitelist()
def get_customer_info(customer):
    customer = frappe.get_doc("Customer", customer)

    res = {"loyalty_points": None, "conversion_factor": None}

    # --- Standard fields ---
    res["email_id"] = customer.email_id
    res["mobile_no"] = customer.mobile_no
    res["image"] = customer.image
    res["loyalty_program"] = customer.loyalty_program
    res["customer_price_list"] = customer.default_price_list
    res["customer_group"] = customer.customer_group
    res["customer_type"] = customer.customer_type
    res["territory"] = customer.territory
    res["birthday"] = customer.posa_birthday
    res["gender"] = customer.gender
    res["tax_id"] = customer.tax_id
    res["posa_discount"] = customer.posa_discount
    res["name"] = customer.name
    res["customer_name"] = customer.customer_name
    res["customer_group_price_list"] = frappe.get_value(
        "Customer Group", customer.customer_group, "default_price_list"
    )

    if customer.loyalty_program:
        # Assuming get_loyalty_program_details_with_points is available
        try:
            lp_details = get_loyalty_program_details_with_points(
                customer.name,
                customer.loyalty_program,
                silent=True,
                include_expired_entry=False,
            )
            res["loyalty_points"] = lp_details.get("loyalty_points")
            res["conversion_factor"] = lp_details.get("conversion_factor")
        except NameError:
            frappe.log_error("Loyalty program utility not found.", "POS Customer Info")

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
        (customer.name,),
        as_dict=True,
    )

    if addresses:
        addr = addresses[0]
        res["address_line1"] = addr.address_line1 or ""
        res["address_line2"] = addr.address_line2 or ""
        res["city"] = addr.city or ""
        res["state"] = addr.state or ""
        res["country"] = addr.country or ""

    # --- VEHICLE QUERY (FIXED: Using Vehicle Master and vehicle_no) ---
    vehicles = frappe.get_all(
        VEHICLE_DOCTYPE,  # Correct DocType: "Vehicle Master"
        filters={"customer": customer.name},  # Correct link field
        fields=["name", "vehicle_no"],  # Correct plate field: "vehicle_no"
        limit_page_length=10,
        # REMOVED: as_dict=True to prevent TypeError on newer Frappe versions
    )

    # Map the result structure
    res["vehicles"] = [{"name": v.name, "vehicle_no": v.vehicle_no} for v in vehicles if v.get("vehicle_no")]

    if res["vehicles"]:
        res["vehicle_no"] = res["vehicles"][0].get("vehicle_no")

    return res


@frappe.whitelist()
def get_customer_by_vehicle(vehicle_no):
    """Return customer details for a vehicle number (exact match)."""

    vehicle_data = frappe.get_all(
        VEHICLE_DOCTYPE,  # Correct DocType: "Vehicle Master"
        filters={"vehicle_no": vehicle_no},  # Correct plate field: "vehicle_no"
        # Adjusted fields to match your DocType: customer, model, chasis_no, mobile
        fields=["name", "customer", "model", "chasis_no", "tel_mobile", "vehicle_no"],
        limit_page_length=1,
        # REMOVED: as_dict=True to prevent TypeError on newer Frappe versions
    )

    # frappe.get_all returns a list of objects/tuples depending on as_dict/Frappe version,
    # but the subsequent code expects dictionary access, so we will use an explicit list check
    if not vehicle_data or not vehicle_data[0]:
        return {}

    vehicle = vehicle_data[0]

    # Ensure vehicle_no is present in the final output structure
    if "vehicle_no" not in vehicle and vehicle.get("vehicle_no_field_name"):  # Example of safety net
        vehicle["vehicle_no"] = vehicle.get("vehicle_no_field_name")

    cust_name = vehicle.get("customer")
    if not cust_name:
        # Return vehicle data even if no customer is linked
        return {"vehicle": vehicle, "customer": {}}

    # Retrieve customer details
    try:
        cust_doc = frappe.get_doc("Customer", cust_name)
        return {
            "vehicle": vehicle,
            "customer": {
                "name": cust_doc.name,
                "customer_name": cust_doc.customer_name,
                "email_id": getattr(cust_doc, "email_id", ""),
                "tel_mobile": getattr(cust_doc, "tel_mobile", ""),
                "tax_id": getattr(cust_doc, "tax_id", ""),
                "customer_group": cust_doc.customer_group,
                "territory": cust_doc.territory,
                "posa_discount": cust_doc.posa_discount,
            },
        }
    except frappe.DoesNotExistError:
        # Handle case where customer link is broken
        return {"vehicle": vehicle, "customer": {}}


# ---------------- Customer CRUD & Utilities ----------------


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

            customer.save()

            if address_line1 or city:
                args = {
                    "name": f"{customer.customer_name} - Shipping",
                    "doctype": "Customer",
                    "customer": customer.name,
                    "address_line1": address_line1 or "",
                    "address_line2": "",
                    "city": city or "",
                    "state": "",
                    "pincode": "",
                    "country": country or "",
                }
                make_address(json.dumps(args))

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
            address_doc = frappe.get_doc("Address", existing_address_name)
            address_doc.address_line1 = address_line1 or ""
            address_doc.city = city or ""
            address_doc.country = country or ""
            address_doc.save()
        else:
            if address_line1 or city:
                args = {
                    "name": f"{customer_doc.customer_name} - Shipping",
                    "doctype": "Customer",
                    "customer": customer_doc.name,
                    "address_line1": address_line1 or "",
                    "address_line2": "",
                    "city": city or "",
                    "state": "",
                    "pincode": "",
                    "country": country or "",
                }
                make_address(json.dumps(args))

        return customer_doc


@frappe.whitelist()
def set_customer_info(customer, fieldname, value=""):
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
        contact_doc.save()
        frappe.set_value("Customer", customer, "customer_primary_contact", contact_doc.name)


@frappe.whitelist()
def get_customer_addresses(customer):
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
    args = json.loads(args)
    address = frappe.get_doc(
        {
            "doctype": "Address",
            "address_title": args.get("name"),
            "address_line1": args.get("address_line1"),
            "address_line2": args.get("address_line2"),
            "city": args.get("city"),
            "state": args.get("state"),
            "pincode": args.get("pincode"),
            "country": args.get("country"),
            "address_type": "Shipping",
            "links": [{"link_doctype": args.get("doctype"), "link_name": args.get("customer")}],
        }
    ).insert()
    return address


@frappe.whitelist()
def get_sales_person_names():
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
