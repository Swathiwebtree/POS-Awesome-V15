# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json

import frappe
from frappe import _
from frappe.utils import cstr
from frappe.utils.response import build_response

# Import specific exceptions for better error handling
from frappe.exceptions import ValidationError, DoesNotExistError, NameError

# The custom DocType name as per your system
VEHICLE_DOCTYPE = "Vehicle Master"
CUSTOMER_DOCTYPE = "Customer"


def _api_error(message, title=None, status_code=417, exc_type="ValidationError"):
    """
    Return a JSON error Response without raising an exception.

    This avoids Frappe's `report_error()` path which can crash with BrokenPipeError
    in some dev setups when it tries to print the traceback.
    """
    message = cstr(message)
    payload = {
        "message": message,
        "exc_type": exc_type,
        "_server_messages": json.dumps(
            [
                json.dumps(
                    {
                        "message": message,
                        "title": cstr(title) if title else _("Error"),
                        "indicator": "red",
                    }
                )
            ]
        ),
    }
    frappe.response.clear()
    frappe.response.update(payload)
    resp = build_response("json")
    resp.status_code = int(status_code or 500)
    return resp


def _has_column(table, column):
    # Use direct schema lookup only. frappe.db.has_column can be true from DocField
    # even when DB column is missing (customizations out of sync).
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


def _set_if_exists(doc, field, value):
    if value is None:
        return
    if hasattr(doc, "meta") and doc.meta and doc.meta.has_field(field):
        setattr(doc, field, value)


def _first_field_value(doc_or_dict, fields):
    if not doc_or_dict:
        return None
    for f in fields:
        v = None
        if isinstance(doc_or_dict, dict):
            v = doc_or_dict.get(f)
        else:
            v = getattr(doc_or_dict, f, None)
        if v not in (None, ""):
            return v
    return None


GCC_PHONE_RULES = {
    "BH": {"dial": "973", "len": 8},
    "KW": {"dial": "965", "len": 8},
    "OM": {"dial": "968", "len": 8},
    "QA": {"dial": "974", "len": 8},
    "SA": {"dial": "966", "len": 9},
    "AE": {"dial": "971", "len": 9},
}

GCC_COUNTRY_ALIASES = {
    "BH": "BH",
    "BAHRAIN": "BH",
    "KW": "KW",
    "KUWAIT": "KW",
    "OM": "OM",
    "OMAN": "OM",
    "QA": "QA",
    "QATAR": "QA",
    "SA": "SA",
    "SAUDI ARABIA": "SA",
    "SAUDI": "SA",
    "AE": "AE",
    "UAE": "AE",
    "UNITED ARAB EMIRATES": "AE",
}


def _resolve_gcc_iso(country_value, fallback_iso="BH"):
    key = cstr(country_value or "").strip().upper()
    if key in GCC_COUNTRY_ALIASES:
        return GCC_COUNTRY_ALIASES[key]
    return fallback_iso if fallback_iso in GCC_PHONE_RULES else "BH"


def _normalize_mobile_no(raw_value, country_value=None, fallback_iso="BH"):
    """Normalize mobile to E.164-style format using GCC country rules."""
    raw = cstr(raw_value or "").strip()
    if not raw:
        return ""

    digits = "".join(ch for ch in raw if ch.isdigit())
    if not digits:
        return ""

    iso = _resolve_gcc_iso(country_value, fallback_iso=fallback_iso)
    rule = GCC_PHONE_RULES.get(iso)
    dial = rule["dial"]
    national_len = int(rule["len"])

    if digits.startswith("00"):
        digits = digits[2:]

    national = digits
    if digits.startswith(dial) and len(digits) > len(dial):
        national = digits[len(dial) :]
    elif digits.startswith("0") and len(digits) == national_len + 1:
        national = digits[1:]

    if len(national) != national_len:
        country_label = iso
        for label, mapped_iso in GCC_COUNTRY_ALIASES.items():
            if mapped_iso == iso and len(label) > 2:
                country_label = label.title()
                break
        frappe.throw(
            _("Mobile number for {0} must be exactly {1} digits").format(country_label, national_len),
            ValidationError,
        )

    return f"+{dial}{national}"


