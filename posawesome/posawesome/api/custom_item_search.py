import frappe
from frappe import _

@frappe.whitelist()
def get_item_prices(item_code=None, item_name=None, item_group=None, price_list=None,
                    limit_start=0, limit_page_length=20):
    """
    Get Item Prices with filtering
    """
    # Disable cache
    frappe.local.no_cache = True

    # Convert limit parameters
    limit_start = int(limit_start) if limit_start else 0
    limit_page_length = int(limit_page_length) if limit_page_length else 20

    # Clean inputs
    item_code = item_code.strip() if item_code else None
    item_name = item_name.strip() if item_name else None
    item_group = item_group.strip() if item_group else None
    price_list = price_list.strip() if price_list else None

    # Build conditions and values
    conditions = []
    values = {}

    if item_code:
        conditions.append("ip.item_code LIKE %(item_code)s")
        values['item_code'] = f"%{item_code}%"

    if item_name:
        conditions.append("i.item_name LIKE %(item_name)s")
        values['item_name'] = f"%{item_name}%"

    if item_group:
        item_groups = get_all_child_item_groups(item_group)
        if not item_groups:
            item_groups = [item_group]
        conditions.append("i.item_group IN %(item_groups)s")
        values['item_groups'] = tuple(item_groups)

    if price_list:
        conditions.append("ip.price_list = %(price_list)s")
        values['price_list'] = price_list

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    try:
        # Get total count
        count_query = f"""
            SELECT COUNT(DISTINCT ip.name) as total
            FROM ⁠ tabItem Price ⁠ ip
            INNER JOIN ⁠ tabItem ⁠ i ON ip.item_code = i.name
            WHERE {where_clause}
        """

        total_result = frappe.db.sql(count_query, values=values, as_dict=1)
        total = total_result[0].total if total_result else 0

        # Get data with pagination
        data_query = f"""
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
            FROM ⁠ tabItem Price ⁠ ip
            INNER JOIN ⁠ tabItem ⁠ i ON ip.item_code = i.name
            WHERE {where_clause}
            ORDER BY i.item_name ASC
            LIMIT {limit_start}, {limit_page_length}
        """

        data = frappe.db.sql(data_query, values=values, as_dict=1)

        return {
            "data": data,
            "total": total,
            "limit_start": limit_start,
            "limit_page_length": limit_page_length,
            "has_more": (limit_start + limit_page_length) < total
        }

    except Exception as e:
        frappe.log_error(f"Query failed: {str(e)}", "Item Price Query Error")
        frappe.log_error(f"Where clause: {where_clause}", "Item Price Query Error")
        frappe.log_error(f"Values: {values}", "Item Price Query Error")

        return {
            "data": [],
            "total": 0,
            "limit_start": limit_start,
            "limit_page_length": limit_page_length,
            "has_more": False
        }


def get_all_child_item_groups(parent_group):
    """
    Get all child item groups including parent
    """
    if not parent_group:
        return []

    try:
        parent = frappe.db.get_value("Item Group", parent_group, ["lft", "rgt"], as_dict=1)

        if parent and parent.lft and parent.rgt:
            groups = frappe.db.sql("""
                SELECT name
                FROM ⁠ tabItem Group ⁠
                WHERE lft >= %(lft)s AND rgt <= %(rgt)s
            """, {"lft": parent.lft, "rgt": parent.rgt}, as_list=1)

            return [g[0] for g in groups] if groups else [parent_group]
        else:
            return [parent_group]

    except Exception as e:
        frappe.log_error(f"Error getting item groups for {parent_group}: {str(e)}")
        return [parent_group]
