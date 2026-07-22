# Copyright (c) 2020, Youssef Restom and contributors
# For license information, please see license.txt

import json
from typing import Any

import frappe
from erpnext.accounts.doctype.sales_invoice.sales_invoice import get_bank_cash_account
from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice
from erpnext.setup.utils import get_exchange_rate
from erpnext.stock.doctype.batch.batch import (
    get_batch_no,
    get_batch_qty,
)  # This should be from erpnext directly
from frappe import _
from frappe.utils import (
    cint,
    cstr,
    flt,
    getdate,
    money_in_words,
    nowdate,
    strip_html_tags,
)
from frappe.utils.background_jobs import enqueue
from posawesome.posawesome.api.payments import (
    redeeming_customer_credit,
)  # Updated import
from posawesome.posawesome.api.customers import get_loyalty_points
from erpnext.accounts.doctype.payment_entry.payment_entry import (
    get_payment_entry as erpnext_get_payment_entry,
)
from posawesome.posawesome.api.utilities import (
    ensure_child_doctype,
    set_batch_nos_for_bundels,
)  # Updated imports

from .items import get_stock_availability
from posawesome.posawesome.api.frequent_cards import create_or_update_card


def _sanitize_item_name(name: str) -> str:
    """Strip HTML and limit length for item names."""
    if not name:
        return ""
    cleaned = strip_html_tags(name)
    return cleaned.strip()[:140]


def _apply_item_name_overrides(invoice_doc, overrides=None):
    """Apply custom item names to invoice items."""
    overrides = overrides or {}
    for item in invoice_doc.items:
        source = overrides.get(item.idx) or {}
        provided = source.get("item_name") if isinstance(source, dict) else None
        default_name = frappe.get_cached_value("Item", item.item_code, "item_name")
        clean = _sanitize_item_name(provided or item.item_name)
        if clean and clean != default_name:
            item.item_name = clean
            item.name_overridden = 1
        else:
            item.item_name = default_name
            item.name_overridden = 0


def _first_nonempty(*values):
    for value in values:
        if value not in (None, ""):
            return value
    return ""


