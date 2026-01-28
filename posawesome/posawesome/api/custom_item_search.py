import frappe
from frappe import _
from erpnext.setup.utils import get_descendants_of

@frappe.whitelist()
def get_item_prices(item_code=None, item_name=None, item_group=None, price_list=None):
    """
    Get Item Prices with filtering by item_code, item_name, and item_group
    Uses Frappe's built-in get_descendants_of for hierarchical groups
    """
    
    conditions = []
    values = {}
    
    if item_code:
        conditions.append("ip.item_code LIKE %(item_code)s")
        values['item_code'] = f"%{item_code}%"
    
    if item_name:
        conditions.append("i.item_name LIKE %(item_name)s")
        values['item_name'] = f"%{item_name}%"
    
    if item_group:
        # Get all descendant groups (includes the parent itself)
        item_groups = get_descendants_of('Item Group', item_group)
        item_groups.append(item_group)
        
        conditions.append("i.item_group IN %(item_groups)s")
        values['item_groups'] = item_groups
    
    if price_list:
        conditions.append("ip.price_list = %(price_list)s")
        values['price_list'] = price_list
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    query = f"""
        SELECT 
            ip.name,
            ip.item_code,
            i.item_name,
            i.item_group,
            i.stock_uom,
            ip.price_list,
            ip.price_list_rate,
            ip.currency,
            ip.valid_from,
            ip.valid_upto,
            i.disabled,
            i.has_variants,
            i.image
        FROM `tabItem Price` ip
        INNER JOIN `tabItem` i ON ip.item_code = i.name
        WHERE {where_clause}
        ORDER BY i.item_name ASC
    """
    
    result = frappe.db.sql(query, values=values, as_dict=1)
    
    return result
