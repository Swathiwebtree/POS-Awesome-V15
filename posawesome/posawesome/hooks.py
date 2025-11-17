doc_events = {
     "Sales Invoice": {
        "validate": "posawesome.posawesome.api.hooks_sales_invoice.validate_sales_invoice"
    },
    "POS Invoice": {
        "validate": "posawesome.posawesome.api.hooks_sales_invoice.validate_sales_invoice"
    },
    "Customer": {
        "validate": "posawesome.posawesome.api.customers.set_customer_info",
    },
    "Payment Entry": {"on_cancel": "posawesome.posawesome.api.payment_entry.on_payment_entry_cancel"},
}
