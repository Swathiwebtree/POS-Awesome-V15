import frappe
from frappe.utils.data import nowdate
from frappe import _
from frappe.utils import getdate, flt

from frappe.model.document import Document


class VehicleMaster(Document):
    def before_insert(self):
        if not self.trans_no:
            # auto generate if empty
            self.trans_no = frappe.model.naming.make_autoname("TRANS-.#####")


# ----------------------------
# TRANSACTIONS MODULE
# ----------------------------


@frappe.whitelist()
def get_items():
    # Return simple items list for browse — adapt to your real item doctype
    items = frappe.get_all(
        "Item",
        filters={"disabled": 0},
        fields=["item_code", "item_name", "standard_rate as price", "item_group as category"],
        limit_page_length=200,
    )
    return items


@frappe.whitelist()
def get_vehicle_service_list():
    return frappe.get_all("Vehicle Service", fields=["name", "service_code", "description", "price"])


@frappe.whitelist()
def get_open_work_orders():
    """Fetch all open work orders"""
    return frappe.get_all(
        "Work Order",
        filters={"status": "Open"},
        fields=[
            "name",
            "vehicle_no",
            "customer",
            "amount",
            "status",
            "work_order_date",
            "sales_person",
            "next_service_date",
        ],
        order_by="creation desc",
    )


@frappe.whitelist()
def apply_coupon(order_no, coupon_code):
    wo = frappe.get_doc("Work Order", order_no)
    wo.discount += wo.net_total * 0.10
    wo.save(ignore_permissions=True)
    frappe.db.commit()
    return get_work_order_details(order_no)


@frappe.whitelist()
def get_vehicle_history(vehicle_no):
    """Fetch all work orders for a vehicle"""
    return frappe.get_all(
        "Work Order",
        filters={"vehicle_no": vehicle_no},
        fields=["name", "work_order_date", "status", "amount", "net_total"],
        order_by="work_order_date desc",
    )


@frappe.whitelist()
def get_service_issue_list():
    return frappe.get_all(
        "Service Issue Note",
        fields=["name", "issue_id", "vehicle", "customer", "status", "priority", "service_date"],
        order_by="creation desc",
    )


@frappe.whitelist(allow_guest=True)
def create_service_issue_note(data):
    data = json.loads(data) if isinstance(data, str) else data
    doc = frappe.new_doc("Service Issue Note")
    doc.update(data)
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return "success"


# @frappe.whitelist()
# def get_service_issue_list():
#     """Fetch service issues"""
#     return frappe.get_all("Service Issue", fields=["name", "issue_code", "description", "status"])


@frappe.whitelist()
def get_work_order_details(order_no):
    """Get full details of a work order"""
    wo = frappe.get_doc("Work Order", order_no)

    items = []
    for item in wo.items:
        items.append(
            {
                "item_code": item.item_code,
                "description": item.description,
                "qty": item.qty,
                "rate": item.rate,
                "amount": item.amount,
                "vat": getattr(item, "tax_rate", 0),
            }
        )

    customer_info = {}
    if wo.customer:
        customer_doc = frappe.get_doc("Customer", wo.customer)
        customer_info = {
            "name": customer_doc.customer_name,
            "mobile": customer_doc.mobile_no,
            "tin": getattr(customer_doc, "tin", ""),
            "address": getattr(customer_doc, "customer_address", ""),
        }

    return {
        "work_order": {
            "name": wo.name,
            "vehicle_no": wo.vehicle_no,
            "status": wo.status,
            "discount": wo.discount or 0,
            "amount": wo.amount,
            "net_total": wo.net_total,
            "items": items,
            "customer_info": customer_info,
            "next_service_date": getattr(wo, "next_service_date", None),
        }
    }


@frappe.whitelist()
def add_item_to_order(order_no, item_code, qty, rate=None):
    """Add item to work order"""
    wo = frappe.get_doc("Work Order", order_no)
    item_rate = rate or frappe.get_value("Item", item_code, "standard_rate") or 0
    wo.append("items", {"item_code": item_code, "qty": float(qty), "rate": float(item_rate)})
    wo.save(ignore_permissions=True)
    frappe.db.commit()
    return get_work_order_details(order_no)


@frappe.whitelist()
def update_item_quantity(order_no, item_code, qty):
    """Update quantity of item"""
    wo = frappe.get_doc("Work Order", order_no)
    for item in wo.items:
        if item.item_code == item_code:
            item.qty = float(qty)
            break
    wo.save(ignore_permissions=True)
    frappe.db.commit()
    return get_work_order_details(order_no)


@frappe.whitelist()
def remove_item_from_order(order_no, item_code):
    """Remove item from order"""
    wo = frappe.get_doc("Work Order", order_no)
    wo.items = [item for item in wo.items if item.item_code != item_code]
    wo.save(ignore_permissions=True)
    frappe.db.commit()
    return get_work_order_details(order_no)


@frappe.whitelist()
def save_work_order(
    work_order=None, vehicle=None, customer=None, staff_code=None, staff_name=None, items=None, discount=0
):
    """
    Create or update a Vehicle Service Work Order (simple generic implementation).
    items expected as list of dicts: [{ item_code, qty, price }]
    """
    if not work_order:
        # generate a name if you want
        work_order = make_autoname("WO-.####")

    doc = None
    if frappe.db.exists("Vehicle Service Work Order", work_order):
        doc = frappe.get_doc("Vehicle Service Work Order", work_order)
        # clear and update items
        doc.items = []
    else:
        doc = frappe.get_doc({"doctype": "Vehicle Service Work Order", "name": work_order})

    doc.vehicle = vehicle
    doc.customer = customer
    doc.staff_code = staff_code
    doc.staff_name = staff_name
    doc.discount = discount

    # append items
    if items:
        # items may be JSON string if called from fetch; ensure list
        if isinstance(items, str):
            import json

            items = json.loads(items)
        for it in items:
            qty = it.get("qty", 1)
            price = it.get("price") or 0
            doc.append(
                "items",
                {
                    "item_code": it.get("item_code"),
                    "description": it.get("item_name") or it.get("description"),
                    "qty": qty,
                    "rate": price,
                },
            )

    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {"status": "ok", "work_order": doc.name}