def _has_column(table, column):
    try:
        table_name = table if str(table).startswith("tab") else f"tab{table}"
        rows = frappe.db.sql(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name = %s
              AND column_name = %s
            LIMIT 1
            """,
            (table_name, column),
            as_dict=True,
        )
        return bool(rows)
    except Exception:
        return False


def _get_vehicle_make_model(data=None, vehicle_no=None, customer=None):
    """Resolve make/model from available vehicle/customer data."""
    data = data or {}
    vehicle_no = cstr(vehicle_no or "").strip()
    customer = cstr(customer or "").strip()

    vehicle_data = data.get("vehicle") if isinstance(data.get("vehicle"), dict) else {}
    customer_data = data.get("customer") if isinstance(data.get("customer"), dict) else {}

    # Direct payload values should win when they are already available.
    make = _first_nonempty(
        data.get("custom_vehicle_make"),
        data.get("vehicle_make"),
        data.get("make"),
        vehicle_data.get("custom_vehicle_make"),
        vehicle_data.get("vehicle_make"),
        vehicle_data.get("make"),
        customer_data.get("custom_vehicle_make"),
        customer_data.get("vehicle_make"),
        customer_data.get("make"),
    )
    model = _first_nonempty(
        data.get("custom_vehicle_model"),
        data.get("vehicle_model"),
        data.get("model"),
        vehicle_data.get("custom_vehicle_model"),
        vehicle_data.get("vehicle_model"),
        vehicle_data.get("model"),
        customer_data.get("custom_vehicle_model"),
        customer_data.get("vehicle_model"),
        customer_data.get("model"),
    )

    if make and model:
        return make, model

    vehicle_fields = ["name"]
    for field in ("vehicle_make", "vehicle_model", "make", "model", "brand", "manufacturer"):
        if _has_column("Vehicle Master", field):
            vehicle_fields.append(field)

    if vehicle_no:
        try:
            vehicle = frappe.get_all(
                "Vehicle Master",
                filters={"vehicle_no": vehicle_no},
                fields=vehicle_fields,
                limit_page_length=1,
            )
        except Exception:
            vehicle = []

        if not vehicle:
            vehicle_fields_vehicle = ["name"]
            for field in (
                "vehicle_make",
                "vehicle_model",
                "make",
                "model",
                "brand",
                "manufacturer",
            ):
                if _has_column("Vehicle", field):
                    vehicle_fields_vehicle.append(field)
            for id_field in ("vehicle_no", "license_plate", "plate_no", "name"):
                if not _has_column("Vehicle", id_field):
                    continue
                try:
                    vehicle = frappe.get_all(
                        "Vehicle",
                        filters={id_field: vehicle_no},
                        fields=vehicle_fields_vehicle,
                        limit_page_length=1,
                    )
                except Exception:
                    vehicle = []
                if vehicle:
                    break

        if vehicle:
            row = vehicle[0]
            make = _first_nonempty(
                row.get("vehicle_make"), row.get("make"), row.get("brand"), row.get("manufacturer")
            )
            model = _first_nonempty(row.get("vehicle_model"), row.get("model"))

    if (not make or not model) and customer:
        try:
            customer_vehicle = frappe.get_all(
                "Vehicle Master",
                filters={"customer": customer},
                fields=vehicle_fields,
                limit_page_length=1,
                order_by="modified desc",
            )
        except Exception:
            customer_vehicle = []

        if not customer_vehicle:
            vehicle_fields_vehicle = ["name"]
            for field in (
                "vehicle_make",
                "vehicle_model",
                "make",
                "model",
                "brand",
                "manufacturer",
            ):
                if _has_column("Vehicle", field):
                    vehicle_fields_vehicle.append(field)
            try:
                customer_vehicle = frappe.get_all(
                    "Vehicle",
                    filters={"customer": customer},
                    fields=vehicle_fields_vehicle,
                    limit_page_length=1,
                    order_by="modified desc",
                )
            except Exception:
                customer_vehicle = []

        if customer_vehicle:
            row = customer_vehicle[0]
            make = make or _first_nonempty(
                row.get("vehicle_make"), row.get("make"), row.get("brand"), row.get("manufacturer")
            )
            model = model or _first_nonempty(row.get("vehicle_model"), row.get("model"))

    return make or "", model or ""


def _resolve_vehicle_make(data=None, invoice_doc=None):
    """Resolve vehicle make from payload, existing doc, or Vehicle lookup."""
    data = data or {}
    invoice_doc = invoice_doc or {}

    make = _first_nonempty(
        data.get("custom_vehicle_make"),
        data.get("make"),
        (
            invoice_doc.get("custom_vehicle_make")
            if hasattr(invoice_doc, "get")
            else invoice_doc.get("custom_vehicle_make")
        ),
    )
    if make:
        return make

    vehicle_no = _first_nonempty(
        data.get("custom_vehicle_no"),
        (
            invoice_doc.get("custom_vehicle_no")
            if hasattr(invoice_doc, "get")
            else invoice_doc.get("custom_vehicle_no")
        ),
    )
    vehicle_no = cstr(vehicle_no or "").strip()
    if not vehicle_no:
        return ""

    for filters in ({"license_plate": vehicle_no}, {"name": vehicle_no}):
        try:
            make = frappe.db.get_value("Vehicle", filters, "make")
        except Exception:
            make = ""
        if make:
            return cstr(make).strip()

    return ""


def _normalize_discount_state(invoice_doc, data=None):
    """Keep only one active discount path on the invoice."""
    data = data or {}

    custom_redeemed_loyalty_points = flt(
        data.get("custom_redeemed_loyalty_points")
        or invoice_doc.get("custom_redeemed_loyalty_points")
        or data.get("redeemed_loyalty_points")
        or data.get("redeem_loyalty_points")
        or 0
    )
    loyalty_discount_amount = flt(
        data.get("loyalty_discount_amount")
        or data.get("loyalty_amount")
        or invoice_doc.get("loyalty_discount_amount")
        or invoice_doc.get("loyalty_amount")
        or 0
    )
    redeemed_coupon_amount = flt(
        data.get("redeemed_coupon_amount") or invoice_doc.get("redeemed_coupon_amount") or 0
    )
    redeemed_offer_amount = flt(
        data.get("redeemed_offer_amount") or invoice_doc.get("redeemed_offer_amount") or 0
    )
    additional_discount = flt(data.get("additional_discount") or invoice_doc.get("additional_discount") or 0)
    discount_amount = flt(data.get("discount_amount") or invoice_doc.get("discount_amount") or 0)
    conversion_factor = flt(
        data.get("conversion_factor")
        or invoice_doc.get("conversion_factor")
        or invoice_doc.get("loyalty_conversion_factor")
        or 0
    )
    available_loyalty_points = flt(
        data.get("available_loyalty_points") or invoice_doc.get("available_loyalty_points") or 0
    )

    active_type = None
    active_amount = additional_discount or discount_amount

    if custom_redeemed_loyalty_points > 0 or loyalty_discount_amount > 0:
        active_type = "loyalty"
        active_amount = loyalty_discount_amount or additional_discount or discount_amount
        invoice_doc.custom_redeemed_loyalty_points = custom_redeemed_loyalty_points
        invoice_doc.redeemed_loyalty_points = custom_redeemed_loyalty_points
        invoice_doc.redeem_loyalty_points = custom_redeemed_loyalty_points
        invoice_doc.loyalty_amount = active_amount
        invoice_doc.loyalty_discount_amount = active_amount
        invoice_doc.redeemed_coupon_amount = 0
        invoice_doc.redeemed_offer_amount = 0
    elif redeemed_coupon_amount > 0:
        active_type = "coupon"
        active_amount = redeemed_coupon_amount or additional_discount or discount_amount
        invoice_doc.custom_redeemed_loyalty_points = 0
        invoice_doc.redeemed_loyalty_points = 0
        invoice_doc.redeem_loyalty_points = 0
        invoice_doc.loyalty_amount = 0
        invoice_doc.loyalty_discount_amount = 0
        invoice_doc.redeemed_coupon_amount = active_amount
        invoice_doc.redeemed_offer_amount = 0
    elif redeemed_offer_amount > 0:
        active_type = "offer"
        active_amount = redeemed_offer_amount or additional_discount or discount_amount
        invoice_doc.custom_redeemed_loyalty_points = 0
        invoice_doc.redeemed_loyalty_points = 0
        invoice_doc.redeem_loyalty_points = 0
        invoice_doc.loyalty_amount = 0
        invoice_doc.loyalty_discount_amount = 0
        invoice_doc.redeemed_coupon_amount = 0
        invoice_doc.redeemed_offer_amount = active_amount
    else:
        invoice_doc.custom_redeemed_loyalty_points = 0
        invoice_doc.redeemed_loyalty_points = 0
        invoice_doc.redeem_loyalty_points = 0
        invoice_doc.loyalty_amount = 0
        invoice_doc.loyalty_discount_amount = 0
        invoice_doc.redeemed_coupon_amount = 0
        invoice_doc.redeemed_offer_amount = 0

    invoice_doc.discount_amount = active_amount
    invoice_doc.additional_discount = active_amount

    return active_type


def _get_available_stock(item):
    """Return available stock qty for an item row.

    If item is explicitly non-stock/service, return 0 (so validation won't block because we will skip such items
    in _collect_stock_errors). Otherwise query batch or stock availability.
    """
    # respect explicit flags to avoid querying stock for service items
    if item.get("is_service_item") == 1 or item.get("update_stock") == 0 or item.get("is_stock_item") == 0:
        return 0

    warehouse = item.get("warehouse")
    batch_no = item.get("batch_no")
    item_code = item.get("item_code")
    if not item_code or not warehouse:
        return 0
    if batch_no:
        return get_batch_qty(batch_no, warehouse) or 0
    return get_stock_availability(item_code, warehouse)


def _collect_stock_errors(items):
    """Return list of items exceeding available stock.

    Skip service/non-stock items (is_service_item == 1 or update_stock == 0 or is_stock_item == 0).
    """
    errors = []
    for d in items:
        # skip negative quantities (returns) or clearly non-stock/service items
        if flt(d.get("qty") or d.get("stock_qty") or 0) < 0:
            continue

        # If front-end marked the item as service or to skip stock updates, ignore it
        if d.get("is_service_item") == 1 or d.get("update_stock") == 0 or d.get("is_stock_item") == 0:
            continue

        available = _get_available_stock(d)
        # requested should be stock_qty if provided, otherwise qty * conversion_factor
        requested = flt(d.get("stock_qty") or (flt(d.get("qty") or 0) * flt(d.get("conversion_factor") or 1)))

        if requested > available:
            errors.append(
                {
                    "item_code": d.get("item_code"),
                    "warehouse": d.get("warehouse"),
                    "requested_qty": requested,
                    "available_qty": available,
                }
            )

    return errors


# def _merge_duplicate_taxes(invoice_doc):
#     """Remove duplicate tax rows with same account and rate.

#     If duplicates are found, keep the first occurrence and recalculate totals.
#     """
#     seen = set()
#     unique = []
#     for tax in invoice_doc.get("taxes", []):
#         key = (tax.account_head, flt(tax.rate), cstr(tax.charge_type))
#         if key in seen:
#             continue
#         seen.add(key)
#         unique.append(tax)
#     if len(unique) != len(invoice_doc.get("taxes", [])):
#         invoice_doc.set("taxes", unique)
#         invoice_doc.calculate_taxes_and_totals()


def _should_block(pos_profile):
    block_sale = cint(
        frappe.db.get_value("POS Profile", pos_profile, "posa_block_sale_beyond_available_qty") or 1
    )
    allow_negative = cint(frappe.get_value("Stock Settings", None, "allow_negative_stock"))
    return block_sale and not allow_negative


def _validate_stock_on_invoice(invoice_doc):
    # If doc explicitly disables update_stock
    if invoice_doc.get("update_stock") == 0:
        return

    items_to_check = [d.as_dict() for d in invoice_doc.items if d.get("is_stock_item")]
    if hasattr(invoice_doc, "packed_items"):
        items_to_check.extend([d.as_dict() for d in invoice_doc.packed_items])
    errors = _collect_stock_errors(items_to_check)
    if errors and _should_block(invoice_doc.pos_profile):
        frappe.throw(frappe.as_json({"errors": errors}), frappe.ValidationError)


def _auto_set_return_batches(invoice_doc):
    """Assign batch numbers for return invoices without a source invoice.

    When the POS Profile allows returns without an original invoice and an
    item requires a batch number, this function allocates the first
    available batch in FIFO order. If no batches exist in the selected
    warehouse, an informative error is raised instead of the generic
    validation error.
    """

    if not invoice_doc.is_return or invoice_doc.get("return_against"):
        return

    profile = invoice_doc.get("pos_profile")
    allow_without_invoice = profile and frappe.db.get_value(
        "POS Profile", profile, "posa_allow_return_without_invoice"
    )
    if not cint(allow_without_invoice):
        return

    allow_free = cint(frappe.db.get_value("POS Profile", profile, "posa_allow_free_batch_return") or 0)

    for d in invoice_doc.items:
        if not d.get("item_code") or not d.get("warehouse"):
            continue

        has_batch = frappe.db.get_value("Item", d.item_code, "has_batch_no")
        if has_batch and not d.get("batch_no"):
            batch_list = get_batch_qty(item_code=d.item_code, warehouse=d.warehouse) or []
            batch_list = [b for b in batch_list if flt(b.get("qty")) > 0]
            if batch_list:
                # FIFO: batches are already sorted by posting/expiry in ERPNext
                d.batch_no = batch_list[0].get("batch_no")
            elif not allow_free:
                frappe.throw(_("No batches available in {0} for {1}.").format(d.warehouse, d.item_code))


def _clean_invoice_payments_before_submit(invoice_doc):
    """Normalize invoice payment rows right before submit.

    Keeps only positive payment rows for paid POS invoices and clears payments
    entirely for credit/on-account invoices.
    """
    positive_payments = []
    for payment in invoice_doc.get("payments") or []:
        payment.amount = flt(payment.amount)
        payment.base_amount = flt(payment.base_amount or 0)
        if payment.amount > 0:
            positive_payments.append(payment)

    paid_amount = flt(sum(flt(payment.amount) for payment in positive_payments))
    rounded_total = flt(invoice_doc.rounded_total or invoice_doc.grand_total or 0)

    if paid_amount <= 0:
        invoice_doc.set("payments", [])
        invoice_doc.is_pos = 0
        invoice_doc.paid_amount = 0
        invoice_doc.base_paid_amount = 0
        invoice_doc.outstanding_amount = rounded_total
    else:
        invoice_doc.set("payments", positive_payments)
        try:
            invoice_doc.set_account_for_mode_of_payment()
        except Exception:
            frappe.log_error(frappe.get_traceback(), "POS Payment Account Mapping Warning")
        invoice_doc.set_paid_amount()
        invoice_doc.is_pos = 1
        invoice_doc.paid_amount = paid_amount
        invoice_doc.base_paid_amount = flt(paid_amount * flt(invoice_doc.conversion_rate or 1))
        invoice_doc.outstanding_amount = flt(rounded_total - paid_amount)

    return invoice_doc


def _is_credit_sale_or_on_account_payment(payment) -> bool:
    mode_of_payment = cstr(payment.get("mode_of_payment") or "").strip().lower()
    return mode_of_payment in {"credit sale", "on account", "on-account", "onaccount"} or cint(
        payment.get("is_credit_sale")
    )


def _get_actual_paid_amount(invoice_doc):
    paid_amount = 0
    for payment in invoice_doc.get("payments") or []:
        amount = flt(payment.get("amount"))
        if amount <= 0:
            continue
        if _is_credit_sale_or_on_account_payment(payment):
            continue
        paid_amount += amount
    return flt(paid_amount)


def _log_submit_debug(invoice_doc, label="submit_invoice"):
    """Write accounting state to Frappe error log for submit debugging."""
    try:
        frappe.log_error(
            message=frappe.as_json(invoice_doc.as_dict(), indent=2),
            title=f"[{label}] invoice_doc.as_dict {invoice_doc.doctype} {invoice_doc.name}",
        )
    except Exception:
        frappe.log_error(
            message=frappe.get_traceback(),
            title=f"[{label}] invoice_doc.as_dict failed {invoice_doc.doctype} {invoice_doc.name}",
        )

    try:
        frappe.log_error(
            message=frappe.as_json(invoice_doc.get("payments") or [], indent=2),
            title=f"[{label}] invoice_doc.payments {invoice_doc.doctype} {invoice_doc.name}",
        )
    except Exception:
        frappe.log_error(
            message=frappe.get_traceback(),
            title=f"[{label}] invoice_doc.payments failed {invoice_doc.doctype} {invoice_doc.name}",
        )

    try:
        frappe.log_error(
            message=frappe.as_json(invoice_doc.get("taxes") or [], indent=2),
            title=f"[{label}] invoice_doc.taxes {invoice_doc.doctype} {invoice_doc.name}",
        )
    except Exception:
        frappe.log_error(
            message=frappe.get_traceback(),
            title=f"[{label}] invoice_doc.taxes failed {invoice_doc.doctype} {invoice_doc.name}",
        )

    try:
        gl_entries = invoice_doc.get_gl_entries()
        frappe.log_error(
            message=frappe.as_json(gl_entries or [], indent=2),
            title=f"[{label}] invoice_doc.get_gl_entries {invoice_doc.doctype} {invoice_doc.name}",
        )
    except Exception:
        frappe.log_error(
            message=frappe.get_traceback(),
            title=f"[{label}] invoice_doc.get_gl_entries failed {invoice_doc.doctype} {invoice_doc.name}",
        )


def _submit_payment_entries_for_invoice(invoice_doc):
    """Create one Payment Entry for each POS payment row."""

    if cint(invoice_doc.get("is_return")):
        return []

    if not invoice_doc.get("customer"):
        frappe.throw(_("Customer is missing on invoice {0}.").format(invoice_doc.name))

    existing_payment_entries = frappe.get_all(
        "Payment Entry Reference",
        filters={
            "reference_doctype": invoice_doc.doctype,
            "reference_name": invoice_doc.name,
            "docstatus": 1,
        },
        fields=["parent"],
    )

    if existing_payment_entries:
        return list({row.parent for row in existing_payment_entries if row.parent})

    valid_payments = [
        payment
        for payment in (invoice_doc.get("payments") or [])
        if flt(payment.get("amount")) > 0 and not _is_credit_sale_or_on_account_payment(payment)
    ]

    if not valid_payments:
        return []

    submitted_entries = []

    try:
        for index, payment in enumerate(valid_payments, start=1):
            payment_amount = flt(payment.get("amount"))

            if payment_amount <= 0:
                continue

            # Reload after every Payment Entry so outstanding is current.
            invoice_doc.reload()

            remaining_outstanding = flt(invoice_doc.get("outstanding_amount"))

            if remaining_outstanding <= 0:
                break

            payment_amount = min(
                payment_amount,
                remaining_outstanding,
            )

            # Generate a fresh standard ERPNext Payment Entry
            # for this specific split-payment row.
            payment_entry = erpnext_get_payment_entry(
                invoice_doc.doctype,
                invoice_doc.name,
            )

            payment_entry.flags.ignore_permissions = True
            frappe.flags.ignore_account_permission = True

            payment_entry.payment_type = "Receive"
            payment_entry.party_type = "Customer"
            payment_entry.party = invoice_doc.customer

            # Each entry receives its own payment method.
            payment_entry.mode_of_payment = payment.get("mode_of_payment")

            payment_entry.reference_no = f"{invoice_doc.name}-{index}"
            payment_entry.reference_date = invoice_doc.get("posting_date")

            # Resolve the correct account for this payment method.
            payment_entry.setup_party_account_field()
            payment_entry.set_missing_values()

            payment_entry.paid_amount = payment_amount
            payment_entry.received_amount = payment_amount

            if payment_entry.get("references"):
                payment_entry.references[0].allocated_amount = payment_amount

            payment_entry.set_amounts()

            # Restore the correct split amount after recalculation.
            payment_entry.paid_amount = payment_amount
            payment_entry.received_amount = payment_amount

            if payment_entry.get("references"):
                payment_entry.references[0].allocated_amount = payment_amount

            # Restore party after ERPNext field recalculation.
            payment_entry.party_type = "Customer"
            payment_entry.party = invoice_doc.customer

            payment_entry.save(ignore_permissions=True)
            payment_entry.submit()

            submitted_entries.append(payment_entry.name)

        invoice_doc.reload()

        if flt(invoice_doc.get("outstanding_amount")) != 0 or invoice_doc.get("status") != "Paid":
            frappe.throw(
                _(
                    "Split payments were submitted, but invoice {0} "
                    "is not fully paid. Outstanding amount: {1}"
                ).format(
                    invoice_doc.name,
                    invoice_doc.get("outstanding_amount"),
                )
            )

        return submitted_entries

    except Exception:
        # Remove Payment Entries created during this failed attempt.
        for entry_name in reversed(submitted_entries):
            try:
                payment_entry = frappe.get_doc(
                    "Payment Entry",
                    entry_name,
                )

                if cint(payment_entry.docstatus) == 1:
                    payment_entry.cancel()

                if frappe.db.exists(
                    "Payment Entry",
                    entry_name,
                ):
                    frappe.delete_doc(
                        "Payment Entry",
                        entry_name,
                        ignore_permissions=True,
                    )

            except Exception:
                frappe.log_error(
                    frappe.get_traceback(),
                    f"Failed to rollback Payment Entry {entry_name}",
                )

        raise


@frappe.whitelist()
def validate_cart_items(items, pos_profile=None):
    """Validate cart items for available stock.

    Returns a list of item dicts where requested quantity exceeds availability.
    This can be used on the front-end for pre-submission checks.
    """

    if isinstance(items, str):
        items = json.loads(items)
    return _collect_stock_errors(items)


def get_latest_rate(from_currency: str, to_currency: str):
    """Return the most recent Currency Exchange rate and its date."""
    rate_doc = frappe.get_all(
        "Currency Exchange",
        filters={"from_currency": from_currency, "to_currency": to_currency},
        fields=["exchange_rate", "date"],
        order_by="date desc, creation desc",
        limit=1,
    )
    if rate_doc:
        return flt(rate_doc[0].exchange_rate), rate_doc[0].date
    rate = get_exchange_rate(from_currency, to_currency, nowdate())
    return flt(rate), nowdate()


@frappe.whitelist()
def validate_return_items(original_invoice_name, return_items, doctype="Sales Invoice"):
    """
    Ensure that return items do not exceed the quantity from the original invoice.
    """
    original_invoice = frappe.get_doc(doctype, original_invoice_name)
    original_item_qty = {}

    for item in original_invoice.items:
        original_item_qty[item.item_code] = original_item_qty.get(item.item_code, 0) + item.qty

    returned_items = frappe.get_all(
        doctype,
        filters={
            "return_against": original_invoice_name,
            "docstatus": 1,
            "is_return": 1,
        },
        fields=["name"],
    )

    for returned_invoice in returned_items:
        ret_doc = frappe.get_doc(doctype, returned_invoice.name)
        for item in ret_doc.items:
            if item.item_code in original_item_qty:
                original_item_qty[item.item_code] -= abs(item.qty)

    for item in return_items:
        item_code = item.get("item_code")
        return_qty = abs(item.get("qty", 0))
        if item_code in original_item_qty and return_qty > original_item_qty[item_code]:
            return {
                "valid": False,
                "message": _("You are trying to return more quantity for item {0} than was sold.").format(
                    item_code
                ),
            }

    return {"valid": True}


@frappe.whitelist()
def update_invoice(data):
    data = json.loads(data)
    incoming_rounding_adjustment = flt(data.get("rounding_adjustment") or 0)

    pos_profile = data.get("pos_profile")
    doctype = "Sales Invoice"
    if pos_profile and frappe.db.get_value(
        "POS Profile",
        pos_profile,
        "create_pos_invoice_instead_of_sales_invoice",
    ):
        doctype = "POS Invoice"

    data.setdefault("doctype", doctype)

    if data.get("name"):
        invoice_doc = frappe.get_doc(doctype, data.get("name"))
        invoice_doc.update(data)
    else:
        invoice_doc = frappe.get_doc(data)

    # Validate return items against original invoice
    if (data.get("is_return") or invoice_doc.is_return) and invoice_doc.get("return_against"):
        validation = validate_return_items(
            invoice_doc.return_against,
            [d.as_dict() for d in invoice_doc.items],
            doctype=invoice_doc.doctype,
        )
        if not validation.get("valid"):
            frappe.throw(validation.get("message"))

    # Get currency information
    selected_currency = data.get("currency")
    price_list_currency = data.get("price_list_currency")

    if not price_list_currency and invoice_doc.get("selling_price_list"):
        price_list_currency = frappe.db.get_value(
            "Price List",
            invoice_doc.selling_price_list,
            "currency",
        )

    # Auto-create customer if doesn't exist
    customer_name = invoice_doc.get("customer")
    if customer_name and not frappe.db.exists("Customer", customer_name):
        try:
            cust = frappe.get_doc(
                {
                    "doctype": "Customer",
                    "customer_name": customer_name,
                    "customer_group": "All Customer Groups",
                    "territory": "All Territories",
                    "customer_type": "Individual",
                }
            )
            cust.flags.ignore_permissions = True
            cust.insert()
            invoice_doc.customer = cust.name
            invoice_doc.customer_name = cust.customer_name
        except Exception as e:
            frappe.log_error(f"Failed to create customer {customer_name}: {e}")

    invoice_doc.custom_vehicle_make = _resolve_vehicle_make(data, invoice_doc)
    invoice_doc.custom_vehicle_model = (
        data.get("custom_vehicle_model") or data.get("model") or invoice_doc.get("custom_vehicle_model") or ""
    )
    _normalize_discount_state(invoice_doc, data)

    # Store item name overrides for later application
    overrides = {d.idx: {"item_name": d.item_name} for d in invoice_doc.items}

    # Store locked prices for return invoices
    locked_items = {}
    if invoice_doc.is_return:
        for d in invoice_doc.items:
            if d.get("locked_price"):
                locked_items[d.idx] = {
                    "rate": d.rate,
                    "price_list_rate": d.price_list_rate,
                    "discount_percentage": d.discount_percentage,
                    "discount_amount": d.discount_amount,
                    "is_free_item": d.get("is_free_item"),
                }

    # Set pricing rule flags
    invoice_doc.ignore_pricing_rule = 1
    invoice_doc.flags.ignore_pricing_rule = False

    # Fetch default values from POS Profile
    invoice_doc.set_missing_values()

    pre_tax_discount_amount = flt(
        invoice_doc.get("discount_amount") or invoice_doc.get("additional_discount") or 0
    )
    loyalty_discount_amount = flt(
        invoice_doc.get("loyalty_discount_amount") or invoice_doc.get("loyalty_amount") or 0
    )
    additional_discount_amount = flt(invoice_doc.get("additional_discount") or 0)

    mirrored_loyalty_discount = (
        pre_tax_discount_amount > 0
        and additional_discount_amount > 0
        and abs(pre_tax_discount_amount - additional_discount_amount) <= 0.000001
        and abs(pre_tax_discount_amount - loyalty_discount_amount) <= 0.000001
    )

    if mirrored_loyalty_discount:
        pre_tax_discount_amount = 0

    invoice_doc.discount_amount = pre_tax_discount_amount
    invoice_doc.loyalty_discount_amount = loyalty_discount_amount
    if pre_tax_discount_amount > 0 and not invoice_doc.get("apply_discount_on"):
        invoice_doc.apply_discount_on = "Net Total"

    # ===== CRITICAL: TAX CALCULATION =====
    pos_profile_name = invoice_doc.get("pos_profile")

    # Get existing total tax amount before clearing (for comparison)
    existing_tax = sum(flt(t.tax_amount) for t in invoice_doc.get("taxes", []))

    if pos_profile_name:
        tax_template_name = frappe.db.get_value(
            "POS Profile",
            pos_profile_name,
            "taxes_and_charges",
        )

        if tax_template_name:
            try:
                tax_template = frappe.get_doc(
                    "Sales Taxes and Charges Template",
                    tax_template_name,
                )

                # Get tax inclusive setting
                inclusive = (
                    frappe.get_cached_value(
                        "POS Profile",
                        invoice_doc.pos_profile,
                        "posa_tax_inclusive",
                    )
                    or 0
                )

                # Clear existing taxes when the invoice should follow the POS template.
                # Mixed carts (only some lines carrying item tax metadata) must use the
                # invoice-level VAT template so the full cart is taxed consistently.
                has_item_tax = any(
                    d.get("item_tax_template") or d.get("item_tax_rate") for d in invoice_doc.items
                )
                all_items_have_item_tax = bool(invoice_doc.items) and all(
                    d.get("item_tax_template") or d.get("item_tax_rate") for d in invoice_doc.items
                )
                use_invoice_tax_template = has_item_tax and not all_items_have_item_tax

                if use_invoice_tax_template:
                    for item in invoice_doc.items:
                        item.item_tax_template = None
                        item.item_tax_rate = None
                    invoice_doc.set("taxes", [])
                elif not has_item_tax:
                    invoice_doc.set("taxes", [])
                else:
                    unique_taxes = []
                    seen_tax_keys = set()
                    for tax in invoice_doc.get("taxes", []):
                        tax_key = (
                            cstr(tax.get("account_head")),
                            cstr(tax.get("charge_type")),
                            flt(tax.get("rate") or 0),
                        )
                        if tax_key in seen_tax_keys:
                            continue
                        seen_tax_keys.add(tax_key)
                        unique_taxes.append(tax)
                    invoice_doc.set("taxes", unique_taxes)

                existing_tax_keys = {
                    (
                        cstr(existing.get("account_head")),
                        cstr(existing.get("charge_type")),
                        flt(existing.get("rate") or 0),
                    )
                    for existing in invoice_doc.get("taxes", [])
                }

                # Inject tax rows from template
                for tax in tax_template.taxes:
                    tax_key = (cstr(tax.account_head), cstr(tax.charge_type), flt(tax.rate or 0))
                    if tax_key in existing_tax_keys:
                        continue
                    invoice_doc.append(
                        "taxes",
                        {
                            "charge_type": tax.charge_type,
                            "account_head": tax.account_head,
                            "description": tax.description,
                            "rate": tax.rate,
                            "apply_on": tax.get("apply_on") or "Net Total",
                            "cost_center": tax.cost_center or invoice_doc.cost_center,
                            "included_in_print_rate": (0 if tax.charge_type == "Actual" else int(inclusive)),
                        },
                    )
                    existing_tax_keys.add(tax_key)

                frappe.logger().info(
                    f"[update_invoice] Injected {len(tax_template.taxes)} tax rows for invoice {invoice_doc.name or 'new'}"
                )

            except Exception as e:
                frappe.log_error(
                    title="Tax Injection Error",
                    message=f"Failed to inject taxes for invoice {invoice_doc.name or 'new'}: {str(e)}",
                )

    # ===== ALWAYS RECALCULATE TOTALS AFTER TAX INJECTION =====
    invoice_doc.calculate_taxes_and_totals()

    # Restore the original invoice discount while preserving the loyalty discount separately.
    invoice_doc.discount_amount = pre_tax_discount_amount
    invoice_doc.loyalty_discount_amount = loyalty_discount_amount

    # Keep the tax base unchanged; the round-off only affects the final payable amount.
    taxable_net_total = flt(invoice_doc.net_total)
    invoice_doc.rounding_adjustment = incoming_rounding_adjustment
    invoice_doc.base_rounding_adjustment = flt(
        incoming_rounding_adjustment * flt(invoice_doc.conversion_rate or 1)
    )

    running_total = taxable_net_total
    total_tax = 0
    for tax in invoice_doc.get("taxes", []):
        if tax.charge_type == "Actual":
            tax_amount = flt(tax.tax_amount or 0)
        else:
            tax_amount = flt((taxable_net_total * flt(tax.rate or 0)) / 100)
        tax.tax_amount = tax_amount
        running_total += tax_amount
        tax.total = flt(running_total)
        total_tax += tax_amount

    invoice_doc.total_taxes_and_charges = flt(total_tax)
    invoice_doc.base_net_total = flt(taxable_net_total * flt(invoice_doc.conversion_rate or 1))
    invoice_doc.base_total_taxes_and_charges = flt(
        invoice_doc.total_taxes_and_charges * flt(invoice_doc.conversion_rate or 1)
    )
    invoice_doc.grand_total = flt(taxable_net_total + total_tax)
    invoice_doc.rounded_total = flt(invoice_doc.grand_total + incoming_rounding_adjustment)
    invoice_doc.total_amount = flt(invoice_doc.grand_total)
    invoice_doc.to_be_paid = flt(invoice_doc.rounded_total)
    invoice_doc.base_grand_total = flt(invoice_doc.grand_total * flt(invoice_doc.conversion_rate or 1))
    invoice_doc.base_rounded_total = flt(invoice_doc.base_grand_total + invoice_doc.base_rounding_adjustment)

    # Log tax calculation for debugging
    new_tax = sum(flt(t.tax_amount) for t in invoice_doc.get("taxes", []))
    frappe.logger().info(
        f"[update_invoice] Tax calculation: existing={existing_tax}, new={new_tax}, "
        f"total_taxes_and_charges={invoice_doc.total_taxes_and_charges}"
    )

    # Apply item name overrides
    _apply_item_name_overrides(invoice_doc, overrides)

    # Restore locked prices for return invoices
    if locked_items:
        for item in invoice_doc.items:
            locked = locked_items.get(item.idx)
            if locked:
                item.update(locked)
        # Recalculate after restoring locked prices
        invoice_doc.calculate_taxes_and_totals()

    # Set selected currency
    if selected_currency:
        invoice_doc.currency = selected_currency

    # Get company currency
    company_currency = frappe.get_cached_value(
        "Company",
        invoice_doc.company,
        "default_currency",
    )

    price_list_currency = price_list_currency or company_currency
    exchange_rate_date = invoice_doc.posting_date

    # Handle multi-currency conversion
    if invoice_doc.currency != company_currency:
        conversion_rate, exchange_rate_date = get_latest_rate(
            invoice_doc.currency,
            company_currency,
        )

        if not conversion_rate:
            frappe.throw(
                _("Unable to find exchange rate for {0} to {1}").format(
                    invoice_doc.currency, company_currency
                )
            )

        plc_conversion_rate = 1
        if price_list_currency != invoice_doc.currency:
            plc_conversion_rate, _ = get_latest_rate(
                price_list_currency,
                invoice_doc.currency,
            )

        invoice_doc.conversion_rate = conversion_rate
        invoice_doc.plc_conversion_rate = plc_conversion_rate
        invoice_doc.price_list_currency = price_list_currency

        # Convert item amounts to base currency
        for item in invoice_doc.items:
            if item.rate:
                item.base_rate = flt(item.rate * conversion_rate)
            if item.amount:
                item.base_amount = flt(item.amount * conversion_rate)

        # Convert payment amounts to base currency
        for payment in invoice_doc.payments:
            payment.base_amount = flt(payment.amount * conversion_rate)

        # Convert grand total to base currency
        invoice_doc.base_grand_total = flt(invoice_doc.grand_total * conversion_rate)
        invoice_doc.base_in_words = money_in_words(
            invoice_doc.base_grand_total,
            company_currency,
        )

    # Handle return invoice payment amounts (must be negative)
    if invoice_doc.is_return:
        for p in invoice_doc.payments:
            p.amount = -abs(p.amount)
            p.base_amount = -abs(p.base_amount)

        invoice_doc.paid_amount = sum(p.amount for p in invoice_doc.payments)
        invoice_doc.base_paid_amount = sum(p.base_amount for p in invoice_doc.payments)

    # Save the invoice
    invoice_doc.flags.ignore_permissions = True
    frappe.flags.ignore_account_permission = True
    invoice_doc.docstatus = 0
    invoice_doc.save()
    invoice_doc.reload()

    # Prepare response with all calculated values
    response = invoice_doc.as_dict()
    response["conversion_rate"] = invoice_doc.conversion_rate
    response["plc_conversion_rate"] = invoice_doc.plc_conversion_rate
    response["exchange_rate_date"] = exchange_rate_date

    # ===== CRITICAL: ENSURE TAX VALUES IN RESPONSE =====
    response["total_taxes_and_charges"] = flt(invoice_doc.total_taxes_and_charges)
    response["base_total_taxes_and_charges"] = flt(invoice_doc.base_total_taxes_and_charges)
    response["grand_total"] = flt(invoice_doc.grand_total)
    response["rounded_total"] = flt(invoice_doc.rounded_total)
    response["rounding_adjustment"] = flt(invoice_doc.rounding_adjustment)
    response["base_rounding_adjustment"] = flt(invoice_doc.base_rounding_adjustment)
    response["total_amount"] = flt(invoice_doc.grand_total)
    response["to_be_paid"] = flt(invoice_doc.rounded_total)
    response["total"] = flt(invoice_doc.total)
    response["net_total"] = flt(invoice_doc.net_total)
    response["redeem_loyalty_points"] = flt(invoice_doc.get("redeem_loyalty_points") or 0)
    response["redeemed_loyalty_points"] = flt(invoice_doc.get("redeemed_loyalty_points") or 0)
    response["custom_redeemed_loyalty_points"] = flt(invoice_doc.get("custom_redeemed_loyalty_points") or 0)
    response["redeemed_coupon_amount"] = flt(invoice_doc.get("redeemed_coupon_amount") or 0)
    response["redeemed_offer_amount"] = flt(invoice_doc.get("redeemed_offer_amount") or 0)
    response["loyalty_amount"] = flt(invoice_doc.get("loyalty_amount") or 0)
    response["loyalty_discount_amount"] = flt(invoice_doc.loyalty_discount_amount)
    response["base_grand_total"] = flt(invoice_doc.base_grand_total)
    response["base_net_total"] = flt(invoice_doc.base_net_total)

    # Include tax breakdown for frontend display
    response["taxes"] = [
        {
            "account_head": t.account_head,
            "charge_type": t.charge_type,
            "description": t.description,
            "rate": t.rate,
            "tax_amount": flt(t.tax_amount),
            "total": flt(t.total),
            "included_in_print_rate": t.included_in_print_rate,
        }
        for t in invoice_doc.get("taxes", [])
    ]

    frappe.logger().info(
        f"[update_invoice] Response prepared with grand_total={response['grand_total']}, "
        f"taxes={response['total_taxes_and_charges']}, net_total={response['net_total']}"
    )

    return response


@frappe.whitelist()
def delete_draft_invoice(name, doctype="Sales Invoice"):
    """Delete a draft invoice created while setting up payment."""

    if not name:
        return {"deleted": False, "reason": "missing_name"}

    if doctype not in {"Sales Invoice", "POS Invoice"}:
        frappe.throw(_("Unsupported doctype {0}").format(doctype))

    if not frappe.db.exists(doctype, name):
        return {"deleted": False, "reason": "not_found"}

    doc = frappe.get_doc(doctype, name)
    if cint(doc.docstatus) != 0:
        return {"deleted": False, "reason": "not_draft"}

    frappe.delete_doc(doctype, name, ignore_permissions=True)
    return {"deleted": True, "name": name, "doctype": doctype}


def get_current_user_open_shift(user=None):
    user = user or frappe.session.user
    open_shifts = frappe.get_all(
        "POS Opening Shift",
        filters={
            "user": user,
            "pos_closing_shift": ["in", ["", None]],
            "docstatus": 1,
            "status": "Open",
        },
        fields=["name", "pos_profile"],
        order_by="period_start_date desc",
        limit_page_length=1,
    )
    return frappe.get_doc("POS Opening Shift", open_shifts[0]["name"]) if open_shifts else None


@frappe.whitelist()
def submit_invoice(invoice, data):
    data = json.loads(data)
    invoice = json.loads(invoice)
    created_new_invoice = False

    pos_profile = invoice.get("pos_profile")
    doctype = "Sales Invoice"
    if pos_profile and frappe.db.get_value(
        "POS Profile", pos_profile, "create_pos_invoice_instead_of_sales_invoice"
    ):
        doctype = "POS Invoice"

    invoice_name = invoice.get("name")
    if not invoice_name or not frappe.db.exists(doctype, invoice_name):
        created = update_invoice(json.dumps(invoice))
        invoice_name = created.get("name")
        invoice_doc = frappe.get_doc(doctype, invoice_name)
        created_new_invoice = True
    else:
        invoice_doc = frappe.get_doc(doctype, invoice_name)
        invoice_doc.update(invoice)

    _apply_item_name_overrides(invoice_doc)
    if invoice.get("posa_delivery_date"):
        invoice_doc.update_stock = 0

    mop_cash_list = [
        i.mode_of_payment
        for i in invoice_doc.payments
        if "cash" in i.mode_of_payment.lower() and i.type == "Cash"
    ]
    if len(mop_cash_list) > 0:
        cash_account = get_bank_cash_account(mop_cash_list[0], invoice_doc.company)
    else:
        cash_account = {"account": frappe.get_value("Company", invoice_doc.company, "default_cash_account")}

    items = []
    for item in invoice_doc.items:
        if item.item_name and item.rate and item.qty:
            total = item.rate * item.qty
            items.append(f"{item.item_name} - Rate: {item.rate}, Qty: {item.qty}, Amount: {total}")

    grand_total = f"\nGrand Total: {invoice_doc.grand_total}"
    items.append(grand_total)
    invoice_doc.remarks = "\n".join(items)

    total_cash = 0
    if data.get("redeemed_customer_credit"):
        total_cash = invoice_doc.total - float(data.get("redeemed_customer_credit"))

    is_payment_entry = 0
    if data.get("redeemed_customer_credit"):
        for row in data.get("customer_credit_dict"):
            if row["type"] == "Advance" and row["credit_to_redeem"]:
                is_payment_entry = 1

    payments = invoice_doc.payments
    _auto_set_return_batches(invoice_doc)
    set_batch_nos_for_bundels(invoice_doc, "warehouse", throw=True)
    _validate_stock_on_invoice(invoice_doc)

    invoice_doc.flags.ignore_permissions = True
    frappe.flags.ignore_account_permission = True
    invoice_doc.posa_is_printed = 1

    def _rollback_failed_created_invoice(doc):
        if not created_new_invoice:
            return
        try:
            if cint(doc.docstatus) == 1:
                doc.cancel()
            if frappe.db.exists(doc.doctype, doc.name):
                frappe.delete_doc(doc.doctype, doc.name, ignore_permissions=True)
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"POS submit rollback failed for {doc.doctype} {doc.name}",
            )

    # ============================================================
    # FIX: Force due_date to be >= posting_date BEFORE any operation
    # ============================================================

    posting_date = getdate(invoice_doc.posting_date) if invoice_doc.posting_date else getdate(nowdate())

    # Get the due_date from data first, then fall back to invoice_doc
    due_date_from_data = data.get("due_date")
    if due_date_from_data:
        try:
            due_date = getdate(due_date_from_data)
        except:
            due_date = posting_date
    else:
        try:
            due_date = getdate(invoice_doc.due_date) if invoice_doc.due_date else posting_date
        except:
            due_date = posting_date

    # Ensure due_date is >= posting_date
    if due_date < posting_date:
        due_date = posting_date

    # Set it directly on the document AND in the database
    invoice_doc.due_date = due_date

    frappe.logger().info(f"Invoice {invoice_doc.name}: posting_date={posting_date}, due_date={due_date}")

    # Directly update in database BEFORE save/submit
    frappe.db.set_value(
        invoice_doc.doctype,
        invoice_doc.name,
        "due_date",
        due_date,
        update_modified=False,
    )
    frappe.db.commit()

    frappe.logger().info(
        frappe.as_json(
            {
                "invoice_doc.payments before reload": [
                    payment.as_dict() for payment in (invoice_doc.get("payments") or [])
                ]
            }
        )
    )

    # Reload to get fresh document
    invoice_doc = frappe.get_doc(invoice_doc.doctype, invoice_doc.name)
    frappe.logger().info(
        frappe.as_json(
            {
                "invoice_doc.payments after reload": [
                    payment.as_dict() for payment in (invoice_doc.get("payments") or [])
                ]
            }
        )
    )
    invoice_doc.update(invoice)
    invoice_doc.custom_vehicle_make = _resolve_vehicle_make(invoice, invoice_doc)
    invoice_doc.custom_vehicle_model = (
        invoice_doc.get("custom_vehicle_model")
        or invoice.get("custom_vehicle_model")
        or invoice.get("model")
        or ""
    )
    invoice_doc.custom_redeemed_loyalty_points = flt(
        invoice.get("custom_redeemed_loyalty_points")
        or invoice_doc.get("custom_redeemed_loyalty_points")
        or invoice.get("redeemed_loyalty_points")
        or invoice.get("redeem_loyalty_points")
        or 0
    )
    invoice_doc.redeemed_coupon_amount = flt(
        invoice.get("redeemed_coupon_amount") or invoice_doc.get("redeemed_coupon_amount") or 0
    )
    invoice_doc.redeemed_offer_amount = flt(
        invoice.get("redeemed_offer_amount") or invoice_doc.get("redeemed_offer_amount") or 0
    )

    invoice_doc.flags.ignore_permissions = True
    frappe.flags.ignore_account_permission = True

    company_currency = frappe.get_cached_value("Company", invoice_doc.company, "default_currency")

    frappe.logger().info(
        "[submit_invoice debug] accounting fields for {name}: "
        "is_pos={is_pos}, debit_to={debit_to}, grand_total={grand_total}, rounded_total={rounded_total}, "
        "base_grand_total={base_grand_total}, base_rounded_total={base_rounded_total}, "
        "rounding_adjustment={rounding_adjustment}, base_rounding_adjustment={base_rounding_adjustment}, "
        "paid_amount={paid_amount}, base_paid_amount={base_paid_amount}, "
        "outstanding_amount={outstanding_amount}, "
        "conversion_rate={conversion_rate}, currency={currency}, company_currency={company_currency}".format(
            name=invoice_doc.name,
            is_pos=invoice_doc.get("is_pos"),
            debit_to=invoice_doc.get("debit_to"),
            grand_total=invoice_doc.get("grand_total"),
            rounded_total=invoice_doc.get("rounded_total"),
            base_grand_total=invoice_doc.get("base_grand_total"),
            base_rounded_total=invoice_doc.get("base_rounded_total"),
            rounding_adjustment=invoice_doc.get("rounding_adjustment"),
            base_rounding_adjustment=invoice_doc.get("base_rounding_adjustment"),
            paid_amount=invoice_doc.get("paid_amount"),
            base_paid_amount=invoice_doc.get("base_paid_amount"),
            outstanding_amount=invoice_doc.get("outstanding_amount"),
            conversion_rate=invoice_doc.get("conversion_rate"),
            currency=invoice_doc.get("currency"),
            company_currency=company_currency,
        )
    )

    for idx, payment in enumerate(invoice_doc.get("payments") or [], start=1):
        frappe.logger().info(
            "[submit_invoice debug] payment row {idx} for {name}: "
            "mode_of_payment={mode_of_payment}, account={account}, amount={amount}, "
            "base_amount={base_amount}, default={default}".format(
                idx=idx,
                name=invoice_doc.name,
                mode_of_payment=payment.get("mode_of_payment"),
                account=payment.get("account"),
                amount=payment.get("amount"),
                base_amount=payment.get("base_amount"),
                default=payment.get("default"),
            )
        )

    for idx, tax in enumerate(invoice_doc.get("taxes") or [], start=1):
        frappe.logger().info(
            "[submit_invoice debug] tax row {idx} for {name}: "
            "account_head={account_head}, charge_type={charge_type}, rate={rate}, "
            "tax_amount={tax_amount}, base_tax_amount={base_tax_amount}, total={total}".format(
                idx=idx,
                name=invoice_doc.name,
                account_head=tax.get("account_head"),
                charge_type=tax.get("charge_type"),
                rate=tax.get("rate"),
                tax_amount=tax.get("tax_amount"),
                base_tax_amount=tax.get("base_tax_amount"),
                total=tax.get("total"),
            )
        )

    try:
        gl_entries = invoice_doc.get_gl_entries()
        for idx, gle in enumerate(gl_entries or [], start=1):
            frappe.logger().info(
                "[submit_invoice debug] gl row {idx} for {name}: "
                "account={account}, party_type={party_type}, party={party}, debit={debit}, credit={credit}, "
                "debit_in_account_currency={debit_in_account_currency}, "
                "credit_in_account_currency={credit_in_account_currency}, against={against}".format(
                    idx=idx,
                    name=invoice_doc.name,
                    account=gle.get("account"),
                    party_type=gle.get("party_type"),
                    party=gle.get("party"),
                    debit=gle.get("debit"),
                    credit=gle.get("credit"),
                    debit_in_account_currency=gle.get("debit_in_account_currency"),
                    credit_in_account_currency=gle.get("credit_in_account_currency"),
                    against=gle.get("against"),
                )
            )
    except Exception:
        frappe.log_error(
            message=frappe.get_traceback(),
            title=f"POS submit debug GL map failed for {invoice_doc.doctype} {invoice_doc.name}",
        )

    # Set the POS-specific flags to skip validation
    invoice_doc.flags.posa_skip_due_date_validation = True

    invoice_doc = _clean_invoice_payments_before_submit(invoice_doc)
    frappe.logger().info(
        frappe.as_json(
            {
                "invoice_doc.payments before submit": [
                    payment.as_dict() for payment in (invoice_doc.get("payments") or [])
                ]
            }
        )
    )

    payments = invoice_doc.payments

    pos_payment_rows = [p.as_dict() for p in invoice_doc.get("payments") or []]

    try:
        current_open = get_current_user_open_shift(frappe.session.user)
        if current_open:
            if invoice_doc.get("posa_pos_opening_shift") != current_open.name:
                invoice_doc.posa_pos_opening_shift = current_open.name
                frappe.db.set_value(
                    invoice_doc.doctype,
                    invoice_doc.name,
                    "posa_pos_opening_shift",
                    current_open.name,
                    update_modified=False,
                )
            frappe.db.commit()
            frappe.logger().info(f"Linked invoice {invoice_doc.name} to open shift {current_open.name}")
        else:
            ref = invoice_doc.get("posa_pos_opening_shift")
        if ref:
            try:
                shift = frappe.get_cached_doc("POS Opening Shift", ref)
                if shift.status != "Open":
                    invoice_doc.posa_pos_opening_shift = None
                    frappe.db.set_value(
                        invoice_doc.doctype,
                        invoice_doc.name,
                        "posa_pos_opening_shift",
                        None,
                        update_modified=False,
                    )
                    frappe.db.commit()
                    frappe.logger().info(f"Cleared non-open shift {ref} from invoice {invoice_doc.name}")
            except Exception:
                # if shift doc can't be loaded, clear reference anyway
                invoice_doc.posa_pos_opening_shift = None
                frappe.db.set_value(
                    invoice_doc.doctype,
                    invoice_doc.name,
                    "posa_pos_opening_shift",
                    None,
                    update_modified=False,
                )
                frappe.db.commit()
    except Exception as e:
        frappe.log_error(str(e), "POS Shift Ensure Error")

    invoice_doc = _clean_invoice_payments_before_submit(invoice_doc)
    invoice_doc.custom_vehicle_make = _resolve_vehicle_make(data, invoice_doc)
    _normalize_discount_state(invoice_doc, data)
    invoice_doc.save()
    invoice_doc.reload()

    # ============================================================

    if frappe.get_value(
        "POS Profile",
        invoice_doc.pos_profile,
        "posa_allow_submissions_in_background_job",
    ):
        invoices_list = frappe.get_all(
            invoice_doc.doctype,
            filters={
                "posa_pos_opening_shift": invoice_doc.posa_pos_opening_shift,
                "docstatus": 0,
                "posa_is_printed": 1,
            },
        )
        for invoice in invoices_list:
            enqueue(
                method=submit_in_background_job,
                queue="short",
                timeout=1000,
                is_async=True,
                kwargs={
                    "invoice": invoice.name,
                    "doctype": invoice_doc.doctype,
                    "invoice_doc": invoice_doc,
                    "data": data,
                    "is_payment_entry": is_payment_entry,
                    "total_cash": total_cash,
                    "cash_account": cash_account,
                    "payments": payments,
                },
            )
    else:

        try:
            _log_submit_debug(invoice_doc, label="submit_invoice.before_submit")
            frappe.log_error(
                title="POS Submit Invoice State Before Submit",
                message=frappe.as_json(
                    {
                        "name": invoice_doc.get("name"),
                        "is_pos": invoice_doc.get("is_pos"),
                        "debit_to": invoice_doc.get("debit_to"),
                        "grand_total": invoice_doc.get("grand_total"),
                        "rounded_total": invoice_doc.get("rounded_total"),
                        "base_grand_total": invoice_doc.get("base_grand_total"),
                        "base_rounded_total": invoice_doc.get("base_rounded_total"),
                        "rounding_adjustment": invoice_doc.get("rounding_adjustment"),
                        "base_rounding_adjustment": invoice_doc.get("base_rounding_adjustment"),
                        "paid_amount": invoice_doc.get("paid_amount"),
                        "base_paid_amount": invoice_doc.get("base_paid_amount"),
                        "outstanding_amount": invoice_doc.get("outstanding_amount"),
                        "payments": [p.as_dict() for p in invoice_doc.payments],
                        "taxes": [t.as_dict() for t in invoice_doc.taxes],
                    }
                ),
            )
            try:
                gl_entries = invoice_doc.get_gl_entries()
                frappe.log_error(
                    title="POS Submit GL Map Before Submit",
                    message=frappe.as_json([g.as_dict() for g in gl_entries]),
                )
            except Exception:
                frappe.log_error(frappe.get_traceback(), "POS Submit GL Map Debug Failed")
            invoice_doc.custom_vehicle_make = _resolve_vehicle_make(data, invoice_doc)
            invoice_doc.custom_redeemed_loyalty_points = flt(
                data.get("custom_redeemed_loyalty_points")
                or invoice_doc.get("custom_redeemed_loyalty_points")
                or data.get("redeemed_loyalty_points")
                or data.get("redeem_loyalty_points")
                or 0
            )
            invoice_doc.redeemed_coupon_amount = flt(
                data.get("redeemed_coupon_amount") or invoice_doc.get("redeemed_coupon_amount") or 0
            )
            invoice_doc.redeemed_offer_amount = flt(
                data.get("redeemed_offer_amount") or invoice_doc.get("redeemed_offer_amount") or 0
            )
            invoice_doc.set("payments", [])
            invoice_doc.is_pos = 0
            invoice_doc.paid_amount = 0
            invoice_doc.base_paid_amount = 0
            invoice_doc.outstanding_amount = flt(invoice_doc.rounded_total or invoice_doc.grand_total or 0)

            invoice_doc.submit()
            frappe.log_error(
                title="POS Debtors Debug",
                message=frappe.as_json(
                    {
                        "customer": invoice_doc.customer,
                        "debit_to": invoice_doc.debit_to,
                        "grand_total": invoice_doc.grand_total,
                        "rounded_total": invoice_doc.rounded_total,
                        "paid_amount": invoice_doc.paid_amount,
                        "outstanding_amount": invoice_doc.outstanding_amount,
                        "is_pos": invoice_doc.is_pos,
                    }
                ),
            )
            invoice_doc.reload()
            invoice_doc.set("payments", pos_payment_rows)
            _submit_payment_entries_for_invoice(invoice_doc)
            invoice_doc.reload()

        except frappe.ValidationError as e:
            error_msg = str(e)
            if "Due Date cannot be before" in error_msg:
                frappe.logger().error(f"Due date validation error on submit: {error_msg}")
                # Force set docstatus to 1 via database
                frappe.db.set_value(
                    invoice_doc.doctype,
                    invoice_doc.name,
                    "docstatus",
                    1,
                    update_modified=False,
                )
                frappe.db.commit()
                invoice_doc = frappe.get_doc(invoice_doc.doctype, invoice_doc.name)
            elif "already been fully paid" in error_msg and invoice_doc.docstatus == 0:
                frappe.logger().warning(
                    f"Clearing draft advance allocation before retrying submit for {invoice_doc.doctype} {invoice_doc.name}: {error_msg}"
                )
                invoice_doc.set("advances", [])
                invoice_doc.flags.ignore_permissions = True
                frappe.flags.ignore_account_permission = True
                invoice_doc.save()
                invoice_doc.reload()
                invoice_doc.set("payments", [])
                invoice_doc.is_pos = 0
                invoice_doc.paid_amount = 0
                invoice_doc.base_paid_amount = 0
                invoice_doc.outstanding_amount = flt(
                    invoice_doc.rounded_total or invoice_doc.grand_total or 0
                )
                invoice_doc.submit()
                invoice_doc.reload()
                invoice_doc.set("payments", pos_payment_rows)
                _submit_payment_entries_for_invoice(invoice_doc)
                invoice_doc.reload()
                if invoice_doc.docstatus == 1:
                    invoice_doc.reload()
            else:
                _rollback_failed_created_invoice(invoice_doc)
                raise
        except Exception:
            _rollback_failed_created_invoice(invoice_doc)
            frappe.log_error(
                message=frappe.get_traceback(),
                title=f"POS submit failed for {invoice_doc.doctype} {invoice_doc.name}",
            )
            raise

    if invoice_doc.docstatus == 1 and flt(data.get("redeemed_customer_credit") or 0) > 0:
        redeeming_customer_credit(invoice_doc, data, is_payment_entry, total_cash, cash_account, payments)

    if invoice_doc.docstatus == 1 and (
        invoice_doc.get("loyalty_program")
        or flt(invoice_doc.get("custom_redeemed_loyalty_points") or 0) > 0
        or flt(invoice_doc.get("redeemed_loyalty_points") or 0) > 0
        or flt(invoice_doc.get("redeem_loyalty_points") or 0) > 0
    ):
        try:
            remaining_loyalty_points = flt(
                get_loyalty_points(invoice_doc.customer, invoice_doc.loyalty_program, invoice_doc.company)
            )
            invoice_doc.loyalty_points = remaining_loyalty_points
            frappe.db.set_value(
                invoice_doc.doctype,
                invoice_doc.name,
                "loyalty_points",
                remaining_loyalty_points,
                update_modified=False,
            )
            invoice_doc.reload()
        except Exception as loyalty_error:
            frappe.log_error(
                frappe.get_traceback(),
                f"POS loyalty remaining points sync failed for {invoice_doc.doctype} {invoice_doc.name}: {loyalty_error}",
            )

    # ============================================================
    # FREQUENT CARDS INTEGRATION - Process after invoice is submitted
    # ============================================================

    # Only process frequent cards if invoice was successfully submitted
    if invoice_doc.docstatus == 1:
        try:
            for item in invoice_doc.items:
                # Check if item has a frequent card reference (free service redemption)
                if hasattr(item, "frequent_card") and item.frequent_card:
                    try:
                        # Link the redeemed card to this invoice using direct DB update
                        frappe.db.set_value(
                            "Frequent Customer Card",
                            item.frequent_card,
                            "redeemed_invoice",
                            invoice_doc.name,
                            update_modified=False,
                        )
                        frappe.db.commit()

                        frappe.logger().info(
                            f"Linked frequent card {item.frequent_card} to invoice {invoice_doc.name}"
                        )
                    except Exception as card_error:
                        frappe.log_error(
                            f"Failed to link frequent card {item.frequent_card} to invoice {invoice_doc.name}: {str(card_error)}",
                            "Frequent Card Linking Error",
                        )
                else:
                    # Auto-increment visits for service items (not returns)
                    if not invoice_doc.is_return:
                        try:
                            item_doc = frappe.get_cached_doc("Item", item.item_code)

                            # Count visits for explicit service rows from frontend and non-stock service items.
                            # Skip free/redeemed rows so only paid visits are counted.
                            is_service_row = (
                                cint(item.get("is_service_item")) == 1
                                or cint(item.get("update_stock")) == 0
                                or cint(item_doc.is_stock_item) == 0
                            )
                            is_paid_row = flt(item.get("amount")) > 0 or flt(item.get("rate")) > 0
                            if is_service_row and is_paid_row:
                                result = create_or_update_card(
                                    customer=invoice_doc.customer,
                                    service_item=item.item_code,
                                    company=invoice_doc.company,
                                )

                                frappe.logger().info(
                                    f"Frequent card processed for {item.item_code}: {result.get('status')}"
                                )

                                # Show success message if card is now completed
                                if result.get("status") == "updated":
                                    card_data = result.get("card", {})
                                    if card_data.get("status") == "Completed":
                                        # Card just became complete - notify user
                                        frappe.msgprint(
                                            _(
                                                "🎉 Congratulations! Your frequent card for {0} is now complete. Next service is FREE!"
                                            ).format(item.item_name or item.item_code),
                                            indicator="green",
                                            alert=True,
                                            title=_("Frequent Card Completed!"),
                                        )
                                elif result.get("status") == "created":
                                    # New card created
                                    frappe.logger().info(f"New frequent card created for {item.item_code}")

                        except Exception as card_error:
                            # Don't fail the invoice if card processing fails
                            frappe.log_error(
                                f"Failed to process frequent card for item {item.item_code} in invoice {invoice_doc.name}: {str(card_error)}",
                                "Frequent Card Processing Error",
                            )
        except ImportError:
            frappe.log_error(
                "Frequent cards module not found. Please ensure posawesome.posawesome.api.frequent_cards exists.",
                "Frequent Cards Import Error",
            )
        except Exception as e:
            # Log error but don't fail the invoice submission
            frappe.log_error(
                f"Unexpected error processing frequent cards for invoice {invoice_doc.name}: {str(e)}",
                "Frequent Cards General Error",
            )

    invoice_doc.reload()
    return {"name": invoice_doc.name, "docstatus": invoice_doc.docstatus, "status": invoice_doc.status}


