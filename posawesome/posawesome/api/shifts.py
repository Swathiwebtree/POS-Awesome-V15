# -*- coding: utf-8 -*-
# Copyright (c) 2020, Youssef Restom and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from warnings import filters
from frappe.utils import now
from frappe.utils.data import flt
import json
import frappe
from frappe.utils import nowdate
from frappe import _
from .utilities import get_version


@frappe.whitelist()
def get_opening_dialog_data():
    user = frappe.session.user

    # Get POS Profile Users
    pos_profile_users = frappe.db.get_all("POS Profile User", filters={"user": user}, pluck="parent")

    # Get POS Profiles
    pos_profiles_data = frappe.db.get_all(
        "POS Profile",
        filters={"name": ["in", pos_profile_users], "disabled": 0},
        fields=["name", "company", "currency"],
    )

    # Get companies
    companies = []
    pos_profiles_list = []
    for profile in pos_profiles_data:
        pos_profiles_list.append(profile.name)
        if profile.company not in companies:
            companies.append(profile.company)

    # Get payment methods
    payments_method = frappe.db.get_all(
        "POS Payment Method", filters={"parent": ["in", pos_profiles_list]}, fields=["*"]
    )

    # Get or create opening entry
    pos_opening_entry = get_or_create_opening_entry(user, pos_profiles_data, pos_profiles_list)

    return {
        "pos_profiles_data": pos_profiles_data,
        "companies": [{"name": c} for c in companies],
        "payments_method": payments_method,
        "pos_opening_entry": pos_opening_entry,
    }


def get_or_create_opening_entry(user, pos_profiles_data, pos_profiles_list):
    """Check for existing open entry or create new one"""

    if not pos_profiles_list:
        return None

    # Check for existing open entry
    open_entry = frappe.db.get_all(
        "POS Opening Entry",
        filters={"user": user, "pos_profile": ["in", pos_profiles_list], "docstatus": 1, "status": "Open"},
        fields=["name", "pos_profile", "company", "period_start_date"],
        order_by="creation desc",
        limit=1,
    )

    if open_entry:
        # Check if there's a closing entry for this
        closing_exists = frappe.db.exists(
            "POS Closing Entry", {"pos_opening_entry": open_entry[0].name, "docstatus": 1}
        )

        if not closing_exists:
            return open_entry[0]

    # Create new opening entry
    first_profile = pos_profiles_data[0]

    opening_entry = frappe.new_doc("POS Opening Entry")
    opening_entry.user = user
    opening_entry.pos_profile = first_profile.name
    opening_entry.company = first_profile.company
    opening_entry.posting_date = frappe.utils.today()
    opening_entry.period_start_date = frappe.utils.now_datetime()

    # Get payment modes for this profile
    payments = frappe.db.get_all(
        "POS Payment Method",
        filters={"parent": first_profile.name},
        fields=["mode_of_payment"],
        order_by="idx",
    )

    # Add balance details with 0 opening amount
    for payment in payments:
        opening_entry.append(
            "balance_details", {"mode_of_payment": payment.mode_of_payment, "opening_amount": 0}
        )

    opening_entry.insert()
    opening_entry.submit()

    return {
        "name": opening_entry.name,
        "pos_profile": opening_entry.pos_profile,
        "company": opening_entry.company,
        "period_start_date": opening_entry.period_start_date,
    }


@frappe.whitelist()
def create_opening_voucher(pos_profile, company, balance_details):
    balance_details = json.loads(balance_details)

    new_pos_opening = frappe.get_doc(
        {
            "doctype": "POS Opening Shift",
            "period_start_date": frappe.utils.get_datetime(),
            "posting_date": frappe.utils.getdate(),
            "user": frappe.session.user,
            "pos_profile": pos_profile,
            "company": company,
            "docstatus": 1,
        }
    )
    new_pos_opening.set("balance_details", balance_details)
    new_pos_opening.insert(ignore_permissions=True)

    data = {}
    data["pos_opening_shift"] = new_pos_opening.as_dict()
    update_opening_shift_data(data, new_pos_opening.pos_profile)
    return data


@frappe.whitelist()
def check_opening_shift(user):

    # Resolve user's default company (if set) to scope open shift lookup

    user_company = get_user_company(user)
    filters = {"pos_closing_shift": ["in", ["", None]], "docstatus": 1, "status": "Open"}
    if user_company:

        # If company is known, filter by company only (user may differ)

        filters["company"] = user_company
    else:
        filters["user"] = user

    open_vouchers = frappe.db.get_all(
        "POS Opening Shift",
        filters=filters,
        fields=["name", "pos_profile"],
        order_by="period_start_date desc",
    )
    data = ""
    if len(open_vouchers) > 0:
        data = {}
        data["pos_opening_shift"] = frappe.get_doc("POS Opening Shift", open_vouchers[0]["name"])
        update_opening_shift_data(data, open_vouchers[0]["pos_profile"])
    return data