@frappe.whitelist()
def get_items_from_barcode(barcode=None):
    if not barcode:
        return []
    # simple lookup on Item Barcode doctype or Item's barcode field
    ib = frappe.get_all(
        "Item Barcode", filters={"barcode": barcode}, fields=["parent as item_code"], limit_page_length=1
    )
    if ib:
        item_code = ib[0].item_code
        item = frappe.get_doc("Item", item_code)
        return [{"item_code": item.name, "item_name": item.item_name, "price": item.standard_rate}]
    # fallback: try item with barcode field
    item = (
        frappe.db.get_values(
            "Item", {"barcode": barcode}, ["name", "item_name", "standard_rate"], as_dict=True
        )
        or []
    )
    return item


@frappe.whitelist()
def get_quotation_list(customer=None, status=None):
    """Fetch all quotations, optionally filtered by customer or status"""
    filters = {}
    if customer:
        filters["customer"] = customer
    if status:
        filters["status"] = status

    return frappe.get_all(
        "Quotation",
        filters=filters,
        fields=["name", "customer", "transaction_date", "status", "grand_total", "currency"],
        order_by="transaction_date desc",
    )


# @frappe.whitelist()
# def get_petty_cash_transactions():
#     """
#     Fetch petty cash transactions with item details
#     """
#     transactions = frappe.get_all(
#         "Petty Cash",
#         fields=[
#             "name as pc_no",
#             "ref",
#             "station_id",
#             "posting_date as date",
#             "description",
#             "user_id",
#             "remarks",
#             "shift_closing_id",
#             "count_closing_id",
#             "day_closing_id",
#             "total",
#         ],
#         order_by="posting_date desc",
#     )

#     for txn in transactions:
#         # Fetch item details
#         txn["items"] = frappe.get_all(
#             "Petty Cash Item",
#             filters={"parent": txn.pc_no},
#             fields=[
#                 "account as ac_code",
#                 "account_name",
#                 "description",
#                 "amount",
#                 "division as div",
#                 "account_id",
#                 "date",
#                 "typ",
#                 "trans_no",
#                 "ref_no",
#                 "currency as cur",
#                 "paid_foreign",
#                 "paid_local",
#             ],
#         )
#     return transactions


@frappe.whitelist()
def get_sales_by_payment_list(from_date=None, to_date=None, payment_type=None):
    """
    Fetch sales filtered by payment type and date range.
    If no dates are provided, it fetches all records.
    """
    filters = ""
    if from_date and to_date:
        filters += f" WHERE posting_date BETWEEN '{from_date}' AND '{to_date}'"
    if payment_type:
        filters += f" {'AND' if filters else 'WHERE'} payment_type='{payment_type}'"

    return frappe.db.sql(
        f"""
        SELECT name as invoice_no, customer, posting_date as date,
               payment_type, paid_amount as amount
        FROM `tabPayment Entry`
        {filters}
        ORDER BY posting_date DESC
    """,
        as_dict=True,
    )


@frappe.whitelist()
def get_redeemed_coupon_points_list(start_date=None, end_date=None, staff=None, vehicle_no=None):
    """
    Fetch redeemed coupon points for a given filter.
    Filters:
        start_date: str (YYYY-MM-DD)
        end_date: str (YYYY-MM-DD)
        staff: str (Staff Code)
        vehicle_no: str (Vehicle Number)
    """
    filters = {}

    if start_date:
        filters["date"] = [">=", start_date]
    if end_date:
        if "date" in filters:
            filters["date"].append(["<=", end_date])
        else:
            filters["date"] = ["<=", end_date]
    if staff:
        filters["staff_code"] = staff
    if vehicle_no:
        filters["vehicle_no"] = vehicle_no

    try:
        redeemed_points = frappe.get_all(
            "Coupon Sales Point",
            filters=filters,
            fields=["staff_code", "staff_name", "date", "points", "terminal", "vehicle_no"],
            order_by="date desc",
        )
        return redeemed_points
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error fetching redeemed coupon points"))
        return {"error": str(e)}


@frappe.whitelist()
def get_coupon_sales_point_list(from_date=None, to_date=None, lift_employee=None):
    """
    Returns the list of coupon sales points based on filters:
    - from_date: Start date
    - to_date: End date
    - lift_employee: Employee code handling the transaction
    """
    filters = {}

    if from_date:
        filters["date"] = [">=", from_date]
    if to_date:
        filters["date"] = filters.get("date", []) + ["<=", to_date]
    if lift_employee:
        filters["lift_employee"] = lift_employee

    try:
        coupon_points = frappe.get_all(
            "Coupon Sales Point",
            filters=filters,
            fields=["staff_code", "staff_name", "date", "points", "terminal", "vehicle_no"],
            order_by="date desc",
        )
        return coupon_points
    except Exception as e:
        frappe.throw(_("Error fetching coupon sales points: {0}").format(str(e)))


@frappe.whitelist()
def apply_discount(order_no, discount):
    """Apply discount to work order"""
    wo = frappe.get_doc("Work Order", order_no)
    wo.discount = float(discount)
    wo.save(ignore_permissions=True)
    frappe.db.commit()
    return get_work_order_details(order_no)


@frappe.whitelist()
def settle_order(order_no, payment_info):
    """Settle work order"""
    wo = frappe.get_doc("Work Order", order_no)
    wo.payment_info = frappe.as_json(payment_info)
    wo.status = "Paid"
    wo.paid_amount = sum([p.get("amount", 0) for p in payment_info])
    wo.save(ignore_permissions=True)
    frappe.db.commit()
    return get_work_order_details(order_no)


@frappe.whitelist()
def hold_order(order_no):
    """Hold work order"""
    wo = frappe.get_doc("Work Order", order_no)
    wo.status = "Hold"
    wo.save(ignore_permissions=True)
    frappe.db.commit()
    return get_work_order_details(order_no)


@frappe.whitelist()
def void_order(order_no):
    if not order_no:
        frappe.throw(_("Order number required"))
    if not frappe.db.exists("Vehicle Service Work Order", order_no):
        frappe.throw(_("Work order not found"))
    doc = frappe.get_doc("Vehicle Service Work Order", order_no)
    # business logic: set status or cancel
    doc.flags.ignore_permissions = True
    doc.db_set("status", "Cancelled")
    frappe.db.commit()
    return {"status": "cancelled", "order": order_no}


@frappe.whitelist()
def print_invoice(order_no):
    """Print invoice PDF"""
    return {"pdf": frappe.get_print("Work Order", order_no)}


@frappe.whitelist()
def get_vehicle_master(vehicle_no=None):
    """Fetch vehicle master details"""
    filters = {"vehicle_no": vehicle_no} if vehicle_no else {}
    return frappe.get_all(
        "Vehicle Master",
        filters=filters,
        fields=[
            "name",
            "vehicle_no",
            "customer",
            "model",
            "chasis_no",
            "color",
            "reg_no",
            "warranty",
            "odometer",
            "engine",
            "body",
            "year",
            "division",
            "address",
            "mobile_no",
            "tin",
        ],
    )