def submit_in_background_job(kwargs):
    invoice = kwargs.get("invoice")
    doctype = kwargs.get("doctype") or "Sales Invoice"
    data = kwargs.get("data")
    is_payment_entry = kwargs.get("is_payment_entry")
    total_cash = kwargs.get("total_cash")
    cash_account = kwargs.get("cash_account")
    payments = kwargs.get("payments")

    invoice_doc = frappe.get_doc(doctype, invoice)

    # Update remarks with items details for background job
    items = []
    for item in invoice_doc.items:
        if item.item_name and item.rate and item.qty:
            total = item.rate * item.qty
            items.append(f"{item.item_name} - Rate: {item.rate}, Qty: {item.qty}, Amount: {total}")

    # Add the grand total at the end of remarks
    grand_total = f"\nGrand Total: {invoice_doc.grand_total}"
    items.append(grand_total)

    invoice_doc.custom_vehicle_make = _resolve_vehicle_make(data, invoice_doc)
    invoice_doc.remarks = "\n".join(items)
    invoice_doc.custom_redeemed_loyalty_points = flt(
        data.get("custom_redeemed_loyalty_points")
        or invoice_doc.get("custom_redeemed_loyalty_points")
        or data.get("redeemed_loyalty_points")
        or data.get("redeem_loyalty_points")
        or 0
    )
    invoice_doc.redeemed_coupon_amount = flt(
        data.get("redeemed_coupon_amount") or invoice_doc.get("redeemed_coupon_amount") or 0
    )
    invoice_doc.redeemed_offer_amount = flt(
        data.get("redeemed_offer_amount") or invoice_doc.get("redeemed_offer_amount") or 0
    )
    invoice_doc.save()

    _log_submit_debug(invoice_doc, label="submit_in_background_job.before_submit")
    invoice_doc.custom_vehicle_make = _resolve_vehicle_make(data, invoice_doc)
    invoice_doc.custom_redeemed_loyalty_points = flt(
        data.get("custom_redeemed_loyalty_points")
        or invoice_doc.get("custom_redeemed_loyalty_points")
        or data.get("redeemed_loyalty_points")
        or data.get("redeem_loyalty_points")
        or 0
    )
    invoice_doc.redeemed_coupon_amount = flt(
        data.get("redeemed_coupon_amount") or invoice_doc.get("redeemed_coupon_amount") or 0
    )
    invoice_doc.redeemed_offer_amount = flt(
        data.get("redeemed_offer_amount") or invoice_doc.get("redeemed_offer_amount") or 0
    )
    pos_payment_rows = [p.as_dict() for p in invoice_doc.get("payments") or []]

    invoice_doc.set("payments", [])
    invoice_doc.is_pos = 0
    invoice_doc.paid_amount = 0
    invoice_doc.base_paid_amount = 0
    invoice_doc.outstanding_amount = flt(invoice_doc.rounded_total or invoice_doc.grand_total or 0)

    invoice_doc.submit()
    invoice_doc.reload()
    invoice_doc.set("payments", pos_payment_rows)
    _submit_payment_entries_for_invoice(invoice_doc)
    invoice_doc.reload()
    if flt((data or {}).get("redeemed_customer_credit") or 0) > 0:
        redeeming_customer_credit(invoice_doc, data, is_payment_entry, total_cash, cash_account, payments)

    if invoice_doc.docstatus == 1 and (
        invoice_doc.get("loyalty_program")
        or flt(invoice_doc.get("custom_redeemed_loyalty_points") or 0) > 0
        or flt(invoice_doc.get("redeemed_loyalty_points") or 0) > 0
        or flt(invoice_doc.get("redeem_loyalty_points") or 0) > 0
    ):
        try:
            remaining_loyalty_points = flt(
                get_loyalty_points(invoice_doc.customer, invoice_doc.loyalty_program, invoice_doc.company)
            )
            invoice_doc.loyalty_points = remaining_loyalty_points
            frappe.db.set_value(
                invoice_doc.doctype,
                invoice_doc.name,
                "loyalty_points",
                remaining_loyalty_points,
                update_modified=False,
            )
            invoice_doc.reload()
        except Exception as loyalty_error:
            frappe.log_error(
                frappe.get_traceback(),
                f"POS loyalty remaining points sync failed for {invoice_doc.doctype} {invoice_doc.name}: {loyalty_error}",
            )

    # ============================================================
    # FREQUENT CARDS INTEGRATION - Background Job
    # ============================================================
    if invoice_doc.docstatus == 1:
        try:
            for item in invoice_doc.items:
                # Check if item has a frequent card reference (free service redemption)
                if hasattr(item, "frequent_card") and item.frequent_card:
                    try:
                        # Link the redeemed card to this invoice using direct DB update
                        frappe.db.set_value(
                            "Frequent Customer Card",
                            item.frequent_card,
                            "redeemed_invoice",
                            invoice_doc.name,
                            update_modified=False,
                        )
                        frappe.db.commit()

                        frappe.logger().info(
                            f"[BG Job] Linked frequent card {item.frequent_card} to invoice {invoice_doc.name}"
                        )
                    except Exception as e:
                        frappe.log_error(str(e), "Frequent Card Link Error (BG Job)")
                else:
                    # Auto-increment visits for service items (not returns)
                    if not invoice_doc.is_return:
                        try:
                            item_doc = frappe.get_cached_doc("Item", item.item_code)

                            # Count visits for explicit service rows from frontend and non-stock service items.
                            # Skip free/redeemed rows so only paid visits are counted.
                            is_service_row = (
                                cint(item.get("is_service_item")) == 1
                                or cint(item.get("update_stock")) == 0
                                or cint(item_doc.is_stock_item) == 0
                            )
                            is_paid_row = flt(item.get("amount")) > 0 or flt(item.get("rate")) > 0
                            if is_service_row and is_paid_row:
                                result = create_or_update_card(
                                    customer=invoice_doc.customer,
                                    service_item=item.item_code,
                                    company=invoice_doc.company,
                                )
                                frappe.logger().info(
                                    f"[BG Job] Frequent card processed for {item.item_code}: {result.get('status')}"
                                )
                        except Exception as e:
                            frappe.log_error(str(e), "Frequent Card Process Error (BG Job)")
        except Exception as e:
            frappe.log_error(str(e), "Frequent Cards Error (BG Job)")