def _sync_vehicle_doctype(
    vehicle_name, vehicle_no, customer, model, make, chasis_no, color, registration_number, mobile_no
):
    """
    Best-effort sync into ERPNext Vehicle doctype.
    This keeps data available even when Vehicle Master schema differs across sites.
    """
    try:
        vdoc = None
        if vehicle_name and frappe.db.exists("Vehicle", vehicle_name):
            vdoc = frappe.get_doc("Vehicle", vehicle_name)
        elif vehicle_no:
            # Vehicle table in this site may use license_plate instead of vehicle_no.
            found = []
            if _has_column("Vehicle", "vehicle_no"):
                found = frappe.get_all(
                    "Vehicle",
                    filters={"vehicle_no": vehicle_no},
                    fields=["name"],
                    limit_page_length=1,
                )
            if not found and _has_column("Vehicle", "license_plate"):
                found = frappe.get_all(
                    "Vehicle",
                    filters={"license_plate": vehicle_no},
                    fields=["name"],
                    limit_page_length=1,
                )
            if found:
                vdoc = frappe.get_doc("Vehicle", found[0].name)

        if not vdoc:
            # Create a new Vehicle record if missing, so fields like make are persisted.
            vdoc = frappe.new_doc("Vehicle")
            _set_if_exists(vdoc, "license_plate", vehicle_no)
            _set_if_exists(vdoc, "vehicle_no", vehicle_no)

        _set_if_exists(vdoc, "customer", customer)
        _set_if_exists(vdoc, "vehicle_no", vehicle_no)
        _set_if_exists(vdoc, "license_plate", vehicle_no)
        _set_if_exists(vdoc, "plate_no", vehicle_no)
        _set_if_exists(vdoc, "model", model)
        _set_if_exists(vdoc, "vehicle_model", model)
        _set_if_exists(vdoc, "model_no", model)
        _set_if_exists(vdoc, "make", make)
        _set_if_exists(vdoc, "vehicle_make", make)
        _set_if_exists(vdoc, "brand", make)
        _set_if_exists(vdoc, "manufacturer", make)
        _set_if_exists(vdoc, "chasis_no", chasis_no)
        _set_if_exists(vdoc, "chassis_no", chasis_no)
        _set_if_exists(vdoc, "color", color)
        _set_if_exists(vdoc, "registration_number", registration_number)
        _set_if_exists(vdoc, "mobile_no", mobile_no)
        _set_if_exists(vdoc, "tel_mobile", mobile_no)
        if vdoc.is_new():
            vdoc.insert(ignore_permissions=True, ignore_mandatory=True)
        else:
            vdoc.save(ignore_permissions=True)
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Vehicle sync warning")


# ============ POS Vehicle APIs ============


