import frappe


PROFILE_CARD_LABEL = "Profile"
SCALE_BARCODE_LABEL = "Scale Barcode Settings"


def execute():
    if not frappe.db.table_exists("Workspace"):
        return

    if not frappe.db.exists("DocType", SCALE_BARCODE_LABEL):
        return

    if not frappe.db.exists("Workspace", "POS Awesome"):
        return

    workspace = frappe.get_doc("Workspace", "POS Awesome")
    links = workspace.links or []

    existing_link = next((link for link in links if link.link_to == SCALE_BARCODE_LABEL), None)

    if existing_link:
        new_link = existing_link
        new_link.type = "Link"
        new_link.label = SCALE_BARCODE_LABEL
        new_link.link_type = "DocType"
        new_link.hidden = 0
        new_link.is_query_report = 0
        new_link.onboard = 0
    else:
        new_link = workspace.append(
            "links",
            {
                "type": "Link",
                "label": SCALE_BARCODE_LABEL,
                "link_to": SCALE_BARCODE_LABEL,
                "link_type": "DocType",
                "link_count": 0,
                "hidden": 0,
                "is_query_report": 0,
                "onboard": 0,
            },
        )
        links = workspace.links or []

    try:
        current_index = links.index(new_link)
    except ValueError:
        return

    profile_index = None
    for idx, link in enumerate(links):
        if link.type == "Card Break" and link.label == PROFILE_CARD_LABEL:
            profile_index = idx
            break

    if profile_index is not None:
        target_index = profile_index + 1
        while target_index < len(links):
            link = links[target_index]
            if link == new_link:
                break
            if link.type == "Card Break":
                break
            target_index += 1

        if target_index != current_index:
            links.pop(current_index)
            if current_index < target_index:
                target_index -= 1
            links.insert(target_index, new_link)

    profile_card = None
    for link in links:
        if link.type == "Card Break" and link.label == PROFILE_CARD_LABEL:
            profile_card = link
            break

    if profile_card:
        count = 0
        started = False
        for link in links:
            if link == profile_card:
                started = True
                count = 0
                continue
            if started and link.type == "Card Break":
                break
            if started and link.type == "Link":
                count += 1
        profile_card.link_count = count

    for idx, link in enumerate(links, start=1):
        link.idx = idx

    workspace.save(ignore_permissions=True)
