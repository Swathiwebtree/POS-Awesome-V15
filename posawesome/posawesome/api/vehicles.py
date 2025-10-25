# -*- coding: utf-8 -*-
# Copyright (c) 2020, Youssef Restom and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

# The custom DocType name as per your system
VEHICLE_DOCTYPE = "Vehicle Master"

# ---------------- POS Vehicle APIs ----------------


@frappe.whitelist()
def get_vehicles_by_customer(customer_name, limit=200, start_after=None):
    """Fetch vehicles for a given customer with pagination."""

    # We use the 'customer' field from your DocType image
    filters = {"customer": customer_name}

    if start_after:
        filters["name"] = [">", start_after]

    vehicles = frappe.get_all(
        VEHICLE_DOCTYPE,  # <-- DocType changed to "Vehicle Master"
        filters=filters,
        fields=[
            "name",
            "customer",
            "vehicle_no",  # <-- Assuming vehicle_no is the License Plate equivalent
            "model",
            "chasis_no",
            "tel_mobile",  # <-- Using 'mobile' field from your DocType
        ],
        order_by="name",
        limit_page_length=limit,
    )

    # Map 'vehicle_no' to 'vehicle_no' (no change needed here, just ensuring the key exists)
    for row in vehicles:
        if "vehicle_no" not in row:
            # Fallback in case the DocType has 'trans_number' or another key
            row["vehicle_no"] = row.get("trans_number") or row.get("name")

    return vehicles


@frappe.whitelist()
def get_customer_by_vehicle(vehicle_no):
    """Return customer details for a vehicle number (exact match)."""
    if not vehicle_no:
        return {}

    # Use 'vehicle_no' for filtering as requested
    vehicle_data = frappe.get_all(
        VEHICLE_DOCTYPE,  # <-- DocType changed to "Vehicle Master"
        filters={"vehicle_no": vehicle_no},
        fields=["name", "customer", "model", "chasis_no", "tel_mobile", "vehicle_no"],
        limit_page_length=1,
    )

    if not vehicle_data:
        return {}

    vehicle = vehicle_data[0]

    cust_name = vehicle.get("customer")
    if not cust_name:
        return {"vehicle": vehicle, "customer": {}}

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
        return {"vehicle": vehicle, "customer": {}}
