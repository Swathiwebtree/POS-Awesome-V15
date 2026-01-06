import frappe
from frappe.utils import flt, nowdate, nowtime, add_days


def on_invoice_submit(doc, method):
    # Basic guards
    if not doc.customer or not doc.loyalty_program:
        return

    if doc.is_return or flt(doc.net_total) <= 0:
        return

    program = frappe.get_doc("Loyalty Program", doc.loyalty_program)

    
    collection_factor = 0

    for rule in program.collection_rules:
        if flt(doc.net_total) >= flt(rule.min_spent):
            collection_factor = flt(rule.collection_factor)
            break

    if not collection_factor:
        # No eligible rule → no points
        return

    points = flt(doc.net_total) / collection_factor

    if points <= 0:
        return

    entry = frappe.get_doc({
        "doctype": "Loyalty Point Entry",
        "customer": doc.customer,
        "loyalty_program": doc.loyalty_program,
        "company": doc.company,
        "loyalty_points": points,
        "purchase_amount": doc.net_total,
        "expiry_date": add_days(
            nowdate(),
            program.expiry_duration or 365
        ),
        "posting_date": nowdate(),
        "posting_time": nowtime(),
        "reference_doctype": "Sales Invoice",
        "reference_name": doc.name,
    })

    entry.insert(ignore_permissions=True)
    entry.submit()
