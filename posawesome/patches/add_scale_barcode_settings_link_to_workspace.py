import frappe
import json
import os

WORKSPACE_NAME = "POS Awesome"


def execute():
    # 1. Ensure the workspace exists
    if not frappe.db.exists("Workspace", WORKSPACE_NAME):
        frappe.log_message(
            f"Workspace '{WORKSPACE_NAME}' not found. Skipping patch.", "POSAwesome Patch"
        )
        return

    # 2. Construct the absolute path to the workspace JSON file
    app_path = frappe.get_app_path("posawesome")
    json_path = os.path.join(
        app_path, "posawesome", "workspace", "pos_awesome", "pos_awesome.json"
    )

    if not os.path.exists(json_path):
        frappe.log_error(f"Workspace JSON not found at {json_path}", "POSAwesome Patch")
        return

    # 3. Read the workspace definition from the JSON file
    with open(json_path, "r") as f:
        workspace_json = json.load(f)

    # 4. Get the workspace document from the database
    workspace = frappe.get_doc("Workspace", WORKSPACE_NAME)

    # 5. Overwrite the links in the document with the ones from the JSON file
    workspace.links = []
    for link_data in workspace_json.get("links", []):
        workspace.append("links", link_data)

    # 6. Crucially, reset the 'custom' flag to allow updates
    workspace.custom = 0
    workspace.flags.ignore_validate = True  # Avoid validation errors on save

    try:
        # 7. Save the workspace, forcing the overwrite
        workspace.save(ignore_permissions=True)
        frappe.db.commit()

        # 8. Clear cache to ensure changes are reflected immediately
        frappe.clear_cache()
        frappe.clear_website_cache()

        frappe.log_message(
            f"Force synced workspace '{WORKSPACE_NAME}' from JSON and cleared cache.",
            "POSAwesome Patch",
        )
    except Exception as e:
        frappe.log_error(
            f"Failed to force sync workspace '{WORKSPACE_NAME}': {e}",
            "POSAwesome Patch Error",
        )
