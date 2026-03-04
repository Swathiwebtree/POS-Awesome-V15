import frappe


@frappe.whitelist()
def get_last_mr_rate(item_code):
    result = frappe.db.sql(
        """
        SELECT mri.rate
        FROM `tabMaterial Request Item` mri
        JOIN `tabMaterial Request` mr ON mri.parent = mr.name
        WHERE mri.item_code = %s AND mr.docstatus = 1
        ORDER BY mr.creation DESC
        LIMIT 1
    """,
        item_code,
    )

    return result[0][0] if result else 0
