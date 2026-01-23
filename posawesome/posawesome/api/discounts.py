import frappe
from posawesome.utils import expand_item_groups


SERVICE_ROOT_GROUPS = ["Services"]
STOCK_ROOT_GROUPS = ["Products"]

ENGINE_OIL_GROUP = "Engine Oil"



def get_all_service_groups():
    """Return ALL service item groups (tree expanded)"""
    return set(expand_item_groups(SERVICE_ROOT_GROUPS))


def get_all_stock_groups():
    """Return ALL stock item groups (tree expanded)"""
    return set(expand_item_groups(STOCK_ROOT_GROUPS))


def get_item_group(item_code=None, item_group=None):
    if not item_group and item_code:
        item_group = frappe.db.get_value("Item", item_code, "item_group")
    return item_group.strip() if item_group else None



def is_service_item(item_code=None, item_group=None):
    item_group = get_item_group(item_code, item_group)
    if not item_group:
        return False

    if item_group == ENGINE_OIL_GROUP:
        return False

    return item_group in get_all_service_groups()


def is_stock_item(item_code=None, item_group=None):
    item_group = get_item_group(item_code, item_group)
    if not item_group:
        return False

    if item_group == ENGINE_OIL_GROUP:
        return False

    return item_group in get_all_stock_groups()


@frappe.whitelist()
def get_max_discount(customer):
    if not customer:
        return {"customer_type": None, "invoice_max_discount": None}

    customer_type = frappe.db.get_value("Customer", customer, "customer_type")
    if not customer_type:
        return {"customer_type": None, "invoice_max_discount": None}

    rule = frappe.get_all(
        "POS Discount Rule",
        filters={"enabled": 1, "customer_type": customer_type},
        fields=["max_discount_"],
        order_by="priority asc",
        limit=1,
    )

    return {
        "customer_type": customer_type,
        "invoice_max_discount": float(rule[0].max_discount_ or 0) if rule else None,
    }



@frappe.whitelist()
def get_vehicle_item_discount(vehicle_no, item_code):

    result = {
        "max_discount": 0,
        "auto_apply": False,
        "auto_apply_value": 0,
        "source": None,
        "message": None,
        "item_type": None,
    }

    if not vehicle_no or not item_code:
        return result

    item_group = get_item_group(item_code=item_code)
    if not item_group:
        return result

    if item_group == ENGINE_OIL_GROUP:
        result.update({
            "message": "Engine Oil items are not eligible for discount",
            "item_type": "engine_oil"
        })
        return result

    is_service = is_service_item(item_group=item_group)
    is_stock = is_stock_item(item_group=item_group)

    if not is_service and not is_stock:
        result["message"] = f"Item group '{item_group}' not configured for discounts"
        return result

    result["item_type"] = "service" if is_service else "stock"

    vehicle = frappe.db.get_value(
        "Vehicle Master",
        vehicle_no,
        [
            "custom_default_discount___stock_items",
            "custom_default_discount___service_items",
            "custom_max_discount___stock_items",
            "custom_max_discount___service_items",
        ],
        as_dict=True,
    )

    if not vehicle:
        result["message"] = f"Vehicle {vehicle_no} not found"
        return result

    if is_service:
        default_max = vehicle.custom_default_discount___service_items or 0
        manual_max = vehicle.custom_max_discount___service_items or 0
        field = "service"
    else:
        default_max = vehicle.custom_default_discount___stock_items or 0
        manual_max = vehicle.custom_max_discount___stock_items or 0
        field = "stock"

    if manual_max > 0:
        return {
            "max_discount": float(manual_max),
            "auto_apply": False,
            "source": f"vehicle_manual_max_{field}",
            "message": f"Manual discount allowed up to {manual_max}%",
            "item_type": result["item_type"],
        }

    if default_max > 0:
        return {
            "max_discount": float(default_max),
            "auto_apply": True,
            "auto_apply_value": float(default_max),
            "source": f"vehicle_default_max_{field}",
            "message": f"Auto-applied {default_max}%",
            "item_type": result["item_type"],
        }

    result["message"] = f"No discount configured for {field} items"
    return result



@frappe.whitelist()
def validate_discount(vehicle_no, item_code, discount_percentage):

    discount_percentage = float(discount_percentage or 0)

    if discount_percentage <= 0:
        return {"is_valid": True, "message": "No discount applied"}

    rules = get_vehicle_item_discount(vehicle_no, item_code)

    if rules.get("item_type") == "engine_oil":
        return {"is_valid": False, "message": "Discount not allowed for Engine Oil"}

    max_allowed = rules.get("max_discount", 0)

    if discount_percentage > max_allowed:
        return {
            "is_valid": False,
            "message": f"Discount exceeds maximum allowed {max_allowed}%",
            "max_allowed": max_allowed,
        }

    return {
        "is_valid": True,
        "message": f"Discount {discount_percentage}% is valid",
        "max_allowed": max_allowed,
    }



@frappe.whitelist()
def get_vehicle_by_customer(customer):
    if not customer:
        return None

    vehicles = frappe.get_all(
        "Vehicle Master",
        filters={"customer": customer},
        fields=[
            "name",
            "vehicle_no",
            "model",
            "custom_default_discount___stock_items",
            "custom_default_discount___service_items",
            "custom_max_discount___stock_items",
            "custom_max_discount___service_items",
        ],
        limit=1,
    )

    return vehicles[0] if vehicles else None


@frappe.whitelist()
def get_customer_by_vehicle(vehicle_no):
    return frappe.db.get_value("Vehicle Master", vehicle_no, "customer")