@frappe.whitelist()
def get_vehicle_details(vehicle_no=None):
    """
    Fetch detailed information for a vehicle including customer, model, mileage,
    next service date, and vehicle history.

    :param vehicle_no: Vehicle number to fetch details for
    :return: dict containing vehicle and customer details, and vehicle history
    """
    if not vehicle_no:
        frappe.throw(_("Vehicle number is required"))

    # Fetch vehicle master details
    vehicle = frappe.get_all(
        "Vehicle Master",
        filters={"vehicle_no": vehicle_no},
        fields=[
            "vehicle_no",
            "model",
            "make",
            "color",
            "chasis_no",
            "reg_no",
            "odometer",
            "warranty",
            "year",
            "division",
            "customer",
        ],
        limit_page_length=1,
    )

    if not vehicle:
        return {"message": _("Vehicle not found"), "data": {}}

    vehicle = vehicle[0]

    # Fetch customer details
    customer = {}
    if vehicle.customer:
        customer = frappe.get_all(
            "Customer",
            filters={"name": vehicle.customer},
            fields=["name", "customer_name", "tin", "email", "mobile_no", "address"],
            limit_page_length=1,
        )
        customer = customer[0] if customer else {}

    # Fetch vehicle history (last 5 transactions)
    vehicle_history = frappe.get_all(
        "Vehicle History",
        filters={"vehicle_no": vehicle_no},
        fields=["bill_no", "date", "item_code", "item_name", "amount", "points", "staff_name", "lift_code"],
        order_by="date desc",
        limit_page_length=5,
    )

    return {"vehicle": vehicle, "customer": customer, "history": vehicle_history}


@frappe.whitelist()
def browse_items(category=None):
    """Fetch items for sale based on category"""
    filters = {"item_group": category} if category else {}
    return frappe.get_all(
        "Item",
        filters=filters,
        fields=[
            "item_code",
            "item_name",
            "description",
            "standard_rate",
            "vat_rate",
            "barcode",
            "unit_of_measure",
        ],
    )


@frappe.whitelist()
def get_petty_cash_transactions():
    """Fetch all Petty Cash entries with items"""
    petty_cash_entries = frappe.get_all(
        "Petty Cash",
        fields=[
            "name as pc_no",
            "ref",
            "station_id",
            "date",
            "description",
            "user_id",
            "remarks",
            "shift_closing_id",
            "count_closing_id",
            "day_closing_id",
            "total",
        ],
        order_by="date desc",
        limit_page_length=200,
    )

    for entry in petty_cash_entries:
        items = frappe.get_all(
            "Petty Cash Item",
            filters={"parent": entry.pc_no},
            fields=[
                "ac_code",
                "account_name",
                "description",
                "amount",
                "division",
                "account_id",
                "date",
                "typ",
                "trans_no",
                "ref_no",
                "currency",
                "paid_foreign",
                "paid_local",
            ],
            order_by="idx",
        )
        entry["items"] = items

    return petty_cash_entries


@frappe.whitelist()
def add_petty_cash(pc_data, items_data):
    """
    Add new Petty Cash entry with items
    pc_data: dict with main fields
    items_data: list of dicts for child table
    """
    import json

    pc_data = json.loads(pc_data)
    items_data = json.loads(items_data)

    doc = frappe.get_doc({"doctype": "Petty Cash", **pc_data, "items": items_data})
    doc.insert()
    frappe.db.commit()
    return {"message": "Petty Cash added successfully", "pc_no": doc.name}


@frappe.whitelist()
def get_receipt_voucher():
    """List receipt vouchers"""
    return frappe.get_all(
        "Receipt Voucher", fields=["name", "customer", "date", "amount", "status", "division"]
    )


@frappe.whitelist(allow_guest=True)
def get_list():
    # Fetch all items
    items = frappe.get_all(
        "Item",
        fields=[
            "name as item_code",
            "item_name",
            "barcode",
            "supplier",
            "stock_uom as unit",
            "default_warehouse as location",
            "selling_price",
            "vat_rate as vat_price",
            "scale",
            "stock_balance",
        ],
    )

    # Fetch price levels
    price_levels = frappe.get_all(
        "Item Price",
        fields=[
            "name as price_id",
            "price_list as price_level",
            "item_code as barcode",
            "price_list_rate as price",
            "price_list_rate_with_tax as price_vat",
        ],
    )

    # Fetch stock in hand
    stock_in_hand = frappe.get_all(
        "Bin", fields=["warehouse as location_name", "actual_qty as balance", "shelf_no"]
    )

    return {"items": items, "price_levels": price_levels, "stock_in_hand": stock_in_hand}


# ----------------------------
# INVENTORY MODULE
# ----------------------------


@frappe.whitelist()
def get_material_request_list(start_date=None, end_date=None, supplier=None, division=None):
    """
    API to fetch Material Request list
    Filters:
    - start_date: filter by MR creation date (YYYY-MM-DD)
    - end_date: filter by MR creation date (YYYY-MM-DD)
    - supplier: filter by supplier name
    - division: filter by division
    """
    filters = {}

    if start_date:
        filters["date"] = [">=", start_date]
    if end_date:
        filters.setdefault("date", []).append(["<=", end_date])
    if supplier:
        filters["supplier"] = supplier
    if division:
        filters["division"] = division

    material_requests = frappe.get_all(
        "Material Request",
        filters=filters,
        fields=[
            "name as mr_no",
            "date",
            "requested_by",
            "division",
            "sales_rep",
            "supplier",
            "station_id",
            "location",
        ],
        order_by="date desc",
    )

    result = []
    for mr in material_requests:
        items = frappe.get_all(
            "Material Request Item",
            filters={"parent": mr.mr_no},
            fields=[
                "barcode",
                "item_code",
                "item_name",
                "description",
                "qty",
                "unit",
                "factor",
                "price",
                "amount",
            ],
        )
        mr_dict = mr.copy()
        mr_dict["items"] = items
        result.append(mr_dict)

    return result


