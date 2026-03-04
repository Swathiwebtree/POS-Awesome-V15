import frappe
from frappe.model.naming import make_autoname


def set_job_order_number(doc, method=None):
    #  Only run if field exists
    if not hasattr(doc, "custom_job_order_number"):
        return

    if not doc.get("custom_job_order_number"):
        doc.custom_job_order_number = make_autoname("JOB-.YYYY.-.#####")
