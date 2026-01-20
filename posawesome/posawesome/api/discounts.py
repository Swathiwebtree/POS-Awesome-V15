import frappe

@frappe.whitelist()
def get_max_discount(customer):
    if not customer:
        return {
            "customer_type": None,
            "invoice_max_discount": 0,
        }

    customer_type = frappe.db.get_value(
        "Customer", customer, "customer_type"
    )

    if not customer_type:
        return {
            "customer_type": None,
            "invoice_max_discount": 0,
        }

    # Get highest priority rule for customer type
    rule = frappe.get_all(
        "POS Discount Rule",
        filters={
            "enabled": 1,
            "customer_type": customer_type,
        },
        fields=["max_discount_"],
        order_by="priority asc",
        limit=1,
    )

    return {
        "customer_type": customer_type,
        "invoice_max_discount": rule[0].max_discount_ if rule else 0,
    }
    
@frappe.whitelist()
def get_vehicle_item_discount(vehicle_no, item_code):
    result = {
        "min_discount": 0,
        "max_discount": 0,
        "auto_apply": False,
        "auto_apply_value": 0,
        "source": None,
        "message": None,
    }

    if not vehicle_no or not item_code:
        return result

    item_group = frappe.db.get_value("Item", item_code, "item_group")
    if not item_group or item_group.strip() == "Engine Oil":
        return result

    vehicle = frappe.db.get_value(
        "Vehicle Master",
        vehicle_no,
        [
            "min_discount_",
            "max_discount_",
            "default_min_discount_",
            "default_max_discount_",
        ],
        as_dict=True,
    )

    if not vehicle:
        return result

    # 1️⃣ Explicit vehicle min/max → NO auto apply
    if (vehicle.min_discount_ and vehicle.min_discount_ > 0) or \
       (vehicle.max_discount_ and vehicle.max_discount_ > 0):

        min_d = vehicle.min_discount_ or 0
        max_d = vehicle.max_discount_ or 0

        return {
            "min_discount": float(min_d),
            "max_discount": float(max_d),
            "auto_apply": False,
            "auto_apply_value": 0,
            "source": "vehicle",
            "message": "Discount based on vehicle settings",
        }

    # 2️⃣ Vehicle DEFAULT → AUTO APPLY MAX
    if (vehicle.default_min_discount_ and vehicle.default_min_discount_ > 0) or \
       (vehicle.default_max_discount_ and vehicle.default_max_discount_ > 0):

        min_d = vehicle.default_min_discount_ or 0
        max_d = vehicle.default_max_discount_ or 0

        return {
            "min_discount": float(min_d),
            "max_discount": float(max_d),
            "auto_apply": True,
            "auto_apply_value": float(max_d),  # 👈 THIS IS THE KEY
            "source": "vehicle_default",
            "message": "Default vehicle discount auto-applied",
        }

    return result