@frappe.whitelist()
def create_vehicle(
    vehicle_no,
    customer,
    model=None,
    make=None,
    chasis_no=None,
    color=None,
    registration_number=None,
    mobile_no=None,
    country=None,
    method="create",
    vehicle_id=None,
):
    """
    Creates or updates a Vehicle Master record based on the 'method' parameter.

    FIX: Restructures error handling to explicitly re-raise Frappe validation
    exceptions, preventing the BrokenPipeError during error response packaging.
    """

    # 1. Sanitize/Normalize inputs
    vehicle_no = (vehicle_no or "").upper().strip()
    customer = customer or ""

    # Use empty string for DocType fields if None is passed from frontend
    model = model or ""
    make = make or ""
    chasis_no = chasis_no or ""
    color = color or ""
    registration_number = registration_number or ""
    mobile_no = _normalize_mobile_no(mobile_no or "", country_value=country)

    # 2. Aggressive Pre-Validation for required fields
    # This prevents the call from hitting the internal Frappe Naming logic
    # if basic mandatory fields are missing (like the one used for DocType name).
    if not vehicle_no:
        return _api_error(_("Vehicle No. is mandatory."), title=_("Validation Error"), status_code=422)
    if not customer:
        return _api_error(_("Customer is mandatory."), title=_("Validation Error"), status_code=422)

    # We use a try block specifically around document operations
    try:
        vm_meta = frappe.get_meta(VEHICLE_DOCTYPE)

        def _vm_set(target_doc, field, value):
            if value is None:
                return
            if vm_meta.has_field(field):
                setattr(target_doc, field, value)

        def _vm_doc_data(base):
            doc = {"doctype": VEHICLE_DOCTYPE}
            for k, v in base.items():
                if k in ("doctype",):
                    continue
                if vm_meta.has_field(k):
                    doc[k] = v
            return doc

        if method == "create":
            # Check for existing vehicle using vehicle_no as the unique key
            if frappe.db.exists(VEHICLE_DOCTYPE, vehicle_no):
                return _api_error(
                    _("Vehicle No. {0} already exists in the system.").format(vehicle_no),
                    title=_("Already Exists"),
                    status_code=409,
                )

            # Create a new document dictionary
            base_doc_data = {
                # Setting 'name' is crucial if the DocType is configured for AutoName: field:vehicle_no
                "customer": customer,
                "vehicle_no": vehicle_no,
                "license_plate": vehicle_no,
                "plate_no": vehicle_no,
                "model": model,
                "vehicle_model": model,
                "model_no": model,
                "make": make,
                "vehicle_make": make,
                "brand": make,
                "manufacturer": make,
                "chasis_no": chasis_no,
                "chassis_no": chasis_no,
                "color": color,
                "registration_number": registration_number,
                "mobile_no": mobile_no,
                "tel_mobile": mobile_no,
            }
            doc_data = _vm_doc_data(base_doc_data)

            # Insert the new document (ignore_mandatory=True removed for better validation)
            vehicle = frappe.get_doc(doc_data)
            vehicle.insert(ignore_permissions=True)

        elif method == "update" and vehicle_id:
            # Update an existing document
            vehicle = frappe.get_doc(VEHICLE_DOCTYPE, vehicle_id)

            # Update fields based on incoming data
            _vm_set(vehicle, "customer", customer)
            _vm_set(vehicle, "vehicle_no", vehicle_no)
            _vm_set(vehicle, "license_plate", vehicle_no)
            _vm_set(vehicle, "plate_no", vehicle_no)
            _vm_set(vehicle, "model", model)
            _vm_set(vehicle, "vehicle_model", model)
            _vm_set(vehicle, "model_no", model)
            _vm_set(vehicle, "make", make)
            _vm_set(vehicle, "vehicle_make", make)
            _vm_set(vehicle, "brand", make)
            _vm_set(vehicle, "manufacturer", make)
            _vm_set(vehicle, "chasis_no", chasis_no)
            _vm_set(vehicle, "chassis_no", chasis_no)
            _vm_set(vehicle, "color", color)
            _vm_set(vehicle, "registration_number", registration_number)
            _vm_set(vehicle, "mobile_no", mobile_no)
            _vm_set(vehicle, "tel_mobile", mobile_no)

            # Save the document (ignore_mandatory=True removed for better validation)
            vehicle.save(ignore_permissions=True)

        else:
            return _api_error(
                _("Invalid method or missing vehicle ID for update."),
                title=_("API Error"),
                status_code=400,
            )

        # Commit changes and return the document
        frappe.db.commit()
        _sync_vehicle_doctype(
            vehicle_name=getattr(vehicle, "name", None),
            vehicle_no=vehicle_no,
            customer=customer,
            model=model,
            make=make,
            chasis_no=chasis_no,
            color=color,
            registration_number=registration_number,
            mobile_no=mobile_no,
        )

        # Keep linked customer mobile in sync when vehicle mobile is edited.
        try:
            if customer and mobile_no and frappe.db.exists("Customer", customer):
                frappe.db.set_value("Customer", customer, "mobile_no", mobile_no, update_modified=False)
                frappe.db.commit()
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Customer mobile sync warning")

        return vehicle.as_dict()

    # CRITICAL FIX: Explicitly catch Frappe-specific exceptions and re-raise them.
    # This pattern lets the Frappe framework handle the response properly.
    except (ValidationError, DoesNotExistError, NameError) as e:
        frappe.log_error(message=frappe.get_traceback(), title="POS Awesome Validation/Data Error")
        return _api_error(cstr(e), title=_("Validation Error"), status_code=409)

    except Exception as e:
        # Catch all other unexpected errors
        frappe.log_error(message=frappe.get_traceback(), title="POS Awesome Vehicle API General Error")
        return _api_error(
            _("An unexpected server error occurred while processing the vehicle request."),
            title=_("Server Error"),
            status_code=500,
            exc_type="ServerError",
        )


