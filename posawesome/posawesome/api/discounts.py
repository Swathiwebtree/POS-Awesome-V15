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


def get_item_context(item_code=None, item_group=None):
    if item_group and item_code:
        is_stock = frappe.db.get_value("Item", item_code, "is_stock_item")
        return {
            "item_group": item_group.strip() if item_group else None,
            "is_stock_item": int(is_stock or 0),
        }

    if item_code:
        item_doc = frappe.db.get_value(
            "Item",
            item_code,
            ["item_group", "is_stock_item"],
            as_dict=True,
        )
        if item_doc:
            return {
                "item_group": (item_doc.item_group or "").strip() or None,
                "is_stock_item": int(item_doc.is_stock_item or 0),
            }

    return {
        "item_group": get_item_group(item_group=item_group),
        "is_stock_item": None,
    }


def is_engine_oil(item_group: str) -> bool:
    return bool(item_group and "engine oil" in item_group.lower())


def is_service_item(item_code=None, item_group=None, is_stock_item_flag=None):
    item_group = get_item_group(item_code, item_group)
    if is_stock_item_flag is not None:
        return bool(item_group and not is_engine_oil(item_group) and int(is_stock_item_flag) == 0)
    return bool(item_group and not is_engine_oil(item_group) and item_group in get_all_service_groups())


def is_stock_item(item_code=None, item_group=None, is_stock_item_flag=None):
    item_group = get_item_group(item_code, item_group)
    if is_stock_item_flag is not None:
        return bool(item_group and not is_engine_oil(item_group) and int(is_stock_item_flag) == 1)
    return bool(item_group and not is_engine_oil(item_group) and item_group in get_all_stock_groups())


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


def _build_discount_rule(item_type, default_discount, max_discount):
    default_discount = float(default_discount or 0)
    max_discount = float(max_discount or 0)

    discount_enabled = default_discount > 0 or max_discount > 0
    if not discount_enabled:
        return {
            "item_type": item_type,
            "max_discount": 0,
            "auto_apply": False,
            "auto_apply_value": 0,
            "discount_enabled": False,
        }

    final_max = max_discount if max_discount > 0 else default_discount
    auto_apply = default_discount > 0
    auto_apply_value = min(default_discount, final_max) if auto_apply else 0

    return {
        "item_type": item_type,
        "max_discount": float(final_max),
        "auto_apply": auto_apply,
        "auto_apply_value": float(auto_apply_value),
        "discount_enabled": True,
    }


@frappe.whitelist()
def get_max_discount(customer):
    if not customer:
        return {
            "customer_type": None,
            "invoice_max_discount": None,
            "condition": None,
            "other_condition": None,
        }

    customer_type = frappe.db.get_value("Customer", customer, "customer_type")
    if not customer_type:
        return {
            "customer_type": None,
            "invoice_max_discount": None,
            "condition": None,
            "other_condition": None,
        }

    meta = frappe.get_meta("POS Discount Rule")
    extra_fields = [f for f in ("condition", "other_condition") if meta.has_field(f)]
    fields = ["max_discount_"] + extra_fields
    rule = frappe.get_all(
        "POS Discount Rule",
        filters={"enabled": 1, "customer_type": customer_type},
        fields=fields,
        order_by="priority asc",
        limit=1,
    )

    invoice_max_discount = float(rule[0].max_discount_ or 0) if rule else None
    if invoice_max_discount is None:
        fallback = get_customer_discount_config(customer) or {}
        service_max = float(fallback.get("custom_custom_max_discount___service_items") or 0)
        stock_max = float(fallback.get("custom_custom_max_discount___stock_items") or 0)
        fallback_max = max(service_max, stock_max)
        invoice_max_discount = fallback_max if fallback_max > 0 else None

    return {
        "customer_type": customer_type,
        "invoice_max_discount": invoice_max_discount,
        "condition": (rule[0].condition if rule and hasattr(rule[0], "condition") else None),
        "other_condition": (
            rule[0].other_condition if rule and hasattr(rule[0], "other_condition") else None
        ),
    }


@frappe.whitelist()
def get_customer_item_discount(customer, item_code):

    result = {
        "max_discount": None,
        "auto_apply": False,
        "auto_apply_value": 0,
        "discount_enabled": False,
        "item_type": None,
        "message": None,
        "condition": None,
        "other_condition": None,
    }

    if not customer or not item_code:
        return result

    item_ctx = get_item_context(item_code=item_code)
    item_group = item_ctx.get("item_group")
    is_stock_item_flag = item_ctx.get("is_stock_item")
    if not item_group:
        return result

    if is_engine_oil(item_group):
        return {
            "item_type": "engine_oil",
            "max_discount": 0,
            "auto_apply": False,
            "auto_apply_value": 0,
            "discount_enabled": False,
            "message": "Engine Oil items are not eligible for discount",
            "condition": None,
            "other_condition": None,
        }

    is_service = is_service_item(
        item_group=item_group,
        is_stock_item_flag=is_stock_item_flag,
    )
    is_stock = is_stock_item(
        item_group=item_group,
        is_stock_item_flag=is_stock_item_flag,
    )

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

    rule = _build_discount_rule(item_type, default_max, manual_max)

    if rule["discount_enabled"]:
        if rule["auto_apply"]:
            rule["message"] = f"Auto-applied {rule['auto_apply_value']}%"
        else:
            rule["message"] = f"Manual discount allowed up to {rule['max_discount']}%"
    else:
        rule["message"] = "Discount disabled"

    rule["condition"] = None
    rule["other_condition"] = None
    return rule


@frappe.whitelist()
def validate_discount(customer, item_code, discount_percentage):

    discount_percentage = float(discount_percentage or 0)

    if discount_percentage <= 0:
        return {"is_valid": True}

    rules = get_customer_item_discount(customer, item_code)

    if rules.get("item_type") == "engine_oil":
        return {"is_valid": False, "message": "Discount not allowed for Engine Oil"}

    if not rules.get("discount_enabled", True):
        return {"is_valid": False, "message": "Discount not allowed for this item"}

    max_allowed = rules.get("max_discount")

    if max_allowed is not None:
        if discount_percentage > max_allowed:
            return {
                "is_valid": False,
                "message": f"Discount exceeds maximum allowed {max_allowed}%",
                "max_allowed": max_allowed,
            }

    return {"is_valid": True, "max_allowed": max_allowed}
