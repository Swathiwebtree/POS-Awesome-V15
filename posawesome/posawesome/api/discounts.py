import frappe

@frappe.whitelist()
def get_max_discount(customer):
    if not customer:
        return {
            "customer_type": None,
            "invoice_max_discount": 0,
        }

    customer_type = frappe.db.get_value(
        "Customer", customer, "customer_type"
    )

    if not customer_type:
        return {
            "customer_type": None,
            "invoice_max_discount": 0,
        }

    # Get highest priority rule for customer type
    rule = frappe.get_all(
        "POS Discount Rule",
        filters={
            "enabled": 1,
            "customer_type": customer_type,
        },
        fields=["max_discount_"],
        order_by="priority asc",
        limit=1,
    )

    return {
        "customer_type": customer_type,
        "invoice_max_discount": rule[0].max_discount_ if rule else 0,
    }