@frappe.whitelist()
def get_vehicle_and_customer(vehicle_no):
    """
    Fetches vehicle and linked customer data based on vehicle_no.
    """
    if not vehicle_no:
        return {}

    vehicle_no = vehicle_no.strip()
    vehicle = {}  # Initialize vehicle dictionary

    try:
        # 1. Try to get the vehicle document
        vehicle_doc = frappe.get_doc(VEHICLE_DOCTYPE, vehicle_no)
        vehicle = vehicle_doc.as_dict()

        customer_name = vehicle.get("customer")
        cust_doc = frappe.new_doc(CUSTOMER_DOCTYPE)  # Default to an empty customer doc

        # 2. Try to fetch the linked customer document if the link field is populated
        if customer_name:
            try:
                cust_doc = frappe.get_doc(CUSTOMER_DOCTYPE, customer_name)
            except DoesNotExistError:
                frappe.log_error(
                    f"Customer {customer_name} linked to Vehicle {vehicle_no} does not exist.",
                    "Vehicle Lookup - Missing Customer",
                )
                # Keep cust_doc as a new empty document to prevent subsequent errors

        # 3. Compile the response data
        return {
            "vehicle": {
                "name": vehicle.get("name"),
                "vehicle_no": vehicle.get("vehicle_no"),
                "model": vehicle.get("model"),
                "make": vehicle.get("make"),
                "chasis_no": vehicle.get("chasis_no"),
                "color": vehicle.get("color"),
                "registration_number": vehicle.get("registration_number"),
                "mobile_no": vehicle.get("mobile_no"),
            },
            "customer": {
                "name": cust_doc.name,
                "customer_name": getattr(cust_doc, "customer_name", ""),
                "custom_display_name": getattr(cust_doc, "custom_display_name", None)
                or getattr(cust_doc, "customer_name", ""),
                "email_id": getattr(cust_doc, "email_id", ""),
                "mobile_no": getattr(cust_doc, "mobile_no", ""),
                "tax_id": getattr(cust_doc, "tax_id", ""),
                "customer_group": getattr(cust_doc, "customer_group", ""),
                "territory": getattr(cust_doc, "territory", ""),
                "posa_discount": getattr(cust_doc, "posa_discount", 0),
            },
        }
    except DoesNotExistError:
        # Handles case where the Vehicle Master document itself is missing
        return {"vehicle": {"vehicle_no": vehicle_no}, "customer": {}}

    except Exception:
        # Catches other unexpected errors
        frappe.log_error(frappe.get_traceback(), "Vehicle Lookup Error - General Failure")
        return {}


@frappe.whitelist()
def get_all_vehicles_for_customer(customer_name):
    """
    Get all vehicles for a customer (no pagination).
    """
    # ... (Keep the rest of the function body)
    if not customer_name:
        return []

    vehicles = frappe.get_all(
        VEHICLE_DOCTYPE,
        filters={"customer": customer_name},
        fields=[
            "name",
            "vehicle_no",
            "model",
            "make",
            "chasis_no",
            "mobile_no",
            "customer",
        ],
        order_by="creation desc",
    )
    return vehicles


@frappe.whitelist()
def search_vehicles(search_term, limit=50):
    """
    Search vehicles by: 1. vehicle_no (license plate) 2. Customer mobile_no
    """
    if not search_term or len(search_term) < 2:
        frappe.throw(_("Search term must be at least 2 characters"))

    search_term = search_term.strip()

    vehicles_by_number = frappe.get_all(
        VEHICLE_DOCTYPE,
        filters={"vehicle_no": ["like", f"%{search_term}%"]},
        fields=["name", "vehicle_no", "customer", "model", "chasis_no", "make", "mobile_no"],
        limit_page_length=int(limit),
    )
    return vehicles_by_number


