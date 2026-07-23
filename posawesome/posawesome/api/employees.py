import frappe
from frappe import _


def _employee_has_field(fieldname):
    try:
        return bool(frappe.get_meta("Employee").has_field(fieldname))
    except Exception:
        return False


def _get_company_lift_employee_departments(company):
    if not company:
        return []

    try:
        departments = frappe.get_all(
            "Department",
            filters={"company": company},
            fields=["name", "department_name"],
        )
    except Exception:
        return []

    lift_departments = []
    for department in departments:
        department_label = str(
            getattr(department, "department_name", None) or getattr(department, "name", "") or ""
        ).strip()
        if not department_label:
            continue
        if department_label.lower().startswith("lift employee"):
            lift_departments.append(str(department.name))

    if lift_departments:
        return lift_departments

    return [
        str(department.name)
        for department in departments
        if "lift employee"
        in str(getattr(department, "department_name", None) or getattr(department, "name", "") or "").lower()
    ]


@frappe.whitelist()
def get_active_employees(company=None, search_term=None):
    """
    Fetch active employees for car wash service
    """
    filters = {"status": "Active", "docstatus": 0}
    or_filters = None

    if company:
        filters["company"] = company
        lift_departments = _get_company_lift_employee_departments(company)
        if lift_departments:
            filters["department"] = ["in", lift_departments]
        else:
            filters["department"] = ["like", "Lift Employee%"]

    has_custom_employee_id = _employee_has_field("custom_employee_id")

    if search_term:
        search_term = (search_term or "").strip()
        if len(search_term) < 3:
            return []
        like_term = f"%{search_term}%"
        or_filters = [
            ["Employee", "name", "like", like_term],
            ["Employee", "employee_name", "like", like_term],
        ]
        if has_custom_employee_id:
            or_filters.append(["Employee", "custom_employee_id", "like", like_term])

    get_all_kwargs = {
        "doctype": "Employee",
        "filters": filters,
        "or_filters": or_filters,
        "fields": ["name", "employee_name", "designation", "department", "branch", "image"],
        "order_by": "employee_name asc",
    }

    if has_custom_employee_id:
        get_all_kwargs["fields"].insert(2, "custom_employee_id")

    if search_term:
        get_all_kwargs["limit_page_length"] = 20

    employees = frappe.get_all(**get_all_kwargs)

    return [
        {
            "employee_id": str(employee.name or ""),
            "employee_name": str(employee.employee_name or employee.name or ""),
            "custom_employee_id": str(getattr(employee, "custom_employee_id", "") or ""),
            "designation": employee.designation,
            "department": employee.department,
            "branch": employee.branch,
            "image": employee.image,
            "display_label": (
                f"{getattr(employee, 'custom_employee_id', '') or employee.name} - "
                f"{employee.employee_name or employee.name}"
            ),
            "name": str(employee.name or ""),
        }
        for employee in employees
    ]


@frappe.whitelist()
def get_employee_details(employee_id):
    """
    Get detailed information about a specific employee
    """
    if not employee_id:
        return None

    employee = frappe.get_doc("Employee", employee_id)

    return {
        "name": str(employee.name or ""),
        "employee_name": str(employee.employee_name or employee.name or ""),
        "custom_employee_id": str(getattr(employee, "custom_employee_id", "") or ""),
        "designation": employee.designation,
        "department": employee.department,
        "branch": employee.branch,
        "image": employee.image,
        "status": employee.status,
    }