def get_user_company(user):
    company = frappe.db.get_value("User Permission", {"user": user, "allow": "Company"}, "for_value")

    if company:
        return company

    return frappe.defaults.get_user_default("Company", user=user) or frappe.defaults.get_user_default(
        "company", user=user
    )


def update_opening_shift_data(data, pos_profile):
    data["pos_profile"] = frappe.get_doc("POS Profile", pos_profile)
    if data["pos_profile"].get("posa_language"):
        frappe.local.lang = data["pos_profile"].posa_language
    data["company"] = frappe.get_doc("Company", data["pos_profile"].company)
    allow_negative_stock = frappe.get_value("Stock Settings", None, "allow_negative_stock")
    data["stock_settings"] = {}
    data["stock_settings"].update({"allow_negative_stock": allow_negative_stock})


@frappe.whitelist()
def close_shift():
    try:
        user = frappe.session.user
        user_company = get_user_company(user)

        filters = {
            "pos_closing_shift": ["in", ["", None]],
            "docstatus": 1,
            "status": "Open",
        }

        if user_company:
            filters["company"] = user_company
        else:
            filters["user"] = user

        open_shifts = frappe.get_all(
            "POS Opening Shift",
            filters=filters,
            fields=["name"],
            limit_page_length=1,
            order_by="period_start_date desc",
        )

        if not open_shifts:
            return {"success": False, "message": _("No open shift found.")}

        shift = frappe.get_doc("POS Opening Shift", open_shifts[0]["name"])

        shift.pos_closing_shift = now()
        shift.status = "Closed"
        shift.save(ignore_permissions=True)

        return {"success": True, "message": _("Shift closed successfully")}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "posawesome.close_shift")
        return {"success": False, "message": _("Failed to close shift: {0}").format(str(e))}


def get_shift_payment_mode_totals(shift_start, pos_profile):
    """
    Returns payment totals per mode_of_payment
    """
    return frappe.db.sql(
        """
        SELECT
            sip.mode_of_payment,
            SUM(sip.amount) AS total_amount
        FROM `tabSales Invoice Payment` sip
        INNER JOIN `tabSales Invoice` si
            ON si.name = sip.parent
        WHERE
            si.docstatus = 1
            AND si.pos_profile = %s
            AND si.creation >= %s
        GROUP BY sip.mode_of_payment
    """,
        (pos_profile, shift_start),
        as_dict=True,
    )


def get_shift_payment_entry_totals(shift_start, pos_profile):
    """
    Returns totals per mode_of_payment from Payment Entry
    """
    return frappe.db.sql(
        """
        SELECT
            pe.mode_of_payment,
            SUM(pe.paid_amount) AS total_amount
        FROM `tabPayment Entry` pe
        INNER JOIN `tabPayment Entry Reference` per
            ON per.parent = pe.name
        INNER JOIN `tabSales Invoice` si
            ON si.name = per.reference_name
        WHERE
            pe.docstatus = 1
            AND pe.payment_type = 'Receive'
            AND si.pos_profile = %s
            AND pe.creation >= %s
        GROUP BY pe.mode_of_payment
    """,
        (pos_profile, shift_start),
        as_dict=True,
    )