@frappe.whitelist()
def get_grn_list(start_date=None, end_date=None, supplier=None, item_code=None):
    """
    Returns a list of Goods Receipt Notes (GRNs) with optional filters.
    Args:
        start_date (str): Filter GRNs from this date (YYYY-MM-DD)
        end_date (str): Filter GRNs up to this date (YYYY-MM-DD)
        supplier (str): Filter by supplier name
        item_code (str): Filter GRNs containing this item code
    Returns:
        list: List of GRNs with details
    """
    filters = {}
    if start_date:
        filters["posting_date"] = (">=", start_date)
    if end_date:
        filters["posting_date"] = ("<=", end_date)
    if supplier:
        filters["supplier"] = supplier

    grn_list = frappe.get_all(
        "Purchase Receipt",
        filters=filters,
        fields=[
            "name",
            "posting_date",
            "supplier",
            "supplier_name",
            "total_qty",
            "grand_total",
            "company",
            "status",
        ],
        order_by="posting_date desc",
    )

    # Filter by item code if provided
    if item_code:
        filtered_grns = []
        for grn in grn_list:
            items = frappe.get_all(
                "Purchase Receipt Item",
                filters={"parent": grn.name, "item_code": item_code},
                fields=["item_code", "item_name", "qty", "rate", "amount"],
            )
            if items:
                grn["items"] = items
                filtered_grns.append(grn)
        grn_list = filtered_grns

    return grn_list


@frappe.whitelist()
def get_issue_note_list(start_date=None, end_date=None, location=None, status=None):
    """
    Fetch a list of Issue Notes within a date range, optionally filtered by location and status.
    """
    filters = {}
    if start_date:
        filters["posting_date"] = [">=", start_date]
    if end_date:
        filters["posting_date"] = ["<=", end_date]
    if location:
        filters["location"] = location
    if status:
        filters["status"] = status

    issue_notes = frappe.get_all(
        "Issue Note",
        filters=filters,
        fields=[
            "name",
            "posting_date",
            "type",
            "division",
            "location",
            "lpo",
            "station_id",
            "debit_account",
            "customer",
            "sales_rep",
            "status",
        ],
        order_by="posting_date desc",
    )

    # Add item details for each Issue Note
    for note in issue_notes:
        note["items"] = frappe.get_all(
            "Issue Note Item",
            filters={"parent": note["name"]},
            fields=[
                "barcode",
                "item_code",
                "item_name",
                "description",
                "qty",
                "unit",
                "factor",
                "net_qty",
                "location",
                "job",
                "division",
            ],
        )

    return issue_notes


@frappe.whitelist()
def get_transfer_in_list(from_date=None, to_date=None, transfer_from=None, transfer_to=None, station_id=None):
    """
    Fetch Transfer In records based on filters.

    :param from_date: Start date filter
    :param to_date: End date filter
    :param transfer_from: Source location filter
    :param transfer_to: Destination location filter
    :param station_id: POS station filter
    :return: List of Transfer In records
    """
    filters = {}

    if from_date:
        filters["date"] = [">=", from_date]
    if to_date:
        filters["date"] = ["<=", to_date]
    if transfer_from:
        filters["transfer_from"] = transfer_from
    if transfer_to:
        filters["transfer_to"] = transfer_to
    if station_id:
        filters["station_id"] = station_id

    transfer_in_list = frappe.get_all(
        "Transfer In",
        filters=filters,
        fields=[
            "name",
            "trans_no",
            "t_out_no",
            "transfer_from",
            "transfer_to",
            "date",
            "station_id",
            "div",
            "user_id",
        ],
        order_by="date desc",
    )

    # Optional: include item details for each transfer
    for transfer in transfer_in_list:
        items = frappe.get_all(
            "Transfer In Item",
            filters={"parent": transfer.name},
            fields=["item_code", "item_name", "qty", "unit", "balance", "source_no"],
        )
        transfer["items"] = items

    return transfer_in_list


@frappe.whitelist()
def get_transfer_out_list(start_date=None, end_date=None, location=None):
    """
    Get list of Transfer Out records filtered by date range and location
    """
    filters = {}

    if start_date:
        filters["date"] = [">=", start_date]
    if end_date:
        filters.setdefault("date", ["<=", end_date])
    if location:
        filters["location"] = location

    transfer_outs = frappe.get_all(
        "Transfer Out",
        filters=filters,
        fields=[
            "name",
            "trans_no",
            "transfer_from",
            "transfer_to",
            "date",
            "station_id",
            "division",
            "user_id",
        ],
        order_by="date desc",
    )

    result = []
    for t in transfer_outs:
        item_details = frappe.get_all(
            "Transfer Out Item",
            filters={"parent": t.name},
            fields=["barcode", "item_code", "item_name", "quantity", "unit", "balance"],
        )
        t["items"] = item_details
        result.append(t)

    return result


@frappe.whitelist()
def get_physical_count_list(filters=None):
    """
    API to fetch Physical Count records for the Inventory module in LAZER POS.
    :param filters: JSON string with filter parameters like date range, station, shift, etc.
    :return: List of Physical Count records
    """
    import json

    if filters:
        filters = json.loads(filters)
    else:
        filters = {}

    conditions = []
    values = []

    if filters.get("from_date"):
        conditions.append("pc.date >= %s")
        values.append(filters["from_date"])
    if filters.get("to_date"):
        conditions.append("pc.date <= %s")
        values.append(filters["to_date"])
    if filters.get("station_id"):
        conditions.append("pc.station_id = %s")
        values.append(filters["station_id"])
    if filters.get("shift_closing_id"):
        conditions.append("pc.shift_closing_id = %s")
        values.append(filters["shift_closing_id"])

    condition_sql = " AND ".join(conditions)
    if condition_sql:
        condition_sql = "WHERE " + condition_sql

    query = f"""
        SELECT
            pc.name as physical_count_id,
            pc.date,
            pc.station_id,
            pc.location,
            pc.shift_closing_id,
            pc.user_id
        FROM `tabPhysical Count` pc
        {condition_sql}
        ORDER BY pc.date DESC
        LIMIT 100
    """

    data = frappe.db.sql(query, values, as_dict=True)
    return data


@frappe.whitelist()
def get_production_form_list(start_date=None, end_date=None, production_type=None, location=None):
    """
    API to fetch Production Form list.
    :param start_date: Filter records from this date (YYYY-MM-DD)
    :param end_date: Filter records up to this date (YYYY-MM-DD)
    :param production_type: Optional filter by type of production
    :param location: Optional filter by location
    :return: List of production forms with relevant details
    """

    filters = {}
    if start_date:
        filters["creation"] = [">=", start_date]
    if end_date:
        filters["creation"] = ["<=", end_date]
    if production_type:
        filters["production_type"] = production_type
    if location:
        filters["location"] = location

    production_forms = frappe.get_all(
        "Production Form",
        filters=filters,
        fields=[
            "name",
            "production_type",
            "date",
            "location",
            "item",
            "qty",
            "status",
            "created_by",
            "creation",
        ],
        order_by="creation desc",
    )

    result = []
    for pf in production_forms:
        result.append(
            {
                "name": pf.name,
                "production_type": pf.production_type,
                "date": pf.date,
                "location": pf.location,
                "item": pf.item,
                "qty": flt(pf.qty),
                "status": pf.status,
                "created_by": pf.created_by,
                "creation": pf.creation,
            }
        )

    return result


