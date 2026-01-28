import frappe
from frappe import _
from erpnext.setup.utils import get_descendants_of

@frappe.whitelist()
def get_item_prices(item_code=None, item_name=None, item_group=None, price_list=None, 
                    limit_start=0, limit_page_length=20):
    """
    Get Item Prices with filtering by item_code, item_name, and item_group
    Uses Frappe's built-in get_descendants_of for hierarchical groups
    
    Args:
        item_code: Filter by item code (supports wildcard %)
        item_name: Filter by item name (supports wildcard %)
        item_group: Filter by item group (includes child groups if is_group=1)
        price_list: Filter by specific price list
        limit_start: Offset for pagination (default: 0)
        limit_page_length: Number of records to return (default: 20)
    
    Returns:
        Dict with data, total count, and pagination info
    """
    
    conditions = []
    values = {
        'limit_start': int(limit_start),
        'limit_page_length': int(limit_page_length)
    }
    
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
    
    # Get total count (for pagination info)
    count_query = f"""
        SELECT COUNT(*) as total
        FROM `tabItem Price` ip
        INNER JOIN `tabItem` i ON ip.item_code = i.name
        WHERE {where_clause}
    """
    
    total = frappe.db.sql(count_query, values=values, as_dict=1)[0].total
    
    # Get paginated data
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
        LIMIT %(limit_start)s, %(limit_page_length)s
    """
    
    data = frappe.db.sql(query, values=values, as_dict=1)
    
    return {
        'data': data,
        'total': total,
        'limit_start': int(limit_start),
        'limit_page_length': int(limit_page_length),
        'has_more': (int(limit_start) + int(limit_page_length)) < total
    }
