# posawesome/posawesome/api/lazer_pos.py
import frappe
from frappe import _

# Utility: safe get all with fields
def _get_all(dt, fields=None, filters=None, limit=100, or_filters=None, order_by=None):
    return frappe.get_all(
        dt,
        fields=fields or ["name"],
        filters=filters or {},
        or_filters=or_filters,
        limit=limit,
        order_by=order_by,
    )

@frappe.whitelist()
def get_items(search=None, limit=200):
    """
    Return POS items with multiple allowed prices (Small/Medium/Large) and VAT rate.
    """
    qf = []
    if search:
        qf.append(["Item", "item_code", "like", f"%{search}%"])
        qf.append(["Item", "item_name", "like", f"%{search}%"])

    items = frappe.get_list(
        "Item",
        fields=["name as item_code", "item_name", "stock_uom", "description", "is_stock_item"],
        filters={"disabled": 0},
        or_filters=qf or None,
        limit_page_length=limit,
        order_by="modified desc",
    )

    # barcode map
    barcodes = frappe.get_all(
        "Item Barcode",
        fields=["parent as item_code", "barcode"],
        limit=10000,
    )
    bc_map = {}
    for b in barcodes:
        bc_map.setdefault(b.item_code, b.barcode)

    # price options map
    prices = frappe.get_all(
        "Item Price",
        fields=["item_code", "price_list", "price_list_rate"],
        limit=100000,
    )
    price_map = {}
    for p in prices:
        price_map.setdefault(p.item_code, []).append(p)

    # simple VAT detection from Item Tax
    item_taxes = frappe.get_all(
        "Item Tax",
        fields=["parent as item_code", "item_tax_template", "tax_rate"],
        limit=100000,
    )
    vat_map = {}
    for t in item_taxes:
        vat_map.setdefault(t.item_code, t.tax_rate or 0)

    out = []
    for it in items:
        plist = []
        for p in price_map.get(it.item_code, []):
            label = p.price_list if p.price_list in ("Small", "Medium", "Large") else "Default"
            plist.append({"label": label, "rate": float(p.price_list_rate or 0)})

        if not plist:
            try:
                std = frappe.db.get_value("Item", it.item_code, "standard_rate") or 0
            except Exception:
                std = 0
            plist = [{"label": "Default", "rate": float(std)}]

        out.append({
            "item_code": it.item_code,
            "item_name": it.item_name,
            "barcode": bc_map.get(it.item_code),
            "stock_uom": it.stock_uom,
            "in_hand": None,  # fill via Bin if needed
            "price_options": plist,
            "vat_rate": float(vat_map.get(it.item_code) or 0),
        })
    return out

@frappe.whitelist()
def get_item_by_barcode(barcode: str):
    ib = frappe.db.get_value("Item Barcode", {"barcode": barcode}, ["parent"], as_dict=True)
    if not ib:
        return {}
    item_code = ib.parent
    item = frappe.db.get_value("Item", item_code, ["item_name", "stock_uom"], as_dict=True)
    prices = frappe.get_all("Item Price", fields=["price_list", "price_list_rate"], filters={"item_code": item_code})
    item_taxes = frappe.get_all("Item Tax", fields=["tax_rate"], filters={"parent": item_code})
    vat_rate = float(item_taxes[0].tax_rate) if item_taxes else 0.0
    price_options = []
    for p in prices:
        label = p.price_list if p.price_list in ("Small", "Medium", "Large") else "Default"
        price_options.append({"label": label, "rate": float(p.price_list_rate or 0)})
    if not price_options:
        std = frappe.db.get_value("Item", item_code, "standard_rate") or 0
        price_options = [{"label": "Default", "rate": float(std)}]
    return {
        "item_code": item_code,
        "item_name": item.item_name if item else item_code,
        "barcode": barcode,
        "stock_uom": item.stock_uom if item else None,
        "price_options": price_options,
        "vat_rate": vat_rate,
    }

