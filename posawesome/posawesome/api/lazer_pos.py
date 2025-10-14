import frappe
from frappe.utils.data import nowdate
from frappe import _

# ----------------------------
# TRANSACTIONS MODULE
# ----------------------------


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
    """Fetch service issues"""
    return frappe.get_all("Service Issue", fields=["name", "issue_code", "description", "status"])


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
def save_work_order(work_order, vehicle, customer, staff_code, staff_name, items, discount=0):
    wo = frappe.get_doc({"doctype": "Work Order", "name": work_order})
    wo.vehicle_no = vehicle
    wo.customer = customer
    wo.sales_person = staff_name
    wo.discount = float(discount)
    for i in items:
        wo.append("items", i)
    wo.insert(ignore_permissions=True)
    frappe.db.commit()
    return get_work_order_details(work_order)


@frappe.whitelist()
def get_items_from_barcode(barcode):
    return frappe.get_all(
        "Item",
        filters={"barcode": barcode},
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


@frappe.whitelist()
def get_petty_cash_transactions():
    """
    Fetch petty cash transactions with item details
    """
    transactions = frappe.get_all(
        "Petty Cash",
        fields=[
            "name as pc_no",
            "ref",
            "station_id",
            "posting_date as date",
            "description",
            "user_id",
            "remarks",
            "shift_closing_id",
            "count_closing_id",
            "day_closing_id",
            "total",
        ],
        order_by="posting_date desc",
    )

    for txn in transactions:
        # Fetch item details
        txn["items"] = frappe.get_all(
            "Petty Cash Item",
            filters={"parent": txn.pc_no},
            fields=[
                "account as ac_code",
                "account_name",
                "description",
                "amount",
                "division as div",
                "account_id",
                "date",
                "typ",
                "trans_no",
                "ref_no",
                "currency as cur",
                "paid_foreign",
                "paid_local",
            ],
        )
    return transactions


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
    """Void work order"""
    wo = frappe.get_doc("Work Order", order_no)
    wo.status = "Voided"
    wo.save(ignore_permissions=True)
    frappe.db.commit()
    return get_work_order_details(order_no)


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
def get_petty_cash():
    """List petty cash entries"""
    return frappe.get_all("Petty Cash", fields=["name", "date", "amount", "paid_by", "division", "status"])


@frappe.whitelist()
def get_receipt_voucher():
    """List receipt vouchers"""
    return frappe.get_all(
        "Receipt Voucher", fields=["name", "customer", "date", "amount", "status", "division"]
    )


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


@frappe.whitelist()
def get_bills_listing_work_order(date_from=None, date_to=None, work_order_no=None):
    """
    Returns a list of bills filtered by work order and date range.
    """
    filters = {}

    if date_from:
        filters["posting_date"] = [">=", date_from]
    if date_to:
        filters["posting_date"] = ["<=", date_to]
    if work_order_no:
        filters["work_order_no"] = work_order_no

    # Query the Sales Invoice or relevant DocType
    bills = frappe.get_all(
        "Sales Invoice",
        filters=filters,
        fields=[
            "work_order_no",
            "name as bill_no",
            "posting_date as date",
            "payment_method",
            "vehicle_no",
            "total_amount",
            "discount_amount",
            "amount_after_discount",
            "tax_amount as vat_amount",
            "grand_total as net_amount",
        ],
        order_by="posting_date desc",
    )

    # Calculate the grand total row
    grand_total = {
        "work_order_no": "Grand Total",
        "bill_no": "",
        "date": "",
        "payment_method": "",
        "vehicle_no": "",
        "total_amount": sum(bill.total_amount for bill in bills),
        "discount_amount": sum(bill.discount_amount for bill in bills),
        "amount_after_discount": sum(bill.amount_after_discount for bill in bills),
        "vat_amount": sum(bill.vat_amount for bill in bills),
        "net_amount": sum(bill.net_amount for bill in bills),
    }

    bills.append(grand_total)
    return bills


@frappe.whitelist()
def get_bills_listing_vehicle(vehicle_no=None, from_date=None, to_date=None):
    """
    Returns bills listing filtered by Vehicle No and Date Range.
    """

    if not vehicle_no:
        frappe.throw(_("Vehicle No is required"))

    filters = []
    if from_date:
        filters.append(["date", ">=", from_date])
    if to_date:
        filters.append(["date", "<=", to_date])
    filters.append(["vehicle_no", "=", vehicle_no])

    bills = frappe.get_all(
        "Sales Invoice",  # Assuming Sales Invoice is the doctype storing POS bills
        filters=filters,
        fields=[
            "name as bill_no",
            "work_order_no",
            "date",
            "payment_method",
            "time_in",
            "time_out",
            "vehicle_no",
            "total_amount",
            "discount_amount",
            "amount_after_discount",
            "vat_amount",
            "net_amount",
        ],
        order_by="date desc",
    )

    grand_total = sum(bill.get("net_amount", 0) for bill in bills)

    return {"bills": bills, "grand_total": grand_total}


@frappe.whitelist()
def get_payment_summary_list(from_date=None, to_date=None, payment_type=None):
    """
    Returns a summary of payments within the specified date range and optional payment type.

    :param from_date: Filter payments from this date (YYYY-MM-DD)
    :param to_date: Filter payments up to this date (YYYY-MM-DD)
    :param payment_type: Optional filter for a specific payment type (Cash, Card, Coupon, etc.)
    :return: List of dictionaries containing Date, Transaction Number, Payment Code, and Amount
    """

    filters = {}
    if from_date:
        filters["posting_date"] = [">=", from_date]
    if to_date:
        filters["posting_date"] = ["<=", to_date]
    if payment_type:
        filters["payment_type"] = payment_type

    payment_summary = frappe.get_all(
        "Payment Entry",  # Assuming Payment Entry doctype stores the payments
        filters=filters,
        fields=[
            "posting_date as date",
            "name as transaction_number",
            "payment_type as payment_code",
            "paid_amount as amount",
        ],
        order_by="posting_date asc",
    )

    # Optional: convert amounts to float for frontend usage
    for entry in payment_summary:
        entry["amount"] = flt(entry["amount"])

    return payment_summary


@frappe.whitelist()
def get_stock_in_hand_list(filters=None):
    """
    API to fetch Stock in Hand report details
    Filters (optional) can include:
        - item_code
        - location
        - from_date
        - to_date
    """
    filters = filters or {}
    conditions = []

    if filters.get("item_code"):
        conditions.append(f"item_code='{filters.get('item_code')}'")
    if filters.get("location"):
        conditions.append(f"location='{filters.get('location')}'")
    if filters.get("from_date"):
        conditions.append(f"posting_date>='{filters.get('from_date')}'")
    if filters.get("to_date"):
        conditions.append(f"posting_date<='{filters.get('to_date')}'")

    condition_str = " AND ".join(conditions)
    if condition_str:
        condition_str = "WHERE " + condition_str

    query = f"""
        SELECT
            item_code,
            item_name,
            warehouse as location,
            sum(actual_qty) as stock_in_hand,
            stock_uom,
            valuation_rate,
            sum(actual_qty * valuation_rate) as total_value
        FROM `tabBin`
        {condition_str}
        GROUP BY item_code, warehouse
        ORDER BY item_code
    """

    stock_list = frappe.db.sql(query, as_dict=True)

    # Add formatted totals if needed
    for row in stock_list:
        row["stock_in_hand"] = flt(row.get("stock_in_hand", 0), 2)
        row["total_value"] = flt(row.get("total_value", 0), 2)

    return stock_list


@frappe.whitelist()
def get_stock_sales_list(
    start_date=None,
    end_date=None,
    department=None,
    main_category=None,
    sub_category=None,
    stock_item_from=None,
    stock_item_to=None,
    group_by=None,
):
    """
    Returns stock sales report filtered by date, department, category, or stock item.
    """
    filters = []

    if start_date:
        filters.append(["posting_date", ">=", start_date])
    if end_date:
        filters.append(["posting_date", "<=", end_date])
    if department:
        filters.append(["department", "=", department])
    if main_category:
        filters.append(["main_category", "=", main_category])
    if sub_category:
        filters.append(["sub_category", "=", sub_category])
    if stock_item_from and stock_item_to:
        filters.append(["item_code", ">=", stock_item_from])
        filters.append(["item_code", "<=", stock_item_to])

    sales_data = frappe.get_all(
        "Sales Invoice Item",
        filters=filters,
        fields=[
            "posting_date",
            "item_code",
            "item_name",
            "quantity",
            "amount",
            "discount_amount",
            "net_amount",
        ],
    )

    # Grouping logic (optional)
    if group_by == "Salesman":
        grouped_data = {}
        for row in sales_data:
            key = frappe.get_value("Sales Invoice", row.get("parent"), "owner")
            grouped_data.setdefault(key, []).append(row)
        return grouped_data

    elif group_by == "Stock Item":
        grouped_data = {}
        for row in sales_data:
            key = row["item_code"]
            grouped_data.setdefault(key, []).append(row)
        return grouped_data

    # Default: return raw list
    return sales_data


@frappe.whitelist()
def get_sales_points_list(start_date=None, end_date=None, staff=None, terminal=None, group_by=None):
    """
    Fetches Sales Points report.

    Args:
        start_date (str): Filter by start date (YYYY-MM-DD)
        end_date (str): Filter by end date (YYYY-MM-DD)
        staff (str): Staff code filter
        terminal (str): Terminal filter
        group_by (str): Option to group by Date, Staff, Terminal

    Returns:
        List of dictionaries containing sales points information
    """
    conditions = []
    if start_date:
        conditions.append(f"date >= '{start_date}'")
    if end_date:
        conditions.append(f"date <= '{end_date}'")
    if staff:
        conditions.append(f"staff_code = '{staff}'")
    if terminal:
        conditions.append(f"terminal = '{terminal}'")

    where_clause = " AND ".join(conditions)
    if where_clause:
        where_clause = "WHERE " + where_clause

    query = f"""
        SELECT
            date,
            staff_code,
            staff_name,
            terminal,
            SUM(points) AS total_points,
            COUNT(*) AS transactions_count
        FROM `tabSales Points`
        {where_clause}
    """

    if group_by:
        query += f" GROUP BY {group_by}"

    query += " ORDER BY date ASC"

    sales_points = frappe.db.sql(query, as_dict=True)
    return sales_points


@frappe.whitelist()
def get_sales_transaction_list(start_date=None, end_date=None, staff=None, terminal=None):
    """
    Fetch Sales Transactions within a given date range, optionally filtered by staff and terminal.
    """
    filters = {}

    if start_date:
        filters["posting_date"] = [">=", start_date]
    if end_date:
        filters["posting_date"] = ["<=", end_date]
    if staff:
        filters["staff"] = staff
    if terminal:
        filters["terminal"] = terminal

    transactions = frappe.get_all(
        "Sales Transaction",
        filters=filters,
        fields=[
            "name",
            "posting_date",
            "transaction_number",
            "bill_no",
            "work_order_no",
            "payment_method",
            "customer",
            "vehicle_no",
            "total_amount",
            "discount",
            "net_amount",
            "vat_amount",
        ],
        order_by="posting_date desc",
    )

    return transactions


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
    if not customer:
        return {"points": 0}

    cards = frappe.get_all(
        "Loyalty Card",
        filters={"customer": customer, "status": "Active"},
        fields=["points"]
    )

    total_points = sum(card.points for card in cards)
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
def get_system_status():
    """Fetch system status information"""
    return {
        "server_time": frappe.utils.data.now_datetime(),
        "frappe_version": frappe.__version__,
        "site_name": frappe.local.site,
    }


# ----------------------------
# CASH COUNTING MODULE API
# ----------------------------


@frappe.whitelist(allow_guest=False)
def submit_cash_count(cashDenominations):
    """
    Save the cash count for the current cashier session.
    cashDenominations: list of dicts [{denomination: 1, count: 5, total: 5}, ...]
    """
    import json

    cash_data = json.loads(cashDenominations)

    total_cash = sum([item["denomination"] * item["count"] for item in cash_data])

    # Create a new Cash Counting record
    doc = frappe.get_doc(
        {
            "doctype": "Cash Counting",
            "counted_by": frappe.session.user,
            "count_date": now_datetime(),
            "cash_breakup": cash_data,
            "total_cash": total_cash,
        }
    )
    doc.insert(ignore_permissions=True)
    frappe.db.commit()

    return {
        "message": "Cash count submitted successfully",
        "total_cash": total_cash,
        "cash_breakup": cash_data,
    }


@frappe.whitelist()
def get_cash_count(user=None):
    """
    Get the last cash count for a user or current session.
    """
    user = user or frappe.session.user
    last_count = frappe.get_all(
        "Cash Counting",
        filters={"counted_by": user},
        order_by="creation desc",
        limit=1,
        fields=["count_date", "cash_breakup", "total_cash"],
    )
    return last_count


# ----------------------------
# CASHIER OUT MODULE
# ----------------------------


@frappe.whitelist()
def cashier_out():
    """
    API to perform Cashier Out.
    Records the cashier out event for the current user/session.
    """
    user = frappe.session.user

    # You can customize the logic, e.g., check open work orders or pending cash counts
    # Here, we just log a cashier out entry
    doc = frappe.get_doc(
        {
            "doctype": "Cashier Out Log",
            "cashier": user,
            "status": "Completed",
            "out_time": frappe.utils.now_datetime(),
        }
    )
    doc.insert(ignore_permissions=True)
    frappe.db.commit()

    return {"message": _("Cashier out completed successfully.")}


# ----------------------------
# DAY END CLOSING MODULE
# ----------------------------


@frappe.whitelist()
def day_end_closing():
    """
    Perform day end closing: calculate total cash, transactions, and generate a report.
    """
    # Example: Fetch all transactions for today
    today = nowdate()
    transactions = frappe.get_all(
        "Work Order",
        filters={"work_order_date": today, "status": ["in", ["Open", "Closed"]]},
        fields=["name", "vehicle_no", "net_total", "discount", "paid_amount"],
    )

    # Calculate totals
    total_sales = sum([t["net_total"] for t in transactions])
    total_discount = sum([t["discount"] for t in transactions])
    total_paid = sum([t["paid_amount"] for t in transactions])

    # Example report structure
    report = {
        "date": today,
        "total_sales": total_sales,
        "total_discount": total_discount,
        "total_paid": total_paid,
        "transaction_count": len(transactions),
        "transactions": transactions,
    }

    # Optionally mark all transactions as "Closed" for the day
    for t in transactions:
        doc = frappe.get_doc("Work Order", t["name"])
        doc.status = "Closed"
        doc.save(ignore_permissions=True)

    frappe.db.commit()
    return report


# ----------------------------
# EXIT MODULE
# ----------------------------


@frappe.whitelist()
def exit_pos(cashier, branch):
    """Log exit action for a cashier"""
    frappe.msgprint(_("Cashier {0} logged out from branch {1}").format(cashier, branch))
    return {"status": "success", "cashier": cashier, "branch": branch}
