import frappe
from frappe import _

@frappe.whitelist()
def get_active_employees(company=None):
    """
    Fetch active employees for car wash service
    """
    filters = {
        "status": "Active",
        "docstatus": 0
    }
    
    if company:
        filters["company"] = company
    
    employees = frappe.get_all(
        "Employee",
        filters=filters,
        fields=[
            "name",
            "employee_name",
            "designation",
            "department",
            "branch",
            "image"
        ],
        order_by="employee_name asc"
    )
    
    return employees

@frappe.whitelist()
def get_employee_details(employee_id):
    """
    Get detailed information about a specific employee
    """
    if not employee_id:
        return None
    
    employee = frappe.get_doc("Employee", employee_id)
    
    return {
        "name": employee.name,
        "employee_name": employee.employee_name,
        "designation": employee.designation,
        "department": employee.department,
        "branch": employee.branch,
        "image": employee.image,
        "status": employee.status
    }