@frappe.whitelist()
def get_damage_memo_list(start_date=None, end_date=None, location=None, station_id=None):
    """
    Fetch a list of Damage Memo records.
    Filters:
    - start_date, end_date: Date range of the damage memos
    - location: Optional filter by warehouse/location
    - station_id: Optional filter by POS station
    """
    filters = {}

    if start_date:
        filters["date"] = [">=", start_date]
    if end_date:
        filters.setdefault("date", [None, None])[1] = end_date
    if location:
        filters["location"] = location
    if station_id:
        filters["station_id"] = station_id

    damage_memos = frappe.get_all(
        "Damage Memo",
        filters=filters,
        fields=[
            "name",
            "date",
            "location",
            "station_id",
            "item_code",
            "item_name",
            "quantity",
            "unit",
            "remarks",
            "created_by",
            "modified",
            "last_modified",
        ],
        order_by="date desc",
    )

    return damage_memos


# ----------------------------
# REPORTS MODULE
# ----------------------------


# ==========================================================
# 2.1 Bills Listing – Work Order
# ==========================================================
@frappe.whitelist()
def get_bills_listing_work_order(filters=None):
    """
    Filters:
        from_date, to_date, work_order_no
    """
    filters = frappe.parse_json(filters) if filters else {}

    query = """
        SELECT
            work_order_no,
            bill_no,
            date,
            payment_method,
            vehicle_no,
            total_amount,
            discount_amount,
            amount_after_discount,
            vat_amount,
            net_amount
        FROM `tabBills Listing Work Order`
        WHERE date BETWEEN %(from_date)s AND %(to_date)s
    """
    if filters.get("work_order_no"):
        query += " AND work_order_no = %(work_order_no)s"

    data = frappe.db.sql(query, filters, as_dict=True)
    return _with_totals(
        data, ["total_amount", "discount_amount", "amount_after_discount", "vat_amount", "net_amount"]
    )


# ==========================================================
# 2.2 Bills Listing – Vehicle
# ==========================================================
@frappe.whitelist()
def get_bills_listing_vehicle(filters=None):
    """
    Filters:
        from_date, to_date, vehicle_no
    """
    filters = frappe.parse_json(filters) if filters else {}

    query = """
        SELECT
            vehicle_no,
            bill_no,
            work_order_no,
            date,
            payment_method,
            time_in,
            time_out,
            vehicle_count,
            total_amount,
            discount_amount,
            amount_after_discount,
            vat_amount,
            net_amount
        FROM `tabBills Listing Vehicle`
        WHERE date BETWEEN %(from_date)s AND %(to_date)s
    """
    if filters.get("vehicle_no"):
        query += " AND vehicle_no = %(vehicle_no)s"

    data = frappe.db.sql(query, filters, as_dict=True)
    return _with_totals(
        data,
        [
            "vehicle_count",
            "total_amount",
            "discount_amount",
            "amount_after_discount",
            "vat_amount",
            "net_amount",
        ],
    )


# ==========================================================
# 2.3 Payment Summary
# ==========================================================
@frappe.whitelist()
def get_payment_summary(filters=None):
    """
    Filters:
        from_date, to_date, payment_type
    """
    filters = frappe.parse_json(filters) if filters else {}

    query = """
        SELECT
            date,
            transaction_no,
            payment_code,
            amount
        FROM `tabPayment Summary`
        WHERE date BETWEEN %(from_date)s AND %(to_date)s
    """
    if filters.get("payment_type"):
        query += " AND payment_code = %(payment_type)s"

    data = frappe.db.sql(query, filters, as_dict=True)
    return _with_totals(data, ["amount"])


# ==========================================================
# 2.4 Stock In Hand
# ==========================================================
@frappe.whitelist()
def get_stock_in_hand(filters=None):
    """
    Filters:
        warehouse (optional)
    """
    filters = frappe.parse_json(filters) if filters else {}

    query = """
        SELECT
            item_code,
            item_name,
            unit,
            warehouse,
            quantity,
            valuation_rate,
            amount
        FROM `tabStock In Hand`
    """
    if filters.get("warehouse"):
        query += " WHERE warehouse = %(warehouse)s"

    data = frappe.db.sql(query, filters, as_dict=True)
    return _with_totals(data, ["quantity", "amount"])


# ==========================================================
# 2.5 Stock Sales
# ==========================================================
@frappe.whitelist()
def get_stock_sales(filters=None):
    """
    Filters:
        from_date, to_date, department, main_category,
        sub_category, stock_item_from, stock_item_to, stock_type, group_by
    """
    filters = frappe.parse_json(filters) if filters else {}

    query = """
        SELECT
            posting_date AS date,
            sales_type,
            department,
            main_category,
            sub_category,
            stock_item,
            quantity,
            amount,
            discount,
            net_sales
        FROM `tabStock Sales`
        WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s
    """

    # Optional filters
    if filters.get("department"):
        query += " AND department = %(department)s"
    if filters.get("main_category"):
        query += " AND main_category = %(main_category)s"
    if filters.get("sub_category"):
        query += " AND sub_category = %(sub_category)s"
    if filters.get("stock_type"):
        query += " AND stock_type = %(stock_type)s"
    if filters.get("stock_item_from") and filters.get("stock_item_to"):
        query += " AND stock_item BETWEEN %(stock_item_from)s AND %(stock_item_to)s"

    # Optional grouping
    if filters.get("group_by"):
        query += f" ORDER BY {filters['group_by'].lower()}"

    data = frappe.db.sql(query, filters, as_dict=True)
    return _with_totals(data, ["quantity", "amount", "discount", "net_sales"])


