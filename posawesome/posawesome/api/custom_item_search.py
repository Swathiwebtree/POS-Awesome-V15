import frappe
from frappe import _

@frappe.whitelist()
def get_item_prices(item_code=None, item_name=None, item_group=None, price_list=None):
    """
    Get Item Prices with filtering by item_code, item_name, and item_group
    
    Args:
        item_code: Filter by item code (supports wildcard %)
        item_name: Filter by item name (supports wildcard %)
        item_group: Filter by item group (exact match or comma-separated list)
        price_list: Filter by specific price list
    
    Returns:
        List of item prices with item details
    """
    
    conditions = []
    values = {}
    
    # Build the query conditions
    if item_code:
        conditions.append("ip.item_code LIKE %(item_code)s")
        values['item_code'] = f"%{item_code}%"
    
    if item_name:
        conditions.append("i.item_name LIKE %(item_name)s")
        values['item_name'] = f"%{item_name}%"
    
    if item_group:
        # Support multiple item groups separated by comma
        if ',' in item_group:
            groups = [g.strip() for g in item_group.split(',')]
            conditions.append("i.item_group IN %(item_groups)s")
            values['item_groups'] = groups
        else:
            conditions.append("i.item_group = %(item_group)s")
            values['item_group'] = item_group
    
    if price_list:
        conditions.append("ip.price_list = %(price_list)s")
        values['price_list'] = price_list
    
    # Build WHERE clause
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    # Execute query
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