@frappe.whitelist()
def get_vehicles_by_customer(customer_name, limit=200, start_after=None, vehicle_no=None):
    """
    Fetch vehicles for a given customer with pagination.
    Returns vehicles with customer details including mobile_no.
    """

    if not customer_name:
        frappe.throw(_("Customer name is required"))

    def _resolve_customer_id(customer_value: str) -> str:
        """Accept Customer.name or (fallback) Customer.customer_name and resolve to Customer.name.

        This is important because the POS UI may sometimes send the display text (customer_name)
        instead of the document id (name). In that case, returning [] is confusing when vehicles exist.
        """
        customer_value = (customer_value or "").strip()
        if not customer_value:
            return customer_value

        if frappe.db.exists("Customer", customer_value):
            return customer_value

        # Fallback: resolve by customer_name (and prefer a customer that has vehicles linked).
        try:
            candidates = frappe.get_all(
                "Customer",
                filters={"customer_name": customer_value},
                fields=["name", "modified"],
                order_by="modified desc",
                limit_page_length=20,
            )
        except Exception:
            candidates = []

        if not candidates:
            return customer_value

        # Prefer customers that actually have vehicles.
        try:
            candidate_ids = [c.name for c in candidates if c.get("name")]
            if candidate_ids:
                rows = frappe.get_all(
                    VEHICLE_DOCTYPE,
                    filters={"customer": ["in", candidate_ids]},
                    fields=["customer"],
                    limit_page_length=1000,
                )
                has_vehicle = {r.customer for r in rows if r.get("customer")}
                for c in candidates:
                    if c.name in has_vehicle:
                        return c.name
        except Exception:
            pass

        # Otherwise, pick most recently modified.
        return candidates[0].name

    limit = int(limit) if limit else 200

    customer_name = _resolve_customer_id(customer_name)
    filters = {"customer": customer_name}
    vehicle_no = (vehicle_no or "").strip()
    if vehicle_no:
        # Strict match by vehicle_no when provided
        filters["vehicle_no"] = vehicle_no
    elif start_after:
        filters["name"] = [">", start_after]

    try:
        # Get customer details first (for mobile_no and customer_name)
        cust_doc = frappe.get_doc(CUSTOMER_DOCTYPE, customer_name)

        # Build field list defensively because Vehicle Master schemas differ by site.
        table_name = VEHICLE_DOCTYPE
        requested_optional_fields = [
            "model",
            "vehicle_model",
            "model_no",
            "make",
            "vehicle_make",
            "brand",
            "manufacturer",
            "chasis_no",
            "color",
            "registration_number",
            "reg_no",
            "mobile_no",
            "tel_mobile",
            "odometer",
        ]

        fields = ["name", "customer", "vehicle_no"]
        for col in requested_optional_fields:
            try:
                if frappe.db.has_column(table_name, col):
                    fields.append(col)
            except Exception:
                # If metadata check fails, skip optional column and continue.
                pass

        vehicles = frappe.get_all(
            VEHICLE_DOCTYPE,
            filters=filters,
            fields=fields,
            order_by="name asc",
            limit_page_length=1 if vehicle_no else limit,
        )

        # Enrich all vehicles with customer details
        for row in vehicles:
            row.setdefault("vehicle_no", row.get("name", ""))
            row["model"] = _first_field_value(row, ["model", "vehicle_model", "model_no"]) or ""
            row["make"] = _first_field_value(row, ["make", "vehicle_make", "brand", "manufacturer"]) or ""
            row.setdefault("chasis_no", "")
            row.setdefault("color", "")
            row.setdefault("registration_number", "")
            row.setdefault("mobile_no", "")
            row.setdefault("odometer", 0)

            # Fallback enrichment from ERPNext Vehicle doctype when Vehicle Master
            # does not contain all fields in this site schema.
            try:
                vehicle_doc = None
                v_fields = ["name"]
                table_vehicle = "Vehicle"
                for f in [
                    "model",
                    "vehicle_model",
                    "make",
                    "vehicle_make",
                    "chasis_no",
                    "chassis_no",
                    "color",
                    "registration_number",
                    "mobile_no",
                    "tel_mobile",
                    "odometer",
                ]:
                    if _has_column(table_vehicle, f):
                        v_fields.append(f)

                # Try by Vehicle.name first
                found = frappe.get_all(
                    "Vehicle",
                    filters={"name": row.get("name")},
                    fields=v_fields,
                    limit_page_length=1,
                )
                if not found and row.get("vehicle_no"):
                    # Fallback by all common identifier columns in case naming differs
                    vehicle_no_value = row.get("vehicle_no")
                    for id_field in ("vehicle_no", "license_plate", "plate_no"):
                        if found:
                            break
                        if not _has_column(table_vehicle, id_field):
                            continue
                        found = frappe.get_all(
                            "Vehicle",
                            filters={id_field: vehicle_no_value},
                            fields=v_fields,
                            limit_page_length=1,
                        )
                if found:
                    vehicle_doc = found[0]

                if vehicle_doc:
                    row["model"] = (
                        row.get("model")
                        or _first_field_value(vehicle_doc, ["model", "vehicle_model", "model_no"])
                        or ""
                    )
                    row["make"] = (
                        row.get("make")
                        or _first_field_value(vehicle_doc, ["make", "vehicle_make", "brand", "manufacturer"])
                        or ""
                    )
                    row["chasis_no"] = (
                        row.get("chasis_no")
                        or _first_field_value(vehicle_doc, ["chasis_no", "chassis_no"])
                        or ""
                    )
                    row["color"] = row.get("color") or vehicle_doc.get("color") or ""
                    row["registration_number"] = (
                        row.get("registration_number")
                        or row.get("reg_no")
                        or _first_field_value(vehicle_doc, ["registration_number", "registration_no"])
                        or ""
                    )
                    row["mobile_no"] = (
                        row.get("mobile_no")
                        or row.get("tel_mobile")
                        or _first_field_value(vehicle_doc, ["mobile_no", "tel_mobile", "phone", "phone_no"])
                        or ""
                    )
                    row["odometer"] = row.get("odometer") or vehicle_doc.get("odometer") or 0

                    # If the resolved Vehicle by name has empty make/model, try alternate
                    # identifier columns; some sites keep the richer data under a different row.
                    if (not row.get("make") or not row.get("model")) and row.get("vehicle_no"):
                        alternate_doc = None
                        vehicle_no_value = row.get("vehicle_no")
                        for id_field in ("vehicle_no", "license_plate", "plate_no"):
                            if not _has_column(table_vehicle, id_field):
                                continue
                            try:
                                alt = frappe.get_all(
                                    "Vehicle",
                                    filters={id_field: vehicle_no_value},
                                    fields=v_fields,
                                    limit_page_length=1,
                                )
                                if alt:
                                    alternate_doc = alt[0]
                                    break
                            except Exception:
                                continue

                        if alternate_doc:
                            if not row.get("model"):
                                row["model"] = (
                                    _first_field_value(
                                        alternate_doc,
                                        ["model", "vehicle_model", "model_no"],
                                    )
                                    or row.get("model")
                                    or ""
                                )
                            if not row.get("make"):
                                row["make"] = (
                                    _first_field_value(
                                        alternate_doc,
                                        ["make", "vehicle_make", "brand", "manufacturer"],
                                    )
                                    or row.get("make")
                                    or ""
                                )
            except Exception:
                # Non-fatal fallback failure; keep available Vehicle Master values.
                pass

            row["customer"] = customer_name
            row["customer_name"] = cust_doc.customer_name
            row["custom_display_name"] = (
                getattr(cust_doc, "custom_display_name", None) or cust_doc.customer_name
            )
            if not row.get("mobile_no"):
                row["mobile_no"] = cust_doc.mobile_no or ""
            row["email_id"] = cust_doc.email_id or ""
            row["tax_id"] = cust_doc.tax_id or ""

        frappe.logger().debug(f"Found {len(vehicles)} vehicles for customer: {customer_name}")

        return vehicles

    except frappe.DoesNotExistError:
        frappe.log_error(f"Customer not found: {customer_name}", "Vehicle Fetch Error")
        return []
    except Exception as e:
        frappe.logger().error(f"Error fetching vehicles for {customer_name}: {str(e)}")
        frappe.throw(_("Error fetching vehicles: {0}").format(str(e)))


