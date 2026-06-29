import frappe
from frappe.utils import flt, nowdate, nowtime, add_days


def on_invoice_submit(doc, method):
    # Basic guards
    if not doc.customer:
        return

    if doc.is_return or flt(doc.net_total) <= 0:
        return

    loyalty_program = doc.loyalty_program or frappe.db.get_value("Customer", doc.customer, "loyalty_program")
    if not loyalty_program:
        return

    program = frappe.get_doc("Loyalty Program", loyalty_program)

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

    def _create_entry(loyalty_points, purchase_amount):
        entry = frappe.get_doc(
            {
                "doctype": "Loyalty Point Entry",
                "customer": doc.customer,
                "loyalty_program": loyalty_program,
                "company": doc.company,
                "loyalty_points": loyalty_points,
                "purchase_amount": purchase_amount,
                "expiry_date": add_days(nowdate(), program.expiry_duration or 365),
                "posting_date": nowdate(),
                "posting_time": nowtime(),
                "reference_doctype": "Sales Invoice",
                "reference_name": doc.name,
            }
        )
        entry.insert(ignore_permissions=True)
        entry.submit()

    redeemed_points = flt(doc.get("redeemed_loyalty_points") or doc.get("redeem_loyalty_points") or 0)
    if redeemed_points <= 0:
        loyalty_amount = flt(doc.get("loyalty_amount") or doc.get("loyalty_discount_amount") or 0)
        if loyalty_amount > 0 and loyalty_program:
            redemption_factor = flt(
                frappe.db.get_value("Loyalty Program", loyalty_program, "conversion_factor")
            )
            if redemption_factor > 0:
                redeemed_points = loyalty_amount / redemption_factor

    if redeemed_points > 0:
        _create_entry(-redeemed_points, flt(doc.get("loyalty_amount") or doc.get("loyalty_discount_amount") or 0))
        return

    _create_entry(points, doc.net_total)


def validate_loyalty_redeem(doc, method=None):
    if flt(doc.loyalty_points) >= 0:
        return

    current_points = frappe.db.sql(
        """
        SELECT IFNULL(SUM(loyalty_points), 0)
        FROM `tabLoyalty Point Entry`
        WHERE customer=%s
          AND loyalty_program=%s
          AND company=%s
          AND docstatus=1
          AND name!=%s
        """,
        (doc.customer, doc.loyalty_program, doc.company, doc.name),
    )[0][0]

    if abs(doc.loyalty_points) > flt(current_points):
        frappe.throw(
            _("Insufficient loyalty points. Available: {0}, Tried: {1}").format(
                current_points, abs(doc.loyalty_points)
            ),
            frappe.ValidationError,
        )