@frappe.whitelist()
def get_closing_dialog_data():
    data = {}

    # -------------------------------------------------------
    # 1. POS Profiles
    # -------------------------------------------------------
    pos_profiles_data = frappe.db.sql(
        """
        SELECT DISTINCT p.name, p.company
        FROM `tabPOS Profile` p
        INNER JOIN `tabPOS Profile User` u ON u.parent = p.name
        WHERE p.disabled = 0 AND u.user = %s
        ORDER BY p.name
    """,
        frappe.session.user,
        as_dict=True,
    )

    if not pos_profiles_data:
        return {
            "pos_profiles_data": [],
            "companies": [],
            "payments_method": [],
            "payment_reconciliation": [],
        }

    data["pos_profiles_data"] = pos_profiles_data

    # -------------------------------------------------------
    # 2. Companies
    # -------------------------------------------------------
    companies = list({p.company for p in pos_profiles_data if p.company})
    data["companies"] = [{"name": c} for c in companies]

    pos_profiles_list = [p.name for p in pos_profiles_data]

    # -------------------------------------------------------
    # 3. Payment methods from POS Profile
    # -------------------------------------------------------
    payment_method_table = "POS Payment Method" if get_version() == 13 else "Sales Invoice Payment"

    payments = frappe.get_list(
        payment_method_table,
        filters={"parent": ["in", pos_profiles_list]},
        fields=["*"],
        limit_page_length=0,
        order_by="parent",
        ignore_permissions=True,
    )

    for pm in payments:
        currency = frappe.get_cached_value("POS Profile", pm.parent, "currency")
        if not currency:
            company = frappe.get_cached_value("POS Profile", pm.parent, "company")
            currency = frappe.get_cached_value("Company", company, "default_currency")
        pm["currency"] = currency

    data["payments_method"] = payments

    # -------------------------------------------------------
    # 4. Open POS Shift
    # -------------------------------------------------------
    user = frappe.session.user
    user_company = get_user_company(user)

    filters = {
        "pos_closing_shift": ["in", ["", None]],
        "docstatus": 1,
        "status": "Open",
    }

    if user_company:
        filters["company"] = user_company
    else:
        filters["user"] = user

    open_shift = frappe.get_all(
        "POS Opening Shift",
        filters=filters,
        fields=["name", "period_start_date", "pos_profile"],
        order_by="period_start_date desc",
        limit_page_length=1,
    )

    if not open_shift:
        data["payment_reconciliation"] = []
        return data

    shift_start = open_shift[0].period_start_date
    pos_profile = open_shift[0].pos_profile

    # -------------------------------------------------------
    # 5A. POS CASH payments (Sales Invoice Payment)
    # -------------------------------------------------------
    pos_invoice_payments = get_shift_payment_mode_totals(shift_start, pos_profile)

    pos_invoice_totals = {p.mode_of_payment: flt(p.total_amount) for p in pos_invoice_payments}

    # -------------------------------------------------------
    # 5B. NON-CASH payments (Payment Entry)
    # -------------------------------------------------------
    payment_entry_payments = frappe.db.sql(
        """
        SELECT
            pe.mode_of_payment,
            SUM(pe.paid_amount) AS total_amount
        FROM `tabPayment Entry` pe
        INNER JOIN `tabPayment Entry Reference` per
            ON per.parent = pe.name
        INNER JOIN `tabSales Invoice` si
            ON si.name = per.reference_name
        WHERE
            pe.docstatus = 1
            AND pe.payment_type = 'Receive'
            AND si.pos_profile = %s
            AND pe.creation >= %s
        GROUP BY pe.mode_of_payment
    """,
        (pos_profile, shift_start),
        as_dict=True,
    )

    payment_entry_totals = {p.mode_of_payment: flt(p.total_amount) for p in payment_entry_payments}

    # -------------------------------------------------------
    # 5C. MERGE ALL totals
    # -------------------------------------------------------
    all_totals = {}

    for mode, amt in pos_invoice_totals.items():
        all_totals[mode] = all_totals.get(mode, 0) + amt

    for mode, amt in payment_entry_totals.items():
        all_totals[mode] = all_totals.get(mode, 0) + amt

    # -------------------------------------------------------
    # 5D. Credit-only fallback (NO payments)
    # -------------------------------------------------------
    sales_total = frappe.db.sql(
        """
        SELECT SUM(si.grand_total) AS total
        FROM `tabSales Invoice` si
        WHERE
            si.docstatus = 1
            AND si.pos_profile = %s
            AND si.creation >= %s
    """,
        (pos_profile, shift_start),
        as_dict=True,
    )

    sales_total = flt(sales_total[0].total) if sales_total else 0

    # -------------------------------------------------------
    # 6. FINAL reconciliation logic
    # -------------------------------------------------------
    reconciliation = []

    for pm in payments:
        mode = pm.mode_of_payment

        if all_totals:
            expected = all_totals.get(mode, 0)
        else:
            # Credit sale → Cash only
            expected = sales_total if mode == "Cash" else 0

        reconciliation.append(
            {
                "mode_of_payment": mode,
                "opening_amount": 0,
                "expected_amount": expected,
                "closing_amount": expected,
                "currency": pm.currency,
            }
        )

    data["payment_reconciliation"] = reconciliation
    return data


@frappe.whitelist()
def close_shift_with_reconciliation(balance_details=None):
    import json
    from frappe.utils import now

    try:
        user = frappe.session.user
        user_company = get_user_company(user)

        if isinstance(balance_details, str):
            balance_details = json.loads(balance_details)

        filters = {
            "pos_closing_shift": ["in", ["", None]],
            "docstatus": 1,
            "status": "Open",
        }

        if user_company:
            filters["company"] = user_company
        else:
            filters["user"] = user

        open_shifts = frappe.get_all(
            "POS Opening Shift",
            filters=filters,
            fields=["name"],
            limit_page_length=1,
            order_by="period_start_date desc",
        )

        if not open_shifts:
            return {"success": False, "message": _("No open shift found.")}

        shift = frappe.get_doc("POS Opening Shift", open_shifts[0]["name"])

        # Save reconciliation
        try:
            shift.closing_reconciliation = json.dumps(balance_details or [])
        except Exception:
            shift.add_comment(
                "Comment",
                _("Closing reconciliation: {0}").format(json.dumps(balance_details or [])),
            )

        shift.pos_closing_shift = now()
        shift.status = "Closed"
        shift.save(ignore_permissions=True)

        return {"success": True, "message": _("Shift closed successfully")}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "posawesome.close_shift_with_reconciliation")
        return {"success": False, "message": _("Failed to close shift: {0}").format(str(e))}
