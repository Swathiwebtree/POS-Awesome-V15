import frappe
from frappe import _


@frappe.whitelist()
def get_item_prices(
    item_code=None, item_name=None, item_group=None, price_list=None, limit_start=0, limit_page_length=20
):
    """
    Get Item Prices with filtering - SIMPLIFIED VERSION
    """

    try:
        # Parse parameters safely
        limit_start = int(limit_start) if str(limit_start).isdigit() else 0
        limit_page_length = int(limit_page_length) if str(limit_page_length).isdigit() else 20

        # Clean inputs
        item_code = frappe.as_unicode(item_code).strip() if item_code else ""
        item_name = frappe.as_unicode(item_name).strip() if item_name else ""
        item_group = frappe.as_unicode(item_group).strip() if item_group else ""
        price_list = frappe.as_unicode(price_list).strip() if price_list else ""

        # Build WHERE conditions
        where_conditions = []
        params = []

        if item_code:
            where_conditions.append("ip.item_code LIKE %s")
            params.append(f"%{item_code}%")

        if item_name:
            where_conditions.append("i.item_name LIKE %s")
            params.append(f"%{item_name}%")

        if item_group:
            item_groups = get_all_child_item_groups_simple(item_group)
            if item_groups:
                placeholders = ", ".join(["%s"] * len(item_groups))
                where_conditions.append(f"i.item_group IN ({placeholders})")
                params.extend(item_groups)

        if price_list:
            where_conditions.append("ip.price_list = %s")
            params.append(price_list)

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # Get total count
        count_query = f"""
            SELECT COUNT(DISTINCT ip.name) as total
            FROM `tabItem Price` ip
            INNER JOIN `tabItem` i ON ip.item_code = i.name
            WHERE {where_clause}
        """

        total_result = frappe.db.sql(count_query, tuple(params))
        total = total_result[0][0] if total_result else 0

        # Get data
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
            FROM `tabItem Price` ip
            INNER JOIN `tabItem` i ON ip.item_code = i.name
            WHERE {where_clause}
            ORDER BY i.item_name ASC
            LIMIT %s, %s
        """

        # Add limit parameters
        params.extend([limit_start, limit_page_length])

        data = frappe.db.sql(data_query, tuple(params), as_dict=1)

        return {
            "data": data,
            "total": total,
            "limit_start": limit_start,
            "limit_page_length": limit_page_length,
            "has_more": (limit_start + limit_page_length) < total,
        }

    except Exception as e:
        frappe.log_error(f"get_item_prices error: {str(e)}", "get_item_prices")
        return {
            "data": [],
            "total": 0,
            "limit_start": limit_start,
            "limit_page_length": limit_page_length,
            "has_more": False,
        }


def get_all_child_item_groups_simple(parent_group):
    """
    Simplified version without any caching
    """
    if not parent_group:
        return []

    try:
        # Get parent group details
        groups = frappe.db.sql(
            """
            SELECT child.name
            FROM `tabItem Group` parent
            JOIN `tabItem Group` child 
            ON child.lft >= parent.lft AND child.rgt <= parent.rgt
            WHERE parent.name = %s
        """,
            parent_group,
            as_list=1,
        )

        return [g[0] for g in groups] if groups else [parent_group]

    except:
        return [parent_group]
