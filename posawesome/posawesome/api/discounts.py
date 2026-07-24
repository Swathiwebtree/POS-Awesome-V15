import frappe

_ITEM_GROUP_PARENT_CACHE = {}


def _normalize_item_group(item_group):
    return item_group.strip() if isinstance(item_group, str) and item_group.strip() else None


def _normalize_item_text(value):
    return value.strip().lower() if isinstance(value, str) and value.strip() else ""


def _looks_like_service(item_group=None, item_name=None, item_code=None):
    searchable = (
        _normalize_item_text(item_group),
        _normalize_item_text(item_name),
        _normalize_item_text(item_code),
    )
    keywords = ("carwash", "car wash", "bike wash", "bikewash", "wash", "service")

    for text in searchable:
        if not text:
            continue
        if any(keyword in text for keyword in keywords):
            return True

    return False


def get_item_context(item_code=None, item_group=None):
    if item_code:
        item_doc = frappe.db.get_value(
            "Item",
            item_code,
            ["item_group", "item_name", "is_stock_item", "custom_service_item"],
            as_dict=True,
        )
        if item_doc:
            item_group = _normalize_item_group(item_doc.item_group) or _normalize_item_group(item_group)
            return {
                "item_group": item_group,
                "item_name": item_doc.item_name,
                "is_stock_item": int(item_doc.is_stock_item or 0),
                "custom_service_item": int(item_doc.custom_service_item or 0),
            }

    return {
        "item_group": _normalize_item_group(item_group),
        "item_name": None,
        "is_stock_item": None,
        "custom_service_item": None,
    }


def is_engine_oil(item_group: str) -> bool:
    return bool(item_group and "engine oil" in item_group.lower())


def _get_item_group_parent(item_group):
    normalized_group = _normalize_item_group(item_group)
    if not normalized_group:
        return None

    cache_key = normalized_group.lower()
    if cache_key in _ITEM_GROUP_PARENT_CACHE:
        return _ITEM_GROUP_PARENT_CACHE[cache_key]

    parent_group = frappe.db.get_value("Item Group", normalized_group, "parent_item_group")
    parent_group = _normalize_item_group(parent_group)
    _ITEM_GROUP_PARENT_CACHE[cache_key] = parent_group
    return parent_group


def _get_item_group_lineage(item_group):
    lineage = []
    current_group = _normalize_item_group(item_group)
    seen_groups = set()

    while current_group:
        cache_key = current_group.lower()
        if cache_key in seen_groups:
            break

        lineage.append(current_group)
        seen_groups.add(cache_key)
        current_group = _get_item_group_parent(current_group)

    return lineage


def _classify_group_hierarchy(item_group):
    lineage = _get_item_group_lineage(item_group)

    for group in lineage:
        if is_engine_oil(group):
            return "engine_oil"

    for group in lineage:
        if group and group.strip().lower() == "services":
            return "service"

    return "stock"


