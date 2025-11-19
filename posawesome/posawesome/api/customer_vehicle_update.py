import frappe


def update_vehicle_for_customer(doc, method):
    vehicle_no = doc.custom_vehicle_no

    if vehicle_no:
        try:
            # Load the vehicle
            vehicle = frappe.get_doc("Vehicle Master", vehicle_no)

            # Update fields
            vehicle.customer = doc.name
            vehicle.customer_name = doc.customer_name

            # Save updates
            vehicle.save(ignore_permissions=True)

        except Exception as e:
            frappe.log_error(f"Vehicle update failed: {str(e)}", "Vehicle Update Error")
