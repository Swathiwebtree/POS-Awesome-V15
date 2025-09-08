import frappe
from frappe import _

@frappe.whitelist()
def get_work_orders():
    """Fetch Work Orders for POS screen."""
    work_orders = frappe.get_all(
        "Work Order",
        fields=[
            "name as work_order_no",
            "transaction_date as date",
            "production_item as model",
            "fg_warehouse as vehicle_no",
            "customer as mobile_no",
            "status",
        ],
        order_by="creation desc",
        limit_page_length=20
    )
    return work_orders

# import frappe
# from frappe import _

# @frappe.whitelist(allow_guest=False)
# def validate_cashier(code: str = None):
#     """Temporary: Bypass cashier code for testing."""
#     # Return a dummy cashier without checking the code
#     return {
#         "status": "success",
#         "cashier": {
#             "name": "Test Cashier",
#             "employee_name": "Test Employee",
#             "user": frappe.session.user,
#             "terminal": "Default Terminal",
#             "role": "Cashier"
#         }
#     }

# # @frappe.whitelist(allow_guest=False)
# # def validate_cashier(code: str = None):
# #     """Validate cashier login code and return cashier info if valid."""
# #     if not code:
# #         frappe.throw(_("Missing cashier code"))

# #     cashier = frappe.get_all(
# #         "Cashier",
# #         filters={"custom_cashier_code_": code, "enabled": 1},
# #         fields=["name", "employee_name", "user", "terminal", "role", "custom_cashier_code_"],
# #         limit_page_length=1
# #     )

# #     if not cashier:
# #         return {"status": "error", "message": _("Invalid cashier code")}

# #     c = cashier[0]

# #     # Optional: remove custom_cashier_code_ before returning
# #     c.pop("custom_cashier_code_", None)

# #     # Log the login
# #     try:
# #         frappe.get_doc({
# #             "doctype": "Cashier Login Log",
# #             "cashier": c["name"],
# #             "terminal": c.get("terminal"),
# #             "status": "Success"
# #         }).insert(ignore_permissions=True)
# #     except Exception:
# #         frappe.log_error(frappe.get_traceback(), "Cashier login log failed")

# #     return {"status": "success", "cashier": c}