@frappe.whitelist()
def delete_invoice(invoice):
    doctype = "Sales Invoice"
    if frappe.db.exists("POS Invoice", invoice):
        doctype = "POS Invoice"
    elif not frappe.db.exists("Sales Invoice", invoice):
        frappe.throw(_("Invoice {0} does not exist").format(invoice))

    if frappe.db.has_column(doctype, "posa_is_printed") and frappe.get_value(
        doctype, invoice, "posa_is_printed"
    ):
        frappe.throw(_("This invoice {0} cannot be deleted").format(invoice))

    frappe.delete_doc(doctype, invoice, force=1)
    return _("Invoice {0} Deleted").format(invoice)


@frappe.whitelist()
def get_draft_invoices(pos_opening_shift, doctype="Sales Invoice"):
    filters = {
        "posa_pos_opening_shift": pos_opening_shift,
        "docstatus": 0,
    }
    if frappe.db.has_column(doctype, "posa_is_printed"):
        filters["posa_is_printed"] = 0

    invoices_list = frappe.get_list(
        doctype,
        filters=filters,
        fields=["name"],
        limit_page_length=0,
        order_by="modified desc",
    )
    data = []
    for invoice in invoices_list:
        data.append(frappe.get_cached_doc(doctype, invoice["name"]))
    return data


