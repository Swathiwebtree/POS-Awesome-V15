import frappe


def execute():
    indexes = [
        ("Customer", ["mobile_no"], "idx_customer_mobile_no"),
        ("Customer", ["customer_name"], "idx_customer_customer_name"),
        ("Vehicle Master", ["vehicle_no"], "idx_vehicle_master_vehicle_no"),
        ("Vehicle Master", ["registration_number"], "idx_vehicle_master_registration_number"),
        ("Vehicle Master", ["plate_no"], "idx_vehicle_master_plate_no"),
        ("Vehicle Master", ["customer"], "idx_vehicle_master_customer"),
    ]

    for doctype, fields, index_name in indexes:
        try:
            frappe.db.add_index(doctype, fields, index_name=index_name)
        except Exception:
            # Ignore if already exists or field is missing on this site schema.
            pass
