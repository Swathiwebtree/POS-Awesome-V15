# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe
from frappe import _

# Import specific exceptions for better error handling
from frappe.exceptions import ValidationError, DoesNotExistError, NameError

# The custom DocType name as per your system
VEHICLE_DOCTYPE = "Vehicle Master"
CUSTOMER_DOCTYPE = "Customer"

# ============ POS Vehicle APIs ============


@frappe.whitelist()
def create_vehicle(
    vehicle_no,
    customer,
    model=None,
    make=None,
    chasis_no=None,
    color=None,
    mobile_no=None,
    method="create",
    vehicle_id=None,
):
    vehicle_no = (vehicle_no or "").upper().strip()
    customer = customer or ""

    if not vehicle_no:
        frappe.throw(_("Vehicle No is required"))
    if not customer:
        frappe.throw(_("Customer is required"))
    if not make:
        frappe.throw(_("Make is required"))

    model = model or ""
    chasis_no = chasis_no or ""
    color = color or ""
    mobile_no = mobile_no or ""

    try:
        if method == "create":
            if frappe.db.exists("Vehicle", {"license_plate": vehicle_no}):
                frappe.throw(_("Vehicle already exists"))

            vehicle = frappe.get_doc({
                "doctype": "Vehicle",
                "license_plate": vehicle_no,
                "make": make,
                "model": model,
                "chassis_no": chasis_no,
                "color": color,
                "customer": customer
            })
            vehicle.insert(ignore_permissions=True)

        else:
            vehicle = frappe.get_doc("Vehicle", vehicle_id)
            vehicle.make = make
            vehicle.model = model
            vehicle.chassis_no = chasis_no
            vehicle.color = color
            vehicle.customer = customer
            vehicle.save(ignore_permissions=True)

        if frappe.db.exists("Vehicle Master", vehicle.name):
            vm = frappe.get_doc("Vehicle Master", vehicle.name)
        else:
            vm = frappe.get_doc({
                "doctype": "Vehicle Master",
                "name": vehicle.name
            })

        vm.vehicle_no = vehicle_no
        vm.customer = customer
        vm.model = model
        vm.chasis_no = chasis_no
        vm.color = color
        vm.tel_mobile = mobile_no

        if vm.is_new():
            vm.insert(ignore_permissions=True)
        else:
            vm.save(ignore_permissions=True)

        frappe.db.commit()

        return {
            "vehicle": vehicle.as_dict(),
            "vehicle_master": vm.as_dict()
        }

    except Exception:
        frappe.log_error(frappe.get_traceback(), "create_vehicle failed")
        frappe.throw(_("Failed to create vehicle"))



@frappe.whitelist()
def get_vehicle_and_customer(vehicle_no):
    if not vehicle_no:
        return {}

    vehicle_no_clean = str(vehicle_no).strip().upper()

    try:
        vm = frappe.get_doc("Vehicle Master", {"vehicle_no": vehicle_no_clean})

        vehicle = frappe.db.get_value(
            "Vehicle",
            {"license_plate": vehicle_no_clean},
            ["name", "make"],
            as_dict=True,
        )

        customer = (
            frappe.get_doc("Customer", vm.customer)
            if vm.customer and frappe.db.exists("Customer", vm.customer)
            else None
        )

        return {
            "vehicle": {
                "name": vm.name,
                "vehicle_no": vm.vehicle_no,
                "make": vehicle.make if vehicle else "",
                "model": vm.model,
                "chasis_no": vm.chasis_no,
                "color": vm.color,
                "mobile_no": vm.tel_mobile,
            },
            "customer": {
                "name": customer.name,
                "customer_name": customer.customer_name,
                "mobile_no": customer.mobile_no,
                "email_id": customer.email_id,
            } if customer else {},
        }

    except frappe.DoesNotExistError:
        return {"vehicle": {"vehicle_no": vehicle_no_clean}, "customer": {}}



@frappe.whitelist()
def get_all_vehicles_for_customer(customer_name):
    if not customer_name:
        return []

    return frappe.get_all(
        VEHICLE_DOCTYPE,
        filters={"customer": customer_name},
        fields=[
            "name",
            "vehicle_no",
            "model",
            "chasis_no",
            "tel_mobile",
            "customer",
        ],
        order_by="creation desc",
    )



@frappe.whitelist()
def search_vehicles(search_term, limit=50):
    if not search_term or len(search_term) < 2:
        frappe.throw(_("Search term must be at least 2 characters"))

    return frappe.get_all(
        VEHICLE_DOCTYPE,
        filters={"vehicle_no": ["like", f"%{search_term.strip()}%"]},
        fields=[
            "name",
            "vehicle_no",
            "model",
            "chasis_no",
            "tel_mobile",
            "customer",
        ],
        limit_page_length=int(limit),
    )

