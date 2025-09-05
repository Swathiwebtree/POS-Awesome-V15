import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    custom_fields = {
        "POS Settings": [
            dict(
                fieldname="custom_cashier_code_",
                label="Cashier Code",
                fieldtype="Data",
                insert_after="company",
                reqd=1
            )
        ]
    }
    create_custom_fields(custom_fields)