@frappe.whitelist()
def update_draft_due_date(name, due_date=None, doctype="Sales Invoice"):
    """Update the due date for a draft invoice/job order."""
    if not name:
        frappe.throw(_("Draft invoice name is required"))

    if not frappe.db.exists(doctype, name):
        frappe.throw(_("Draft invoice not found"))

    updated_due_date = getdate(due_date) if due_date else None
    frappe.db.set_value(
        doctype,
        name,
        "due_date",
        updated_due_date,
        update_modified=False,
    )
    frappe.db.commit()
    return {"name": name, "due_date": frappe.db.get_value(doctype, name, "due_date")}


@frappe.whitelist()
def search_invoices_for_return(
    invoice_name,
    company,
    customer_name=None,
    customer_id=None,
    mobile_no=None,
    tax_id=None,
    from_date=None,
    to_date=None,
    min_amount=None,
    max_amount=None,
    page=1,
    doctype="Sales Invoice",
):
    """
    Search for invoices that can be returned with separate customer search fields and pagination

    Args:
        invoice_name: Invoice ID to search for
        company: Company to search in
        customer_name: Customer name to search for
        customer_id: Customer ID to search for
        mobile_no: Mobile number to search for
        tax_id: Tax ID to search for
        from_date: Start date for filtering
        to_date: End date for filtering
        min_amount: Minimum invoice amount to filter by
        max_amount: Maximum invoice amount to filter by
        page: Page number for pagination (starts from 1)

    Returns:
        Dictionary with:
        - invoices: List of invoice documents
        - has_more: Boolean indicating if there are more invoices to load
    """
    # Start with base filters
    filters = {
        "company": company,
        "docstatus": 1,
        "is_return": 0,
    }

    # Convert page to integer if it's a string
    if page and isinstance(page, str):
        page = int(page)
    else:
        page = 1  # Default to page 1

    # Items per page - can be adjusted based on performance requirements
    page_length = 100
    start = (page - 1) * page_length

    # Add invoice name filter if provided
    if invoice_name:
        filters["name"] = ["like", f"%{invoice_name}%"]

    # Add date range filters if provided
    if from_date:
        filters["posting_date"] = [">=", from_date]

    if to_date:
        if "posting_date" in filters:
            filters["posting_date"] = ["between", [from_date, to_date]]
        else:
            filters["posting_date"] = ["<=", to_date]

    # Add amount filters if provided
    if min_amount:
        filters["grand_total"] = [">=", float(min_amount)]

    if max_amount:
        if "grand_total" in filters:
            # If min_amount was already set, change to between
            filters["grand_total"] = ["between", [float(min_amount), float(max_amount)]]
        else:
            filters["grand_total"] = ["<=", float(max_amount)]

    # If any customer search criteria is provided, find matching customers
    customer_ids = []
    if customer_name or customer_id or mobile_no or tax_id:
        conditions = []
        params = {}

        if customer_name:
            conditions.append("customer_name LIKE %(customer_name)s")
            params["customer_name"] = f"%{customer_name}%"

        if customer_id:
            conditions.append("name LIKE %(customer_id)s")
            params["customer_id"] = f"%{customer_id}%"

        if mobile_no:
            conditions.append("mobile_no LIKE %(mobile_no)s")
            params["mobile_no"] = f"%{mobile_no}%"

        if tax_id:
            conditions.append("tax_id LIKE %(tax_id)s")
            params["tax_id"] = f"%{tax_id}%"

        # Build the WHERE clause for the query
        where_clause = " OR ".join(conditions)
        customer_query = f"""
        SELECT name
        FROM `tabCustomer`
        WHERE {where_clause}
        LIMIT 100
    """

        customers = frappe.db.sql(customer_query, params, as_dict=True)
        customer_ids = [c.name for c in customers]

        # If we found matching customers, add them to the filter
        if customer_ids:
            filters["customer"] = ["in", customer_ids]
        # If customer search criteria provided but no matches found, return empty
        elif any([customer_name, customer_id, mobile_no, tax_id]):
            return {"invoices": [], "has_more": False}

    # Count total invoices matching the criteria (for has_more flag)
    total_count_query = frappe.get_list(
        doctype,
        filters=filters,
        fields=["count(name) as total_count"],
        as_list=False,
    )
    total_count = total_count_query[0].total_count if total_count_query else 0

    # Get invoices matching all criteria with pagination
    invoices_list = frappe.get_list(
        doctype,
        filters=filters,
        fields=["name"],
        limit_start=start,
        limit_page_length=page_length,
        order_by="posting_date desc, name desc",
    )

    # Process and return the results
    data = []

    # Process invoices and check for returns
    for invoice in invoices_list:
        invoice_doc = frappe.get_doc(doctype, invoice.name)

        # Check if any items have already been returned
        has_returns = frappe.get_all(
            doctype,
            filters={"return_against": invoice.name, "docstatus": 1},
            fields=["name"],
        )

        if has_returns:
            # Calculate returned quantity per item_code
            returned_qty = {}
            for ret_inv in has_returns:
                ret_doc = frappe.get_doc(doctype, ret_inv.name)
                for item in ret_doc.items:
                    returned_qty[item.item_code] = returned_qty.get(item.item_code, 0) + abs(item.qty)

            # Filter items with remaining qty
            filtered_items = []
            for item in invoice_doc.items:
                remaining_qty = item.qty - returned_qty.get(item.item_code, 0)
                if remaining_qty > 0:
                    new_item = item.as_dict().copy()
                    new_item["qty"] = remaining_qty
                    new_item["amount"] = remaining_qty * item.rate
                    if item.get("stock_qty"):
                        new_item["stock_qty"] = (
                            item.stock_qty / item.qty * remaining_qty if item.qty else remaining_qty
                        )
                    filtered_items.append(frappe._dict(new_item))

            if filtered_items:
                # Create a copy of invoice with filtered items
                filtered_invoice = frappe.get_doc(doctype, invoice.name)
                filtered_invoice.items = filtered_items
                data.append(filtered_invoice)
        else:
            data.append(invoice_doc)

    # Check if there are more results
    has_more = (start + page_length) < total_count

    return {"invoices": data, "has_more": has_more}