@frappe.whitelist()
def get_vehicle_models(search_term="", make="", limit=500):
    """
    Return distinct vehicle models, optionally filtered by selected make.
    Works across Vehicle and Vehicle Master schemas.
    """
    search_term = (search_term or "").strip()
    make = (make or "").strip()
    try:
        limit = int(limit or 500)
    except Exception:
        limit = 500
    limit = min(max(limit, 1), 5000)

    values = set()

    def _collect_models(table_label, model_columns, make_columns):
        existing_models = [c for c in model_columns if _has_column(table_label, c)]
        if not existing_models:
            return
        existing_makes = [c for c in make_columns if _has_column(table_label, c)]

        for model_col in existing_models:
            where_parts = [f"TRIM(IFNULL({model_col}, '')) != ''"]
            params = []

            if search_term:
                where_parts.append(f"{model_col} LIKE %s")
                params.append(f"%{search_term}%")

            if make:
                if not existing_makes:
                    continue
                make_expr = " OR ".join([f"LOWER(TRIM(IFNULL({c}, ''))) = LOWER(%s)" for c in existing_makes])
                where_parts.append(f"({make_expr})")
                params.extend([make] * len(existing_makes))

            where_clause = " AND ".join(where_parts)
            table_name = table_label if table_label.startswith("tab") else f"tab{table_label}"
            rows = frappe.db.sql(
                f"""
                SELECT DISTINCT TRIM({model_col}) AS value
                FROM `{table_name}`
                WHERE {where_clause}
                ORDER BY value ASC
                LIMIT %s
                """,
                tuple(params + [limit]),
                as_dict=True,
            )
            for row in rows:
                value = (row.get("value") or "").strip()
                if value:
                    values.add(value)

    _collect_models("Vehicle", ["model", "vehicle_model", "model_no"], ["make", "vehicle_make", "brand"])
    _collect_models(
        VEHICLE_DOCTYPE,
        ["model", "vehicle_model", "model_no"],
        ["make", "vehicle_make", "brand", "manufacturer"],
    )

    return sorted(values, key=lambda x: x.lower())[:limit]


