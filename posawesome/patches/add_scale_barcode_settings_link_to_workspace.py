import frappe
import json
import os


def execute():
    if not frappe.db.exists("Workspace", "POS Awesome"):
        return

    # Construct the absolute path to the workspace JSON file
    app_path = frappe.get_app_path("posawesome")
    json_path = os.path.join(
        app_path,
        "posawesome",
        "workspace",
        "pos_awesome",
        "pos_awesome.json",
    )

    if not os.path.exists(json_path):
        frappe.log_error(f"Workspace JSON not found at {json_path}", "POS Awesome Patch")
        return

    with open(json_path, "r") as f:
        workspace_json = json.load(f)

    workspace_links = workspace_json.get("links")

    if workspace_links is None:
        frappe.log_error("No 'links' key found in workspace JSON", "POS Awesome Patch")
        return

    workspace = frappe.get_doc("Workspace", "POS Awesome")

    # Overwrite the links in the document with the ones from the JSON file
    workspace.links = []
    for link_data in workspace_links:
        workspace.append("links", link_data)

    # Re-index the links
    for idx, link in enumerate(workspace.links, start=1):
        link.idx = idx

    try:
        workspace.save(ignore_permissions=True)
        frappe.db.commit()
        frappe.log_message(
            "POS Awesome: Workspace links synced from JSON definition.", "Patch Log"
        )
    except Exception as e:
        frappe.log_error(f"Failed to save workspace: {e}", "POS Awesome Patch Error")