@frappe.whitelist()
def create_sales_invoice_from_order(sales_order):
    sales_invoice = make_sales_invoice(sales_order, ignore_permissions=True)
    sales_invoice.save()
    return sales_invoice


@frappe.whitelist()
def delete_sales_invoice(sales_invoice):
    frappe.delete_doc("Sales Invoice", sales_invoice)


@frappe.whitelist()
def get_sales_invoice_child_table(sales_invoice, sales_invoice_item):
    parent_doc = frappe.get_doc("Sales Invoice", sales_invoice)
    child_doc = frappe.get_doc("Sales Invoice Item", {"parent": parent_doc.name, "name": sales_invoice_item})
    return child_doc


@frappe.whitelist()
def update_invoice_from_order(data):
    data = json.loads(data)
    invoice_doc = frappe.get_doc("Sales Invoice", data.get("name"))
    invoice_doc.update(data)
    invoice_doc.save()
    return invoice_doc


@frappe.whitelist()
def get_available_currencies():
    """Get list of available currencies from ERPNext"""
    return frappe.get_all(
        "Currency",
        fields=["name", "currency_name"],
        filters={"enabled": 1},
        order_by="currency_name",
    )


@frappe.whitelist()
def fetch_exchange_rate(currency: str, company: str, posting_date: str | None = None):
    """Return latest exchange rate and its date."""
    company_currency = frappe.get_cached_value("Company", company, "default_currency")
    rate, date = get_latest_rate(currency, company_currency)
    return {"exchange_rate": rate, "date": date}


@frappe.whitelist()
def fetch_exchange_rate_pair(from_currency: str, to_currency: str, posting_date: str | None = None):
    """Return latest exchange rate between two currencies along with rate date."""
    rate, date = get_latest_rate(from_currency, to_currency)
    return {"exchange_rate": rate, "date": date}


@frappe.whitelist()
def get_price_list_currency(price_list: str) -> str:
    """Return the currency of the given Price List."""
    if not price_list:
        return None
    return frappe.db.get_value("Price List", price_list, "currency")


@frappe.whitelist()
def get_vehicles_by_customer(doctype, txt, searchfield, start, page_len, filters):
    customer = (filters or {}).get("customer")
    if not customer:
        return []

    start = int(start or 0)
    page_len = int(page_len or 20)

    vehicles = frappe.get_all(
        "Vehicle Master",
        filters={"customer": customer},
        fields=["name", "vehicle_no", "model"],
        order_by="name asc",
        limit_start=start,
        limit_page_length=page_len,
    )

    results = []
    for v in vehicles:
        name = v.get("name")
        label = v.get("vehicle_no") or name
        if v.get("model"):
            label = f"{label} — {v.get('model')}"
        results.append([name, label])

    return results