def classify_item(item_code=None, item_group=None, is_stock_item_flag=None, custom_service_item=None):
    item_ctx = get_item_context(item_code=item_code, item_group=item_group)

    normalized_group = _normalize_item_group(item_ctx.get("item_group"))
    custom_service = item_ctx.get("custom_service_item")

    if custom_service_item is not None:
        custom_service = custom_service_item

    item_type = _classify_group_hierarchy(normalized_group)
    if item_type == "engine_oil":
        return {
            "item_type": "engine_oil",
            "item_group": normalized_group,
            "is_stock_item": 0,
            "custom_service_item": 0,
        }

    if int(custom_service or 0) == 1:
        return {
            "item_type": "service",
            "item_group": normalized_group,
            "is_stock_item": 0,
            "custom_service_item": 1,
        }

    if item_type == "service":
        return {
            "item_type": "service",
            "item_group": normalized_group,
            "is_stock_item": 0,
            "custom_service_item": 1,
        }

    if item_type == "stock":
        return {
            "item_type": "stock",
            "item_group": normalized_group,
            "is_stock_item": 1,
            "custom_service_item": 0,
        }

    return {
        "item_type": "stock",
        "item_group": normalized_group,
        "is_stock_item": 1,
        "custom_service_item": 0,
    }


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
    discount_editable = max_discount > 0
    auto_apply = default_discount > 0
    auto_apply_value = float(default_discount if auto_apply else 0)

    if not discount_enabled:
        return {
            "item_type": item_type,
            "default_discount": 0,
            "max_discount": 0,
            "auto_apply": False,
            "auto_apply_value": 0,
            "discount_enabled": False,
            "discount_editable": False,
            "configuration_warning": False,
            "message": "Discount disabled",
        }

    configuration_warning = bool(auto_apply and discount_editable and default_discount > max_discount)
    if configuration_warning:
        message = (
            f"Configuration warning: {item_type.title()} default discount {default_discount}% "
            f"exceeds the maximum allowed {max_discount}%."
        )
    elif auto_apply and not discount_editable:
        message = f"Auto-applied {auto_apply_value}% and locked"
    elif auto_apply:
        message = f"Auto-applied {auto_apply_value}%"
    else:
        message = f"Manual discount allowed up to {max_discount}%"

    return {
        "item_type": item_type,
        "default_discount": float(default_discount),
        "max_discount": float(max_discount),
        "auto_apply": auto_apply,
        "auto_apply_value": auto_apply_value,
        "discount_enabled": True,
        "discount_editable": discount_editable,
        "configuration_warning": configuration_warning,
        "message": message,
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
        "default_discount": 0,
        "max_discount": None,
        "auto_apply": False,
        "auto_apply_value": 0,
        "discount_enabled": False,
        "discount_editable": False,
        "item_type": None,
        "message": None,
        "condition": None,
        "other_condition": None,
        "configuration_warning": False,
    }

    if not customer or not item_code:
        return result

    item_ctx = get_item_context(item_code=item_code)
    classification = classify_item(
        item_code=item_code,
        item_group=item_ctx.get("item_group"),
        is_stock_item_flag=item_ctx.get("is_stock_item"),
        custom_service_item=item_ctx.get("custom_service_item"),
    )
    item_type = classification.get("item_type")

    if item_type == "engine_oil":
        return {
            "item_type": "engine_oil",
            "default_discount": 0,
            "max_discount": 0,
            "auto_apply": False,
            "auto_apply_value": 0,
            "discount_enabled": False,
            "discount_editable": False,
            "message": "Engine Oil items are not eligible for discount",
            "condition": None,
            "other_condition": None,
            "configuration_warning": False,
        }

    if item_type == "unknown":
        return {
            "item_type": "unknown",
            "default_discount": 0,
            "max_discount": 0,
            "auto_apply": False,
            "auto_apply_value": 0,
            "discount_enabled": False,
            "discount_editable": False,
            "message": "Unknown items are not eligible for service or stock discounts",
            "condition": None,
            "other_condition": None,
            "configuration_warning": False,
        }

    discounts = get_customer_discount_config(customer)
    if not discounts:
        result["item_type"] = item_type
        result["message"] = "Discount disabled"
        return result

    if item_type == "service":
        default_max = discounts.custom_custom_default_discount___service_items or 0
        manual_max = discounts.custom_custom_max_discount___service_items or 0
    else:
        default_max = discounts.custom_custom_default_discount___stock_items or 0
        manual_max = discounts.custom_custom_max_discount___stock_items or 0

    rule = _build_discount_rule(item_type, default_max, manual_max)

    if rule["discount_enabled"]:
        if rule["configuration_warning"]:
            rule["message"] = (
                f"Configuration warning: {item_type.title()} default discount {rule['default_discount']}% "
                f"exceeds the maximum allowed {rule['max_discount']}%."
            )
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

    if rules.get("item_type") == "unknown":
        return {"is_valid": False, "message": "Discount not allowed for unknown item type"}

    if not rules.get("discount_enabled", True):
        return {"is_valid": False, "message": "Discount not allowed for this item"}

    auto_apply_value = float(rules.get("auto_apply_value") or 0)
    discount_editable = bool(rules.get("discount_editable"))
    max_allowed = rules.get("max_discount")

    if not discount_editable:
        if rules.get("auto_apply") and abs(discount_percentage - auto_apply_value) <= 0.000001:
            return {"is_valid": True, "max_allowed": max_allowed}
        return {
            "is_valid": False,
            "message": "Discount field is locked for this item",
            "max_allowed": max_allowed,
        }

    if max_allowed is not None:
        if discount_percentage > max_allowed:
            return {
                "is_valid": False,
                "message": f"Discount exceeds maximum allowed {max_allowed}%",
                "max_allowed": max_allowed,
            }

    return {"is_valid": True, "max_allowed": max_allowed}
