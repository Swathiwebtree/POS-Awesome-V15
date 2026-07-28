import frappe
from frappe import _


def _employee_has_field(fieldname):
    try:
        return bool(frappe.get_meta("Employee").has_field(fieldname))
    except Exception:
        return False


def _get_employee_doc_by_identifier(employee_id):
    if not employee_id:
        return None

    try:
        return frappe.get_doc("Employee", employee_id)
    except Exception:
        pass

    if _employee_has_field("custom_employee_id"):
        employee_name = frappe.db.get_value(
            "Employee",
            {"custom_employee_id": employee_id, "docstatus": 0},
            "name",
        )
        if employee_name:
            return frappe.get_doc("Employee", employee_name)

    return None


@frappe.whitelist()
def get_active_employees(company=None, search_term=None):
    """
    Fetch active employees for car wash service
    """
    search_term = (search_term or "").strip()
    if search_term and len(search_term) < 3:
        return []

    has_custom_employee_id = _employee_has_field("custom_employee_id")
    has_company_expense_flag = _employee_has_field("custom_is_company_expense")

    def _build_filters(scoped_company=None):
        filters = {"status": "Active", "docstatus": 0}
        if scoped_company:
            filters["company"] = scoped_company
        if has_company_expense_flag:
            filters["custom_is_company_expense"] = 0
        return filters

    def _build_query(scoped_company=None):
        or_filters = None
        if search_term:
            like_term = f"%{search_term}%"
            or_filters = [
                ["Employee", "name", "like", like_term],
                ["Employee", "employee_name", "like", like_term],
            ]
            if has_custom_employee_id:
                or_filters.append(["Employee", "custom_employee_id", "like", like_term])

        get_all_kwargs = {
            "doctype": "Employee",
            "filters": _build_filters(scoped_company),
            "or_filters": or_filters,
            "fields": ["name", "employee_name", "designation", "department", "branch", "image"],
            "order_by": "employee_name asc",
        }

        if has_custom_employee_id:
            get_all_kwargs["fields"].insert(2, "custom_employee_id")
        if search_term:
            get_all_kwargs["limit_page_length"] = 20
        return get_all_kwargs

    employees = frappe.get_all(**_build_query(company))

    if company and not employees:
        employees = frappe.get_all(**_build_query(None))

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

    employee = _get_employee_doc_by_identifier(employee_id)
    if not employee:
        return None

    custom_employee_id = str(getattr(employee, "custom_employee_id", "") or "")
    display_label = f"{custom_employee_id or employee.name} - {employee.employee_name or employee.name}"

    return {
        "name": str(employee.name or ""),
        "employee_id": str(employee.name or ""),
        "employee_name": str(employee.employee_name or employee.name or ""),
        "custom_employee_id": custom_employee_id,
        "designation": employee.designation,
        "department": employee.department,
        "branch": employee.branch,
        "image": employee.image,
        "status": employee.status,
        "display_label": display_label,
    }