@frappe.whitelist()
def get_customer_by_vehicle(vehicle_no):
    """
    Return customer details for a vehicle number (exact match).
    Defensive: tries Vehicle Master then Vehicle; normalizes vehicle_no and logs findings.
    """
    if not vehicle_no:
        frappe.logger().warning("get_customer_by_vehicle called without vehicle_no")
        frappe.throw(_("Vehicle number is required"))

    # normalize common input issues
    vehicle_no_clean = str(vehicle_no).strip().upper()

    frappe.logger().info(f"get_customer_by_vehicle lookup starting for: {vehicle_no_clean}")

    # try Vehicle Master first, then Vehicle
    doctype_candidates = ["Vehicle Master", "Vehicle"]
    vehicle = None
    vehicle_doc = None

    for dt in doctype_candidates:
        try:
            found = frappe.get_all(
                dt,
                filters={"vehicle_no": vehicle_no_clean},
                fields=["name", "customer", "model", "chasis_no", "vehicle_no"],
                limit_page_length=1,
            )
            if found:
                vehicle = found[0]
                frappe.logger().info(f"Found vehicle in {dt}: {vehicle}")
                break
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Error querying {dt} for vehicle {vehicle_no_clean}")
            # continue to next candidate

    if not vehicle:
        # Try loose search (in case of extra spaces/case or vehicle_no stored differently)
        try:
            loose = frappe.db.sql(
                """
                SELECT name, customer, model, chasis_no, vehicle_no
                FROM `tabVehicle Master`
                WHERE REPLACE(UPPER(vehicle_no), ' ', '') = %s
                LIMIT 1
                """,
                (vehicle_no_clean.replace(" ", ""),),
                as_dict=1,
            )
            if loose:
                vehicle = loose[0]
                frappe.logger().info(f"Found vehicle via loose match in Vehicle Master: {vehicle}")
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Loose match attempt failed")

    if not vehicle:
        frappe.logger().info(f"No vehicle found for '{vehicle_no_clean}'")
        # return empty object (consistent with your current behavior), but log
        return {}

    cust_name = vehicle.get("customer")
    if not cust_name:
        frappe.logger().info(f"Vehicle {vehicle.get('name')} has no customer linked")
        return {"vehicle": vehicle, "customer": {}}

    try:
        cust_doc = frappe.get_doc("Customer", cust_name)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            f"Failed to fetch Customer {cust_name} linked to vehicle {vehicle.get('name')}",
        )
        return {"vehicle": vehicle, "customer": {}}

    resp = {
        "vehicle": {
            "name": vehicle.get("name"),
            "vehicle_no": vehicle.get("vehicle_no"),
            "model": vehicle.get("model"),
            "chasis_no": vehicle.get("chasis_no"),
        },
        "customer": {
            "name": cust_doc.name,
            "customer_name": getattr(cust_doc, "customer_name", ""),
            "custom_display_name": getattr(cust_doc, "custom_display_name", None)
            or getattr(cust_doc, "customer_name", ""),
            "email_id": getattr(cust_doc, "email_id", ""),
            "mobile_no": getattr(cust_doc, "mobile_no", ""),
            "tax_id": getattr(cust_doc, "tax_id", ""),
            "customer_group": getattr(cust_doc, "customer_group", ""),
            "territory": getattr(cust_doc, "territory", ""),
            "posa_discount": getattr(cust_doc, "posa_discount", 0),
        },
    }

    frappe.logger().info(
        f"get_customer_by_vehicle returning for {vehicle_no_clean}: customer {cust_doc.name}"
    )
    return resp


