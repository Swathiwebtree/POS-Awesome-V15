# -*- coding: utf-8 -*-
# Copyright (c) 2020, Youssef Restom and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from frappe.utils import now
from frappe.utils.data import flt
import json
import frappe
from frappe.utils import nowdate
from frappe import _
from .utilities import get_version


@frappe.whitelist()
def get_opening_dialog_data():
    data = {}

    # Get only POS Profiles where current user is defined in POS Profile User table
    pos_profiles_data = frappe.db.sql(
        """
        SELECT DISTINCT p.name, p.company, p.currency 
        FROM `tabPOS Profile` p
        INNER JOIN `tabPOS Profile User` u ON u.parent = p.name
        WHERE p.disabled = 0 AND u.user = %s
        ORDER BY p.name
    """,
        frappe.session.user,
        as_dict=1,
    )

    data["pos_profiles_data"] = pos_profiles_data

    # Derive companies from accessible POS Profiles
    company_names = []
    for profile in pos_profiles_data:
        if profile.company and profile.company not in company_names:
            company_names.append(profile.company)
    data["companies"] = [{"name": c} for c in company_names]

    pos_profiles_list = []
    for i in data["pos_profiles_data"]:
        pos_profiles_list.append(i.name)

    payment_method_table = "POS Payment Method" if get_version() == 13 else "Sales Invoice Payment"
    data["payments_method"] = frappe.get_list(
        payment_method_table,
        filters={"parent": ["in", pos_profiles_list]},
        fields=["*"],
        limit_page_length=0,
        order_by="parent",
        ignore_permissions=True,
    )
    # set currency from pos profile
    for mode in data["payments_method"]:
        mode["currency"] = frappe.get_cached_value("POS Profile", mode["parent"], "currency")

    return data


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
    open_vouchers = frappe.db.get_all(
        "POS Opening Shift",
        filters={
            "user": user,
            "pos_closing_shift": ["in", ["", None]],
            "docstatus": 1,
            "status": "Open",
        },
        fields=["name", "pos_profile"],
        order_by="period_start_date desc",
    )
    data = ""
    if len(open_vouchers) > 0:
        data = {}
        data["pos_opening_shift"] = frappe.get_doc("POS Opening Shift", open_vouchers[0]["name"])
        update_opening_shift_data(data, open_vouchers[0]["pos_profile"])
    return data


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
    """
    Closes the latest open POS Opening Shift for the current session user.
    Returns: { success: True/False, message: "..." }
    """
    try:
        user = frappe.session.user
        # Find latest open POS Opening Shift for the user
        open_shifts = frappe.get_all(
            "POS Opening Shift",
            filters={
                "user": user,
                "pos_closing_shift": ["in", ["", None]],
                "docstatus": 1,
                "status": "Open",
            },
            fields=["name"],
            limit_page_length=1,
            order_by="period_start_date desc",
        )

        if not open_shifts:
            return {"success": False, "message": _("No open shift found for user.")}

        docname = open_shifts[0]["name"]
        shift = frappe.get_doc("POS Opening Shift", docname)

        # Mark closing timestamp and change status
        shift.pos_closing_shift = now()  # timestamp; change to nowdate() if you want date-only
        # if you also have a separate closing doc relationship, adjust accordingly
        shift.status = "Closed"
        shift.save(ignore_permissions=True)

        # Optionally you may want to run any closing logic/hooks here

        return {"success": True, "message": _("Shift closed successfully")}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "posawesome.close_shift")
        return {"success": False, "message": _("Failed to close shift: {0}").format(str(e))}