@frappe.whitelist()
def get_vehicles_by_customer(customer_name, limit=200, start_after=None):
    """
    Fetch vehicles for a given customer with pagination.
    Returns vehicles with customer details including mobile_no.
    """

    if not customer_name:
        frappe.throw(_("Customer name is required"))

    limit = int(limit) if limit else 200

    filters = {"customer": customer_name}

    if start_after:
        filters["name"] = [">", start_after]

    try:
        # Get customer details first (for mobile_no and customer_name)
        cust_doc = frappe.get_doc(CUSTOMER_DOCTYPE, customer_name)

        vehicles = frappe.get_all(
            VEHICLE_DOCTYPE,
            filters=filters,
            fields=[
                "name",
                "customer",
                "vehicle_no",
                # "model",
                # "make",
                "chasis_no",
            ],
            order_by="name asc",
            limit_page_length=limit,
        )

        # Enrich all vehicles with customer details
        for row in vehicles:
            row.setdefault("vehicle_no", row.get("name", ""))
            # row.setdefault("model", "")
            # row.setdefault("make", "")
            row.setdefault("chasis_no", "")
            row["customer"] = customer_name
            row["customer_name"] = cust_doc.customer_name
            row["mobile_no"] = cust_doc.mobile_no or ""
            row["email_id"] = cust_doc.email_id or ""
            row["tax_id"] = cust_doc.tax_id or ""

        frappe.logger().debug(f"Found {len(vehicles)} vehicles for customer: {customer_name}")

        return vehicles

    except frappe.DoesNotExistError:
        frappe.log_error(f"Customer not found: {customer_name}", "Vehicle Fetch Error")
        return []
    except Exception as e:
        frappe.logger().error(f"Error fetching vehicles for {customer_name}: {str(e)}")
        frappe.throw(_("Error fetching vehicles: {0}").format(str(e)))


@frappe.whitelist()
def get_vehicle_models(search_term=""):
    filters = []
    if search_term:
        filters = [["model", "like", f"%{search_term}%"]]

    rows = frappe.get_all(
        VEHICLE_DOCTYPE,
        filters=filters,
        fields=["DISTINCT model"],
        order_by="model asc",
        limit_page_length=20,
    )
    return [r.model for r in rows if r.model]


@frappe.whitelist()
def get_customer_by_vehicle(vehicle_no):
    if not vehicle_no:
        frappe.throw(_("Vehicle number is required"))

    vehicle_no_clean = str(vehicle_no).strip().upper()

    vehicle = None

    found = frappe.get_all(
        "Vehicle Master",
        filters={"vehicle_no": vehicle_no_clean},
        fields=["name", "customer", "model", "chasis_no", "vehicle_no"],
        limit_page_length=1,
    )

    if found:
        vehicle = found[0]

    if not vehicle:
        found = frappe.get_all(
            "Vehicle",
            filters={"license_plate": vehicle_no_clean},
            fields=["name", "customer", "model", "chassis_no"],
            limit_page_length=1,
        )
        if found:
            vehicle = found[0]
            vehicle["vehicle_no"] = vehicle_no_clean
            vehicle["chasis_no"] = vehicle.get("chassis_no")

    if not vehicle:
        return {}

    cust_name = vehicle.get("customer")
    if not cust_name or not frappe.db.exists("Customer", cust_name):
        return {"vehicle": vehicle, "customer": {}}

    cust = frappe.get_doc("Customer", cust_name)

    return {
        "vehicle": {
            "name": vehicle.get("name"),
            "vehicle_no": vehicle.get("vehicle_no"),
            "model": vehicle.get("model"),
            "chasis_no": vehicle.get("chasis_no"),
        },
        "customer": {
            "name": cust.name,
            "customer_name": cust.customer_name,
            "email_id": cust.email_id,
            "mobile_no": cust.mobile_no,
            "tax_id": cust.tax_id,
            "customer_group": cust.customer_group,
            "territory": cust.territory,
            "posa_discount": getattr(cust, "posa_discount", 0),
        },
    }

@frappe.whitelist()
def get_vehicles_by_search(search_term="", limit=1):
    """
    Lookup vehicle by vehicle_no and return vehicle + customer
    (wrapper around get_customer_by_vehicle for compatibility)
    """
    if not search_term:
        return {}

    return get_customer_by_vehicle(search_term)

@frappe.whitelist()
def get_all_vehicles(limit=500):
    """
    Used for POS vehicle dropdown (no customer selected).
    Returns ALL vehicles with linked customer details.
    """

    vehicles = frappe.get_all(
        VEHICLE_DOCTYPE,
        fields=[
            "name",
            "vehicle_no",
            "customer",
        ],
        order_by="modified desc",
        limit_page_length=int(limit),
    )

    if not vehicles:
        return []

    # Fetch customer details in ONE query (important)
    customer_names = list({v.customer for v in vehicles if v.customer})
    customers = frappe.get_all(
        "Customer",
        filters={"name": ["in", customer_names]},
        fields=["name", "customer_name", "mobile_no"],
    )
    customer_map = {c.name: c for c in customers}

    for v in vehicles:
        cust = customer_map.get(v.customer)
        v["customer_name"] = cust.customer_name if cust else ""
        v["mobile_no"] = cust.mobile_no if cust else ""

    return vehicles
    
@frappe.whitelist()
def get_vehicle_makes(search_term=""):
    conditions = ""
    values = []

    if search_term:
        conditions = "WHERE make LIKE %s"
        values.append(f"%{search_term}%")

    rows = frappe.db.sql(
        f"""
        SELECT DISTINCT make
        FROM `tabVehicle`
        {conditions}
        ORDER BY make ASC
        LIMIT 20
        """,
        values,
        as_dict=True,
    )

    return [r.make for r in rows if r.make]
