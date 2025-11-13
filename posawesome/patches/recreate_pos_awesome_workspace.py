import frappe
import json
import os

WORKSPACE_NAME = "POS Awesome"


def execute():
    frappe.log_message(f"--- Starting Delete and Recreate patch for {WORKSPACE_NAME} ---", "POSAwesome Patch")

    # 1. Delete the existing workspace document, if it exists
    if frappe.db.exists("Workspace", WORKSPACE_NAME):
        try:
            frappe.delete_doc("Workspace", WORKSPACE_NAME, force=1, ignore_permissions=True)
            frappe.db.commit()
            frappe.log_message(f"Successfully deleted workspace '{WORKSPACE_NAME}'.", "POSAwesome Patch")
        except Exception as e:
            frappe.log_error(f"Failed to delete workspace '{WORKSPACE_NAME}': {e}", "POSAwesome Patch Error")
            # If deletion fails, we cannot proceed
            return

    # 2. Construct the absolute path to the workspace JSON file
    app_path = frappe.get_app_path("posawesome")
    json_path = os.path.join(
        app_path, "posawesome", "workspace", "pos_awesome", "pos_awesome.json"
    )

    if not os.path.exists(json_path):
        frappe.log_error(f"Workspace JSON not found at {json_path}. Cannot recreate.", "POSAwesome Patch")
        return

    # 3. Read the workspace definition from the JSON file
    with open(json_path, "r") as f:
        workspace_json = json.load(f)

    # 4. Create a new workspace document from the JSON data
    try:
        new_workspace = frappe.get_doc(workspace_json)
        new_workspace.insert(ignore_permissions=True)
        frappe.db.commit()
        frappe.log_message(f"Successfully recreated workspace '{WORKSPACE_NAME}' from JSON.", "POSAwesome Patch")
    except Exception as e:
        frappe.log_error(f"Failed to recreate workspace '{WORKSPACE_NAME}': {e}", "POSAwesome Patch Error")
        return

    # 5. Clear cache to ensure changes are reflected
    frappe.clear_cache()
    frappe.clear_website_cache()
    frappe.log_message("--- Finished Delete and Recreate patch successfully. ---", "POSAwesome Patch")
