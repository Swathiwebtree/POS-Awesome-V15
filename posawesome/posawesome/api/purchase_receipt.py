import frappe

def create_stock_entry_from_pr(doc, method):

    # prevent duplicate creation
    if frappe.db.exists("Stock Entry", {"purchase_receipt": doc.name}):
        return

    se = frappe.new_doc("Stock Entry")
    se.stock_entry_type = "Material Receipt"
    se.company = doc.company
    se.purchase_receipt = doc.name  # custom link

    for item in doc.items:

        qty = item.received_qty or item.qty

        # choose correct rate source (valuation_rate preferred)
        rate = item.valuation_rate or item.rate or 0

        se.append("items", {
            "item_code": item.item_code,
            "qty": item.qty,
            "uom": item.uom,
            "t_warehouse": item.warehouse,
            "basic_rate": item.base_rate or item.rate,
            "basic_amount": item.base_amount, 
            "amount": item.amount,             
            
        })

    se.set_posting_date = 1
    se.posting_date = doc.posting_date
    se.posting_time = doc.posting_time

    se.save(ignore_permissions=True)
    se.submit()

    frappe.msgprint(f"Stock Entry <b>{se.name}</b> created from Purchase Receipt {doc.name}")
