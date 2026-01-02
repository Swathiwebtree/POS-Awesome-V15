import frappe
from frappe.model.naming import make_autoname


def set_job_order_number(doc, method=None):
    if not doc.custom_job_order_number:
        doc.custom_job_order_number = make_autoname("JOB-.YYYY.-.#####")