@frappe.whitelist()
def validate_selling_price(item_code: str, price: float):
    """
    Returns ok=True if price equals one of Item Price rates for that item (exact match).
    """
    price = float(price)
    exists = frappe.db.exists(
        "Item Price",
        {"item_code": item_code, "price_list_rate": price}
    )
    if exists:
        return {"ok": True}
    return {"ok": False, "error": _("This is not selling price")}

@frappe.whitelist()
def sales_listings(limit: int = 500):
    """
    Fetch Sales Invoices to feed the Listings grid. Many fields might be custom; we return blanks if unavailable.
    """
    si = frappe.get_list(
        "Sales Invoice",
        fields=["name as bill_no", "posting_date as date", "posting_time as time", "customer", "customer_name",
                "grand_total as net", "total_taxes_and_charges as vat", "rounded_total as paid", "is_return",
                "pos_profile", "owner as cashier", "docstatus"],
        limit_page_length=limit,
        order_by="posting_date desc, posting_time desc",
    )
    out = []
    for s in si:
        out.append({
            "sales": s.grand_total,
            "hold_remarks": "",
            "customer_id": s.customer,
            "default_disc_stock": "",
            "stock_discount": "",
            "discount_percent": "",
            "is_hold": 0,
            "max_disc_stock": "",
            "pay_type": "",
            "service_discount": "",
            "customer_name": s.customer_name,
            "default_disc_service": "",
            "time": s.time,
            "lift_code": "",
            "discount": "",
            "telephone_no": "",
            "vat": s.vat,
            "max_disc_service": "",
            "net": s.net,
            "is_open": 1 if s.docstatus == 0 else 0,
            "paid": s.paid,
            "change": "",
            "loyalty_card_no": "",
            "wa_expdate": "",
            "customer": s.customer,
            "loyalty_card_name": "",
            "r_bill_points": "",
            "bill_points": "",
            "closing_id": "",
            "shift_closing_id": "",
            "fc_used": "",
            "return_no": s.bill_no if s.is_return else "",
            "bill_no": s.bill_no,
            "date": s.date,
            "disc_voucher_no": "",
            "station_no": s.pos_profile,
            "work_order_no": "",
            "fc_no": "",
            "is_additional_no": "",
            "cashier": s.cashier,
            "next_service": "",
            "salespoint": "",
            "table_no": "",
            "vehicle_no": "",
            "model_no": "",
            "time_in": "",
            "make": "",
            "mileage": "",
            "mobile_no": "",
            "customer2": s.customer,
            "customer_name2": s.customer_name,
        })
    return out

@frappe.whitelist()
def validate_coupon(vehicle_no: str, coupon_no: str):
    """
    Validate a coupon. For MVP, just return staff info + points.
    Later: Check against Coupon doctype and mark redeemed.
    """
    staff_code = frappe.session.user
    staff_name = frappe.db.get_value("User", staff_code, "full_name") or staff_code

    exists = frappe.db.exists("Coupon", {"name": coupon_no, "vehicle_no": vehicle_no})
    if not exists:
        return {"staff_code": staff_code, "staff_name": staff_name, "points": 0, "saved": False}

    frappe.db.set_value("Coupon", coupon_no, "validated", 1)
    frappe.db.commit()

    return {"staff_code": staff_code, "staff_name": staff_name, "points": 10, "saved": True}

@frappe.whitelist()
def vehicles_master_list(limit: int = 500):
    """
    Fetch vehicle master records with required fields.
    Assumes you have a custom Doctype `Vehicle Master`.
    """
    rows = frappe.get_list(
        "Vehicle Master",
        fields=[
            "name as trans_no",
            "vehicle_no",
            "customer",
            "model",
            "chasis_no",
            "color",
            "reg_no",
            "warranty",
            "odometer",
            "date",
            "engine",
            "body",
            "year",
            "division",
            "address",
            "po_box",
            "city",
            "tin",
            "tel_mob",
            "office",
            "home",
            "bill_to",
            "stationed",
            "loc",
            "sales_rep",
            "comments",
            "owner as created_by",
            "creation as on",
            "modified_by as modified",
            "modified as last_modified",
        ],
        limit_page_length=limit,
        order_by="modified desc",
    )
    return rows
