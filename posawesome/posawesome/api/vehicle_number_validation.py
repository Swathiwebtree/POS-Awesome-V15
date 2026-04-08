import re

import frappe
from frappe import _


def _normalize_vehicle_number(value: str | None) -> str:
    # Keep a simple canonical form so "abc 123" and "ABC123" are treated as the same.
    value = (value or "").strip().upper()
    value = re.sub(r"\s+", "", value)
    return value


def _first_present(doc, fieldnames: list[str]) -> tuple[str | None, str | None]:
    """Return (fieldname, value) for first existing non-empty field on doc."""
    meta = getattr(doc, "meta", None)
    for fieldname in fieldnames:
        if meta and not meta.has_field(fieldname):
            continue
        value = getattr(doc, fieldname, None)
        if value not in (None, ""):
            return fieldname, value
    return None, None


def validate_vehicle_number(doc, method=None):
    """
    Prevent two different customers from having the same vehicle number.

    This runs on the core ERPNext `Vehicle` DocType via hooks.py doc_events.
    """
    plate_field, plate_value = _first_present(doc, ["license_plate", "vehicle_no", "plate_no"])
    if not plate_field or not plate_value:
        return

    normalized = _normalize_vehicle_number(plate_value)
    if not normalized:
        return

    # Write back normalized value for consistent storage/search.
    try:
        setattr(doc, plate_field, normalized)
    except Exception:
        pass

    filters: dict[str, object] = {plate_field: normalized}

    # If make/model exist on this site, also narrow to matching make+model.
    # (If they don't exist, uniqueness falls back to vehicle number alone.)
    if getattr(doc, "meta", None) and doc.meta.has_field("make") and getattr(doc, "make", None):
        filters["make"] = doc.make
    if getattr(doc, "meta", None) and doc.meta.has_field("model") and getattr(doc, "model", None):
        filters["model"] = doc.model

    if getattr(doc, "name", None):
        filters["name"] = ["!=", doc.name]

    query_fields = ["name"]
    has_customer_field = bool(getattr(doc, "meta", None) and doc.meta.has_field("customer"))
    if has_customer_field:
        query_fields.append("customer")

    existing = frappe.get_all("Vehicle", filters=filters, fields=query_fields, limit_page_length=1)
    if not existing:
        return

    row = existing[0]
    existing_customer = row.get("customer") if has_customer_field else None
    this_customer = getattr(doc, "customer", None) if has_customer_field else None

    # If customers differ (or one is empty), block the duplicate.
    if existing_customer != this_customer:
        frappe.throw(
            _(
                "Vehicle Number {0} already exists on Vehicle {1}{2}. It cannot be used for another customer."
            ).format(
                frappe.bold(normalized),
                frappe.bold(row.get("name")),
                f" (Customer: {frappe.bold(existing_customer)})" if existing_customer else "",
            )
        )
