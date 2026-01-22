import frappe

# Service item groups (excluding Engine Oil)
SERVICE_ITEM_GROUPS = [
    "Services",
    "Car Wash Cleaning Items", 
    "Carwash",
    "Extra car care service",
    "Vehicle Under Coating"
]

# Stock item groups (excluding Engine Oil)
STOCK_ITEM_GROUPS = [
    "Products",
    "Carcare Products",
    "Consumable",
    "Mineral Oil"
]

def is_service_item(item_code=None, item_group=None):
   
    if not item_group and item_code:
        item_group = frappe.db.get_value("Item", item_code, "item_group")
    
    if not item_group:
        return False
    
    # Engine Oil is neither stock nor service for discount purposes
    if item_group.strip() == "Engine Oil":
        return False
    
    return item_group.strip() in SERVICE_ITEM_GROUPS


def is_stock_item(item_code=None, item_group=None):
   
    if not item_group and item_code:
        item_group = frappe.db.get_value("Item", item_code, "item_group")
    
    if not item_group:
        return False
    
    # Engine Oil is neither stock nor service for discount purposes
    if item_group.strip() == "Engine Oil":
        return False
    
    return item_group.strip() in STOCK_ITEM_GROUPS


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
        "max_discount": 0,
        "auto_apply": False,
        "auto_apply_value": 0,
        "source": None,
        "message": None,
        "item_type": None,
    }

    if not vehicle_no or not item_code:
        return result

    # Get item group
    item_group = frappe.db.get_value("Item", item_code, "item_group")
    
    if not item_group:
        return result
    
    # Engine Oil items get NO discount
    if item_group.strip() == "Engine Oil":
        result["message"] = "Engine Oil items are not eligible for discount"
        result["item_type"] = "engine_oil"
        return result

    # Determine item type
    is_service = is_service_item(item_group=item_group)
    is_stock = is_stock_item(item_group=item_group)
    
    if not is_service and not is_stock:
        result["message"] = f"Item group '{item_group}' is not configured for discounts"
        return result
    
    result["item_type"] = "service" if is_service else "stock"

    # Fetch vehicle discount settings
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
        default_max_discount = vehicle.custom_default_discount___service_items or 0
        manual_max_discount = vehicle.custom_max_discount___service_items or 0
        field_type = "service"
    else: 
        default_max_discount = vehicle.custom_default_discount___stock_items or 0
        manual_max_discount = vehicle.custom_max_discount___stock_items or 0
        field_type = "stock"

    if manual_max_discount and manual_max_discount > 0:
        return {
            "max_discount": float(manual_max_discount),
            "auto_apply": False,
            "auto_apply_value": 0,
            "source": f"vehicle_manual_max_{field_type}",
            "message": f"Manual entry allowed up to {manual_max_discount}% for {field_type} items",
            "item_type": result["item_type"],
        }

    if default_max_discount and default_max_discount > 0:
        return {
            "max_discount": float(default_max_discount),
            "auto_apply": True,
            "auto_apply_value": float(default_max_discount),
            "source": f"vehicle_default_max_{field_type}",
            "message": f"Auto-applied: {default_max_discount}% max discount for {field_type} items",
            "item_type": result["item_type"],
        }

    result["message"] = f"No discount configured for {field_type} items on this vehicle"
    return result


@frappe.whitelist()
def validate_discount(vehicle_no, item_code, discount_percentage):
    
    if not vehicle_no or not item_code:
        return {
            "is_valid": False,
            "message": "Vehicle or item information missing"
        }
    
    discount_percentage = float(discount_percentage or 0)
    
    if discount_percentage <= 0:
        return {
            "is_valid": True,
            "message": "No discount applied"
        }
    
    # Get discount rules
    rules = get_vehicle_item_discount(vehicle_no, item_code)
    
    # Engine Oil check
    if rules.get("item_type") == "engine_oil":
        return {
            "is_valid": False,
            "message": "Discount not allowed for Engine Oil items"
        }
    
    # Check if item type is configured
    if not rules.get("item_type"):
        return {
            "is_valid": False,
            "message": rules.get("message", "Item type not configured for discounts")
        }
    
    max_allowed = rules.get("max_discount", 0)
    
    # If no max discount configured, don't allow any discount
    if max_allowed <= 0:
        return {
            "is_valid": False,
            "message": f"No discount configured for this {rules.get('item_type')} item on vehicle {vehicle_no}"
        }
    
    # Validate against max
    if discount_percentage > max_allowed:
        return {
            "is_valid": False,
            "message": f"Discount {discount_percentage}% exceeds maximum allowed {max_allowed}% for {rules.get('item_type')} items",
            "max_allowed": max_allowed
        }
    
    return {
        "is_valid": True,
        "message": f"Discount {discount_percentage}% is valid (max: {max_allowed}%)",
        "max_allowed": max_allowed
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
        limit=1
    )
    
    if vehicles:
        return vehicles[0]
    
    return None


@frappe.whitelist()
def get_customer_by_vehicle(vehicle_no):

    if not vehicle_no:
        return None
    
    customer = frappe.db.get_value("Vehicle Master", vehicle_no, "customer")
    
    return customer