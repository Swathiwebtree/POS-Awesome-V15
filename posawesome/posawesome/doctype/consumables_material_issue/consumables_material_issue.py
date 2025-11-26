import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, nowtime


class ConsumablesMaterialIssue(Document):
    pass


def create_stock_entry(doc, method):

    # safety check for child table
    if not doc.material_issue or len(doc.material_issue) == 0:
        frappe.throw("No consumable items found to create Stock Entry.")

    # create new Stock Entry
    se = frappe.new_doc("Stock Entry")
    se.stock_entry_type = "Material Issue"

    # company (required)
    if getattr(doc, "company", None):
        se.company = doc.company
    else:
        se.company = frappe.defaults.get_user_default("company")

    # posting date and time
    se.posting_date = nowdate()
    se.posting_time = nowtime()

    # loop through consumable items
    for row in doc.material_issue:
        item = se.append(
            "items",
            {
                "s_warehouse": row.source_warehouse,
                "item_code": row.item,
                "qty": row.quantity,
                "uom": frappe.get_value("Item", row.item, "stock_uom"),
                "cost_center": getattr(doc, "cost_center", None),
            },
        )

        # allow zero valuation rate for consumables
        item.allow_zero_valuation_rate = 1

    # save and submit
    se.save(ignore_permissions=True)
    se.submit()

    # link back to parent
    if hasattr(doc, "stock_entry_reference"):
        doc.db_set("stock_entry_reference", se.name)

    frappe.msgprint(f"Stock Entry <b>{se.name}</b> created and submitted.")