@frappe.whitelist()
def get_closing_dialog_data():
    """
    Return data needed to populate the closing dialog.
    This implementation avoids referencing non-existent SQL columns (e.g. p.currency)
    by fetching payment methods and then resolving currency per POS Profile.
    """
    data = {}

    # Find POS Profiles where current user is part of POS Profile User
    pos_profiles_data = frappe.db.sql(
        """
        SELECT DISTINCT p.name, p.company
        FROM `tabPOS Profile` p
        INNER JOIN `tabPOS Profile User` u ON u.parent = p.name
        WHERE p.disabled = 0 AND u.user = %s
        ORDER BY p.name
        """,
        frappe.session.user,
        as_dict=1,
    )

    # If none found, return empty
    if not pos_profiles_data:
        data["pos_profiles_data"] = []
        data["companies"] = []
        data["payments_method"] = []
        return data

    data["pos_profiles_data"] = pos_profiles_data

    # Derive company list
    company_names = []
    for profile in pos_profiles_data:
        if profile.company and profile.company not in company_names:
            company_names.append(profile.company)
    data["companies"] = [{"name": c} for c in company_names]

    # Build list of pos_profile names for filtering payment methods
    pos_profiles_list = [p.name for p in pos_profiles_data]

    # Determine payments table name (compat with different versions)
    payment_method_table = "POS Payment Method" if get_version() == 13 else "Sales Invoice Payment"

    # Fetch payment methods using frappe.get_list (safer than raw SQL select with missing columns)
    payments = frappe.get_list(
        payment_method_table,
        filters={"parent": ["in", pos_profiles_list]},
        fields=["*"],
        limit_page_length=0,
        order_by="parent",
        ignore_permissions=True,
    )

    # For each payment method row, populate currency from POS Profile (if not present)
    for row in payments:
        try:
            # many older schemas store currency on the POS Profile, not on the payment row
            # use cached value to avoid extra queries where possible
            profile_currency = frappe.get_cached_value("POS Profile", row.get("parent"), "currency")
            if profile_currency:
                row["currency"] = profile_currency
            else:
                # fallback: try company default currency if profile has no currency
                profile_company = frappe.get_cached_value("POS Profile", row.get("parent"), "company")
                if profile_company:
                    row["currency"] = frappe.get_cached_value(
                        "Company", profile_company, "default_currency"
                    ) or row.get("currency")
        except Exception as e:
            # don't break the entire function for one missing value; log and continue
            frappe.log_error(frappe.get_traceback(), "get_closing_dialog_data: currency lookup failed")
            row["currency"] = row.get("currency") or ""

    data["payments_method"] = payments

    return data


@frappe.whitelist()
def close_shift_with_reconciliation(balance_details=None):
    import json
    from frappe.utils import now

    try:
        user = frappe.session.user
        if isinstance(balance_details, str):
            balance_details = json.loads(balance_details)

        open_shifts = frappe.get_all(
            "POS Opening Shift",
            filters={
                "user": user,
                "pos_closing_shift": ["in", ["", None]],
                "docstatus": 1,
                "status": "Open",
            },
            fields=["name"],
            limit_page_length=1,
            order_by="period_start_date desc",
        )

        if not open_shifts:
            return {"success": False, "message": _("No open shift found for user.")}

        docname = open_shifts[0]["name"]
        shift = frappe.get_doc("POS Opening Shift", docname)

        # --- Persist reconciliation on the doc (avoid db_set before save) ---
        try:
            # If the field exists on the doctype, set it on the doc object
            if "closing_reconciliation" in shift.as_dict():
                shift.closing_reconciliation = json.dumps(balance_details or [])
            else:
                # fallback: add a comment to the document for audit trail
                shift.add_comment(
                    "Comment",
                    _("Closing reconciliation: {0}").format(json.dumps(balance_details or [])),
                )
        except Exception:
            # final fallback: attempt to add a comment and continue
            try:
                shift.add_comment(
                    "Comment",
                    _("Closing reconciliation (fallback): {0}").format(json.dumps(balance_details or [])),
                )
            except Exception:
                # log but continue to try closing shift
                frappe.log_error(frappe.get_traceback(), "posawesome.close_shift_recon_save_error")

        # --- Update closing meta and save once (keeps doc timestamps consistent) ---
        shift.pos_closing_shift = now()
        shift.status = "Closed"

        # Save once - ignore permissions if necessary
        shift.save(ignore_permissions=True)

        return {"success": True, "message": _("Shift closed successfully")}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "posawesome.close_shift_with_reconciliation")
        return {"success": False, "message": _("Failed to close shift: {0}").format(str(e))}
