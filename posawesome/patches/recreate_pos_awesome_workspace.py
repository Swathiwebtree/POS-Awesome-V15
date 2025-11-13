import frappe
import json
import os

WORKSPACE_NAME = "POS Awesome"


def execute():
    print(f"--- Starting Delete and Recreate patch for {WORKSPACE_NAME} ---")

    # 1. Delete the existing workspace document, if it exists
    if frappe.db.exists("Workspace", WORKSPACE_NAME):
        try:
            frappe.delete_doc("Workspace", WORKSPACE_NAME, force=1, ignore_permissions=True)
            frappe.db.commit()
            print(f"Successfully deleted workspace '{WORKSPACE_NAME}'.")
        except Exception as e:
            print(f"Failed to delete workspace '{WORKSPACE_NAME}': {e}")
            # If deletion fails, we cannot proceed
            return

    # 2. Construct the absolute path to the workspace JSON file
    app_path = frappe.get_app_path("posawesome")
    json_path = os.path.join(
        app_path, "posawesome", "workspace", "pos_awesome", "pos_awesome.json"
    )

    if not os.path.exists(json_path):
        print(f"Workspace JSON not found at {json_path}. Cannot recreate.")
        return

    # 3. Read the workspace definition from the JSON file
    with open(json_path, "r") as f:
        workspace_json = json.load(f)

    # 4. Create a new workspace document from the JSON data
    try:
        new_workspace = frappe.get_doc(workspace_json)
        new_workspace.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"Successfully recreated workspace '{WORKSPACE_NAME}' from JSON.")
    except Exception as e:
        print(f"Failed to recreate workspace '{WORKSPACE_NAME}': {e}")
        return

    # 5. Clear cache to ensure changes are reflected
    frappe.clear_cache()
    frappe.clear_website_cache()
    print("--- Finished Delete and Recreate patch successfully. ---")
