import frappe
from posawesome.posawesome.api.utils import expand_item_groups

SERVICE_ROOT_GROUPS = ["Services"]
STOCK_ROOT_GROUPS = ["Products"]


def get_all_service_groups():
    return set(expand_item_groups(SERVICE_ROOT_GROUPS))


def get_all_stock_groups():
    return set(expand_item_groups(STOCK_ROOT_GROUPS))


def get_item_group(item_code=None, item_group=None):
    if not item_group and item_code:
        item_group = frappe.db.get_value("Item", item_code, "item_group")
    return item_group.strip() if item_group else None


def is_engine_oil(item_group: str) -> bool:
    return bool(item_group and "engine oil" in item_group.lower())


def is_service_item(item_code=None, item_group=None):
    item_group = get_item_group(item_code, item_group)
    return bool(
        item_group
        and not is_engine_oil(item_group)
        and item_group in get_all_service_groups()
    )


def is_stock_item(item_code=None, item_group=None):
    item_group = get_item_group(item_code, item_group)
    return bool(
        item_group
        and not is_engine_oil(item_group)
        and item_group in get_all_stock_groups()
    )



def get_customer_discount_config(customer):
    return frappe.db.get_value(
        "Customer",
        customer,
        [
            "custom_custom_default_discount___service_items",
            "custom_custom_default_discount___stock_items",
            "custom_custom_max_discount___service_items",
            "custom_custom_max_discount___stock_items",
        ],
        as_dict=True,
    )



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
def get_customer_item_discount(customer, item_code):

    result = {
        "max_discount": 0,
        "auto_apply": False,
        "auto_apply_value": 0,
        "item_type": None,
        "message": None,
    }

    if not customer or not item_code:
        return result

    item_group = get_item_group(item_code=item_code)
    if not item_group:
        return result

    if is_engine_oil(item_group):
        return {
            "item_type": "engine_oil",
            "max_discount": 0,
            "auto_apply": False,
            "message": "Engine Oil items are not eligible for discount",
        }

    is_service = is_service_item(item_group=item_group)
    is_stock = is_stock_item(item_group=item_group)

    if not is_service and not is_stock:
        return result

    discounts = get_customer_discount_config(customer)
    if not discounts:
        return result

    if is_service:
        default_max = discounts.custom_custom_default_discount___service_items or 0
        manual_max = discounts.custom_custom_max_discount___service_items or 0
        item_type = "service"
    else:
        default_max = discounts.custom_custom_default_discount___stock_items or 0
        manual_max = discounts.custom_custom_max_discount___stock_items or 0
        item_type = "stock"

    # Manual override
    if manual_max > 0:
        return {
            "item_type": item_type,
            "max_discount": float(manual_max),
            "auto_apply": False,
            "message": f"Manual discount allowed up to {manual_max}%",
        }

    # Auto apply
    if default_max > 0:
        return {
            "item_type": item_type,
            "max_discount": float(default_max),
            "auto_apply": True,
            "auto_apply_value": float(default_max),
            "message": f"Auto-applied {default_max}%",
        }

    return result



@frappe.whitelist()
def validate_discount(customer, item_code, discount_percentage):

    discount_percentage = float(discount_percentage or 0)

    if discount_percentage <= 0:
        return {"is_valid": True}

    rules = get_customer_item_discount(customer, item_code)

    if rules.get("item_type") == "engine_oil":
        return {"is_valid": False, "message": "Discount not allowed for Engine Oil"}

    max_allowed = rules.get("max_discount", 0)

    if discount_percentage > max_allowed:
        return {
            "is_valid": False,
            "message": f"Discount exceeds maximum allowed {max_allowed}%",
            "max_allowed": max_allowed,
        }

    return {"is_valid": True, "max_allowed": max_allowed}