# ==========================================================
# 2.6 Stock Points
# ==========================================================
@frappe.whitelist()
def get_stock_points(filters=None):
    """
    Filters:
        from_date, to_date, from_staff, to_staff, from_terminal, to_terminal, report_group_by
    """
    filters = frappe.parse_json(filters) if filters else {}

    query = """
        SELECT
            date,
            staff,
            terminal,
            item,
            quantity,
            amount,
            discount,
            net_sales
        FROM `tabStock Points Item`
        WHERE date BETWEEN %(from_date)s AND %(to_date)s
    """

    if filters.get("from_staff") and filters.get("to_staff"):
        query += " AND staff BETWEEN %(from_staff)s AND %(to_staff)s"
    if filters.get("from_terminal") and filters.get("to_terminal"):
        query += " AND terminal BETWEEN %(from_terminal)s AND %(to_terminal)s"

    if filters.get("report_group_by"):
        query += f" ORDER BY {filters['report_group_by'].lower()}"

    data = frappe.db.sql(query, filters, as_dict=True)
    return _with_totals(data, ["quantity", "amount", "discount", "net_sales"])


# ==========================================================
# 2.7 Sales Points
# ==========================================================
@frappe.whitelist()
def get_sales_points(filters=None):
    """
    Filters:
        from_date, to_date, staff, terminal
    """
    filters = frappe.parse_json(filters) if filters else {}

    query = """
        SELECT
            date,
            staff,
            terminal,
            total_sales,
            total_discount,
            total_net_sales
        FROM `tabSales Points`
        WHERE date BETWEEN %(from_date)s AND %(to_date)s
    """
    if filters.get("staff"):
        query += " AND staff = %(staff)s"
    if filters.get("terminal"):
        query += " AND terminal = %(terminal)s"

    data = frappe.db.sql(query, filters, as_dict=True)
    return _with_totals(data, ["total_sales", "total_discount", "total_net_sales"])


# ==========================================================
# 2.8 Sales Transaction
# ==========================================================
@frappe.whitelist()
def get_sales_transaction(filters=None):
    """
    Filters:
        from_date, to_date, sales_type
    """
    filters = frappe.parse_json(filters) if filters else {}

    query = """
        SELECT
            date,
            transaction_no,
            sales_type,
            amount,
            discount,
            net_sales
        FROM `tabSales Transaction`
        WHERE date BETWEEN %(from_date)s AND %(to_date)s
    """
    if filters.get("sales_type"):
        query += " AND sales_type = %(sales_type)s"

    data = frappe.db.sql(query, filters, as_dict=True)
    return _with_totals(data, ["amount", "discount", "net_sales"])


# ==========================================================
# Common Utility Function
# ==========================================================
def _with_totals(data, numeric_fields):
    """Helper to include totals for numeric fields."""
    totals = {}
    for field in numeric_fields:
        totals[field] = sum((d.get(field) or 0) for d in data)
    return {"data": data, "totals": totals}


@frappe.whitelist()
def get_loyalty_customer(filters=None):
    """
    Get Loyalty Customer List

    Args:
        filters (dict, optional): Filters like customer_name, card_no, active, etc.

    Returns:
        list: List of loyalty customers matching filters
    """
    filters = filters or {}

    query_filters = []

    if filters.get("customer_name"):
        query_filters.append(f"customer_name LIKE '%{filters['customer_name']}%'")
    if filters.get("card_no"):
        query_filters.append(f"loyalty_card_no = '{filters['card_no']}'")
    if filters.get("active") is not None:
        query_filters.append(f"active = {int(filters['active'])}")

    where_clause = " AND ".join(query_filters)
    if where_clause:
        where_clause = "WHERE " + where_clause

    sql_query = f"""
        SELECT
            name AS customer_id,
            customer_name,
            loyalty_card_no,
            expiry_date,
            points_balance,
            active
        FROM `tabLoyalty Customer`
        {where_clause}
        ORDER BY customer_name ASC
        LIMIT 100
    """

    return frappe.db.sql(sql_query, as_dict=True)


@frappe.whitelist()
def get_loyalty_points(customer):
    """
    Calculates the current available loyalty points for a given customer.

    :param customer: The Customer ID (string).
    :returns: A dictionary containing the total available points.
    """
    if not customer:
        frappe.throw("Customer ID is required.")

    # Get the Loyalty Program linked to the customer
    # This assumes a standard ERPNext setup where a Customer can be linked to a Loyalty Program
    loyalty_program = frappe.db.get_value("Customer", customer, "loyalty_program")

    if not loyalty_program:
        # Check if any Loyalty Program is set as default/global
        loyalty_program = frappe.db.get_value("Loyalty Program", {"is_active": 1, "is_default": 1}, "name")

    if not loyalty_program:
        # If no program is found, return 0 points
        return {"points": 0}

    # Calculate the total points balance
    # Total points earned minus total points redeemed for the given customer and program
    total_points = (
        frappe.db.get_value(
            "Loyalty Point Entry",
            {"customer": customer, "loyalty_program": loyalty_program},
            "SUM(loyalty_points)",
        )
        or 0
    )

    return {"points": total_points}


@frappe.whitelist()
def validate_loyalty_coupon(vehicle_no: str, coupon_no: str, staff_code: str = None):
    """
    Validate a loyalty coupon for a specific vehicle.

    :param vehicle_no: Vehicle number associated with the coupon.
    :param coupon_no: Loyalty coupon number to validate.
    :param staff_code: Optional staff code performing the validation.
    :return: Dict with validation status, points, and related details.
    """
    if not vehicle_no or not coupon_no:
        frappe.throw(_("Vehicle number and coupon number are required"))

    # Fetch vehicle details
    vehicle = frappe.get_all(
        "Vehicles Master", filters={"vehicle_no": vehicle_no}, fields=["name", "customer", "model"]
    )

    if not vehicle:
        return {"status": "error", "message": _("Vehicle not found")}

    vehicle = vehicle[0]

    # Fetch the coupon record
    coupon = frappe.get_all(
        "Redeemed Coupon Points",
        filters={"coupon_no": coupon_no, "vehicle_no": vehicle_no},
        fields=["name", "points", "status", "redeemed_on"],
    )

    if not coupon:
        return {"status": "error", "message": _("Coupon not valid for this vehicle")}

    coupon = coupon[0]

    if coupon.get("status") == "Redeemed":
        return {"status": "error", "message": _("Coupon already redeemed")}

    # Optionally record staff validation
    if staff_code:
        frappe.db.set_value("Redeemed Coupon Points", coupon["name"], "validated_by", staff_code)
        frappe.db.set_value("Redeemed Coupon Points", coupon["name"], "validated_on", frappe.utils.now())

    return {
        "status": "success",
        "vehicle": vehicle,
        "coupon_no": coupon_no,
        "points": coupon.get("points"),
        "message": _("Coupon is valid and can be redeemed"),
    }