@frappe.whitelist()
def get_vehicles_by_search(search_term="", limit=1):
    """
    Lookup vehicle by vehicle_no and return vehicle + customer
    (wrapper around get_customer_by_vehicle for compatibility)
    """
    if not search_term:
        return {}

    return get_customer_by_vehicle(search_term)


@frappe.whitelist()
def get_all_vehicles(limit=500):
    """
    Used for POS vehicle dropdown (no customer selected).
    Returns ALL vehicles with linked customer details.
    """

    vehicles = frappe.get_all(
        VEHICLE_DOCTYPE,
        fields=[
            "name",
            "vehicle_no",
            "customer",
        ],
        order_by="modified desc",
        limit_page_length=int(limit),
    )

    if not vehicles:
        return []

    # Fetch customer details in ONE query (important)
    customer_names = list({v.customer for v in vehicles if v.customer})
    has_custom_display_name = False
    try:
        has_custom_display_name = bool(
            frappe.db.has_column("tabCustomer", "custom_display_name")
            and frappe.get_meta("Customer").get_field("custom_display_name")
        )
    except Exception:
        has_custom_display_name = False

    customer_fields = ["name", "customer_name", "mobile_no"]
    if has_custom_display_name:
        customer_fields.insert(2, "custom_display_name")

    customers = frappe.get_all(
        "Customer",
        filters={"name": ["in", customer_names]},
        fields=customer_fields,
    )
    customer_map = {c.name: c for c in customers}

    for v in vehicles:
        cust = customer_map.get(v.customer)
        v["customer_name"] = getattr(cust, "customer_name", "") if cust else ""
        v["custom_display_name"] = (
            (getattr(cust, "custom_display_name", None) or getattr(cust, "customer_name", ""))
            if cust
            else (v.get("customer_name") or "")
        )
        v["mobile_no"] = getattr(cust, "mobile_no", "") if cust else ""

    return vehicles


@frappe.whitelist()
def get_vehicle_makes(search_term="", limit=500):
    """
    Return vehicle makes for POS dropdown.
    Includes makes stored in both Vehicle and Vehicle Master doctypes.
    """
    search_term = (search_term or "").strip()
    try:
        limit = int(limit or 500)
    except Exception:
        limit = 500
    limit = min(max(limit, 1), 2000)

    make_set = set()
    fetch_limit = max(limit * 10, 5000)

    def _collect_from(table_label, make_columns):
        table_name = table_label if str(table_label).startswith("tab") else f"tab{table_label}"
        existing_make_columns = [c for c in make_columns if _has_column(table_label, c)]
        if not existing_make_columns or len(make_set) >= limit:
            return

        for column in existing_make_columns:
            try:
                conditions = [f"COALESCE(`{column}`, '') != ''"]
                params = {"limit": fetch_limit}
                if search_term:
                    conditions.append(f"`{column}` LIKE %(search)s")
                    params["search"] = f"%{search_term}%"

                rows = frappe.db.sql(
                    f"""
                    SELECT DISTINCT TRIM(`{column}`) AS make
                    FROM `{table_name}`
                    WHERE {' AND '.join(conditions)}
                    ORDER BY TRIM(`{column}`) ASC
                    LIMIT %(limit)s
                    """,
                    params,
                    as_dict=True,
                )
            except Exception:
                continue

            for row in rows:
                value = (row.get("make") or "").strip()
                if value:
                    make_set.add(value)
                if len(make_set) >= limit:
                    return

    _collect_from("Vehicle", ["make", "vehicle_make", "brand", "manufacturer"])
    _collect_from(VEHICLE_DOCTYPE, ["make", "vehicle_make", "brand", "manufacturer"])

    return sorted(make_set, key=lambda x: x.lower())[:limit]