@frappe.whitelist()
def add_service(work_order, vehicle_no, service_items, staff_code, payment_method=None):
    """
    Add services/products to a Work Order.

    Args:
        work_order (str): Work Order number
        vehicle_no (str): Vehicle number
        service_items (list of dict): List of services/items, each dict containing:
            - item_code (str)
            - qty (float)
            - price (float)
        staff_code (str): Code of the staff adding the service
        payment_method (str, optional): Payment method if applicable

    Returns:
        dict: Status message and updated Work Order info
    """
    try:
        # Validate work order
        wo_doc = frappe.get_doc("Work Order", work_order)
        if not wo_doc:
            return {"status": "error", "message": _("Work Order not found")}

        # Validate vehicle
        vehicle_doc = frappe.get_doc("Vehicle", vehicle_no)
        if not vehicle_doc:
            return {"status": "error", "message": _("Vehicle not found")}

        # Add services/items to Work Order
        for item in service_items:
            wo_doc.append(
                "items",
                {
                    "item_code": item.get("item_code"),
                    "qty": item.get("qty", 1),
                    "rate": item.get("price", 0.0),
                },
            )

        # Assign staff
        wo_doc.staff_code = staff_code

        # Save Work Order
        wo_doc.save()
        frappe.db.commit()

        # Optionally handle payment method
        if payment_method:
            # Add payment logic here if required
            pass

        return {"status": "success", "message": _("Services added successfully"), "work_order": work_order}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error in add_service"))
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def update_service_status(service_id, new_status):
    """
    Update the status of a specific service in the POS system.

    :param service_id: Name/ID of the service to update
    :param new_status: New status to set (e.g., 'Pending', 'Completed', 'Cancelled')
    :return: Dict containing success or error message
    """
    if not service_id or not new_status:
        return {"status": "error", "message": "Service ID and new status are required."}

    try:
        service_doc = frappe.get_doc("Lazer POS Service", service_id)
        service_doc.status = new_status
        service_doc.save(ignore_permissions=True)
        frappe.db.commit()
        return {"status": "success", "message": f"Service {service_id} updated to {new_status}"}
    except frappe.DoesNotExistError:
        return {"status": "error", "message": f"Service {service_id} does not exist."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_service_records(start_date=None, end_date=None, employee=None, vehicle_no=None, work_order=None):
    """
    API to fetch service records from Service Issue Notes and Vehicle Service.

    Optional Filters:
    - start_date: filter by service date (YYYY-MM-DD)
    - end_date: filter by service date (YYYY-MM-DD)
    - employee: filter by Lift Employee / Staff Code
    - vehicle_no: filter by Vehicle #
    - work_order: filter by Work Order #
    """

    filters = {}

    if start_date:
        filters["date"] = [">=", start_date]
    if end_date:
        filters["date"] = ["<=", end_date]
    if employee:
        filters["lift_employee"] = employee
    if vehicle_no:
        filters["vehicle_no"] = vehicle_no
    if work_order:
        filters["work_order"] = work_order

    service_records = frappe.get_all(
        "Service Issue Note",
        filters=filters,
        fields=[
            "name as service_note_no",
            "date",
            "work_order",
            "vehicle_no",
            "lift_employee",
            "model",
            "customer",
            "station_id",
        ],
        order_by="date desc",
    )

    for record in service_records:
        # Fetch item details linked to this service record
        items = frappe.get_all(
            "Service Item",
            filters={"parent": record.service_note_no},
            fields=["item_code", "item_name", "description", "qty", "unit", "price", "amount"],
        )
        record["items"] = items

    return service_records


# ----------------------------
# SYSTEM MODULE
# ----------------------------


@frappe.whitelist()
def get_users(filters=None, limit_start=0, limit_page_length=50):
    """
    API to fetch users for the POS system.
    Args:
        filters (dict, optional): Filtering options like {'role': 'Cashier', 'status': 'Active'}
        limit_start (int, optional): For pagination, start index
        limit_page_length (int, optional): For pagination, number of records
    Returns:
        list: List of user dictionaries with basic information
    """
    filters = filters or {}

    # Default filter to only fetch enabled users
    filters.setdefault("enabled", 1)

    # Query to fetch users
    users = frappe.get_all(
        "User",
        filters=filters,
        fields=[
            "name",
            "first_name",
            "last_name",
            "email",
            "roles",
            "enabled",
        ],
        limit_start=limit_start,
        limit_page_length=limit_page_length,
        order_by="first_name asc",
    )

    # Format roles into a list
    for user in users:
        if isinstance(user.get("roles"), str):
            user["roles"] = user["roles"].split(",")

    return users


# ----------------------------
# CASH COUNTING MODULE
# ----------------------------


@frappe.whitelist()
def get_cash_counting(start_date=None, end_date=None, station_id=None):
    """
    Fetch cash counting records for a given date range and station.
    :param start_date: Filter from date (optional)
    :param end_date: Filter to date (optional)
    :param station_id: Filter by POS station (optional)
    :return: List of cash counting records
    """
    filters = {}
    if start_date:
        filters["date"] = [">=", start_date]
    if end_date:
        filters["date"] = ["<=", end_date]
    if station_id:
        filters["station_id"] = station_id

    cash_countings = frappe.get_all(
        "Cash Counting",
        filters=filters,
        fields=[
            "name",
            "date",
            "shift",
            "station_id",
            "user",
            "opening_cash",
            "cash_in",
            "cash_out",
            "closing_cash",
            "remarks",
        ],
        order_by="date desc",
    )

    return cash_countings


# ----------------------------
# CASHIER OUT MODULE
# ----------------------------


@frappe.whitelist()
def get_cashier_out(from_date=None, to_date=None, cashier=None, station=None):
    """
    Returns a list of Cashier Out transactions filtered by date, cashier, and station.

    :param from_date: Start date for filtering (optional)
    :param to_date: End date for filtering (optional)
    :param cashier: Cashier ID or name (optional)
    :param station: POS station (optional)
    :return: List of Cashier Out records
    """
    filters = {}
    if from_date:
        filters["posting_date"] = [">=", from_date]
    if to_date:
        filters["posting_date"] = ["<=", to_date]
    if cashier:
        filters["cashier"] = cashier
    if station:
        filters["station"] = station

    # Fetch records from the Cashier Out DocType
    cashier_out_records = frappe.get_all(
        "Cashier Out",
        filters=filters,
        fields=["name", "posting_date", "cashier", "station", "total_amount", "remarks"],
        order_by="posting_date desc",
    )

    return cashier_out_records


# ----------------------------
# DAY END CLOSING MODULE
# ----------------------------


@frappe.whitelist()
def get_daily_summary(start_date=None, end_date=None, station_id=None):
    """
    Fetch daily summary of sales, payments, and cashier activities.
    """
    if not start_date or not end_date:
        frappe.throw(_("Please provide both start_date and end_date"))

    conditions = []
    if station_id:
        conditions.append(f"station_id = '{station_id}'")

    cond_str = " AND ".join(conditions)
    if cond_str:
        cond_str = " AND " + cond_str

    # Fetch sales summary
    sales_summary = frappe.db.sql(
        f"""
        SELECT 
            SUM(net_total) AS total_sales,
            SUM(discount_amount) AS total_discount,
            SUM(vat_amount) AS total_vat,
            SUM(paid_amount) AS total_paid,
            SUM(change_amount) AS total_change
        FROM `tabSales Invoice`
        WHERE posting_date BETWEEN '{start_date}' AND '{end_date}' {cond_str}
    """,
        as_dict=True,
    )

    # Fetch payment summary
    payment_summary = frappe.db.sql(
        f"""
        SELECT 
            payment_type,
            SUM(amount) AS total_amount
        FROM `tabPayment Entry`
        WHERE posting_date BETWEEN '{start_date}' AND '{end_date}' {cond_str}
        GROUP BY payment_type
    """,
        as_dict=True,
    )

    # Fetch cashier activity
    cashier_summary = frappe.db.sql(
        f"""
        SELECT 
            cashier,
            COUNT(name) AS transactions,
            SUM(paid_amount) AS total_collected
        FROM `tabSales Invoice`
        WHERE posting_date BETWEEN '{start_date}' AND '{end_date}' {cond_str}
        GROUP BY cashier
    """,
        as_dict=True,
    )

    return {
        "sales_summary": sales_summary,
        "payment_summary": payment_summary,
        "cashier_summary": cashier_summary,
    }


# ----------------------------
# SYSTEM MODULE
# ----------------------------


@frappe.whitelist()
def get_settings():
    return frappe.get_all("System Settings_2", fields=["name", "parameter", "value"])


@frappe.whitelist()
def create_setting(parameter, value):
    doc = frappe.get_doc({"doctype": "System Settings_2", "parameter": parameter, "value": value})
    doc.insert()
    return doc


@frappe.whitelist()
def update_setting(name, value):
    doc = frappe.get_doc("System Settings_2", name)
    doc.value = value
    doc.save()
    return doc


@frappe.whitelist()
def delete_setting(name):
    frappe.delete_doc("System Settings_2", name)
    return {"status": "success"}


# ----------------------------
# CASH COUNTING MODULE API
# ----------------------------


@frappe.whitelist()
def get_cash_counts():
    return frappe.get_all("Cash Counting_2", fields=["name", "user", "amount", "date"])


@frappe.whitelist()
def create_cash_count(user, amount, date):
    doc = frappe.get_doc({"doctype": "Cash Counting_2", "user": user, "amount": amount, "date": date})
    doc.insert()
    return doc


@frappe.whitelist()
def update_cash_count(name, amount):
    doc = frappe.get_doc("Cash Counting_2", name)
    doc.amount = amount
    doc.save()
    return doc


@frappe.whitelist()
def delete_cash_count(name):
    frappe.delete_doc("Cash Counting_2", name)
    return {"status": "success"}


# ----------------------------
# CASHIER OUT MODULE
# ----------------------------


@frappe.whitelist()
def get_shifts():
    return frappe.get_all(
        "Cashier Out", fields=["name", "user", "shift", "total_cash", "start_time", "end_time"]
    )


@frappe.whitelist()
def create_shift(user, shift, total_cash, start_time, end_time):
    doc = frappe.get_doc(
        {
            "doctype": "Cashier Out",
            "user": user,
            "shift": shift,
            "total_cash": total_cash,
            "start_time": start_time,
            "end_time": end_time,
        }
    )
    doc.insert()
    return doc


@frappe.whitelist()
def update_shift(name, total_cash, end_time):
    doc = frappe.get_doc("Cashier Out", name)
    doc.total_cash = total_cash
    doc.end_time = end_time
    doc.save()
    return doc


@frappe.whitelist()
def delete_shift(name):
    frappe.delete_doc("Cashier Out", name)
    return {"status": "success"}


# ----------------------------
# DAY END CLOSING MODULE
# ----------------------------


@frappe.whitelist()
def get_day_end():
    return frappe.get_all(
        "Day End Closing_2", fields=["name", "user", "total_cash", "open_work_orders", "closing_time"]
    )


@frappe.whitelist()
def create_day_end(user, total_cash, open_work_orders, closing_time):
    doc = frappe.get_doc(
        {
            "doctype": "Day End Closing_2",
            "user": user,
            "total_cash": total_cash,
            "open_work_orders": open_work_orders,
            "closing_time": closing_time,
        }
    )
    doc.insert()
    return doc


@frappe.whitelist()
def update_day_end(name, total_cash, open_work_orders, closing_time):
    doc = frappe.get_doc("Day End Closing_2", name)
    doc.total_cash = total_cash
    doc.open_work_orders = open_work_orders
    doc.closing_time = closing_time
    doc.save()
    return doc


@frappe.whitelist()
def delete_day_end(name):
    frappe.delete_doc("Day End Closing_2", name)
    return {"status": "success"}


# ----------------------------
# EXIT MODULE
# ----------------------------


@frappe.whitelist()
def exit_pos(user):
    """
    Simple API to log the user exit from POS.
    Can also record shift summary closure if needed.
    """
    # Optional: Update Shift Summary for this user if open
    shift = frappe.db.get_value("Day End Closing_2", {"user": user, "end_time": None})
    if shift:
        shift_doc = frappe.get_doc("Day End Closing_2", shift)
        import datetime

        shift_doc.end_time = datetime.datetime.now()
        shift_doc.save()

    frappe.db.commit()
    return {"message": _("POS exited successfully")}


@frappe.whitelist(allow_guest=True)
def cashier_login(cashier_code):
    """
    API to verify cashier login code
    """
    user = frappe.get_all(
        "User", filters={"cashier_code": cashier_code, "enabled": 1}, fields=["name", "full_name"]
    )

    if user:
        frappe.local.response.update(
            {"status": "success", "message": f"Welcome {user[0].full_name}", "user": user[0].name}
        )
        return frappe.local.response
    else:
        frappe.throw(_("Invalid Cashier Code"))
