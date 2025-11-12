import json

import frappe


SHORTCUT_LABEL = "Scale Barcode Settings"
SHORTCUT_ID = "ScaleBarcodeShortcut"


def execute():
    if not frappe.db.table_exists("Workspace"):
        return

    if not frappe.db.exists("Workspace", "POS Awesome"):
        return

    workspace = frappe.get_doc("Workspace", "POS Awesome")

    changed = False

    changed |= ensure_shortcut(workspace)
    changed |= ensure_links(workspace)
    changed |= ensure_content(workspace)

    if changed:
        workspace.save(ignore_permissions=True)
        frappe.clear_cache(doctype="Workspace")


def ensure_shortcut(workspace):
    shortcuts = workspace.shortcuts or []
    existing = next((s for s in shortcuts if s.link_to == SHORTCUT_LABEL), None)

    updated = False

    if not existing:
        workspace.append(
            "shortcuts",
            {
                "label": SHORTCUT_LABEL,
                "link_to": SHORTCUT_LABEL,
                "type": "DocType",
                "doc_view": "",
                "color": "Grey",
            },
        )
        shortcuts = workspace.shortcuts or []
        existing = next((s for s in shortcuts if s.link_to == SHORTCUT_LABEL), None)
        updated = True

    if existing and existing.doc_view not in ("", None):
        existing.doc_view = ""
        updated = True

    for idx, shortcut in enumerate(workspace.shortcuts or [], start=1):
        if shortcut.idx != idx:
            shortcut.idx = idx
            updated = True

    return updated


def ensure_links(workspace):
    links = workspace.links or []

    existing = next(
        (
            link
            for link in links
            if link.type == "Link" and link.link_to == SHORTCUT_LABEL
        ),
        None,
    )

    updated = False

    if not existing:
        workspace.append(
            "links",
            {
                "type": "Link",
                "label": SHORTCUT_LABEL,
                "link_to": SHORTCUT_LABEL,
                "link_type": "DocType",
                "link_count": 0,
                "hidden": 0,
                "is_query_report": 0,
                "onboard": 0,
            },
        )
        links = workspace.links or []
        existing = next(
            (
                link
                for link in links
                if link.type == "Link" and link.link_to == SHORTCUT_LABEL
            ),
            None,
        )
        updated = True

    profile_card = next(
        (link for link in links if link.type == "Card Break" and link.label == "Profile"),
        None,
    )

    if profile_card and existing:
        pos_profile_link = next(
            (link for link in links if link.type == "Link" and link.link_to == "POS Profile"),
            None,
        )

        profile_card_index = links.index(profile_card)
        next_card_index = next(
            (idx for idx in range(profile_card_index + 1, len(links)) if links[idx].type == "Card Break"),
            len(links),
        )

        desired_index = profile_card_index + 1
        if pos_profile_link:
            desired_index = links.index(pos_profile_link) + 1
        if desired_index > next_card_index:
            desired_index = next_card_index

        current_index = links.index(existing)
        if current_index != desired_index:
            shortcut_link = links.pop(current_index)
            if current_index < desired_index:
                desired_index -= 1
            links.insert(desired_index, shortcut_link)
            updated = True

    updated |= _update_card_break_count(links, "Profile")
    updated |= _update_card_break_count(links, "POS")

    for idx, link in enumerate(workspace.links or [], start=1):
        if link.idx != idx:
            link.idx = idx
            updated = True

    return updated


def _update_card_break_count(links, label):
    card = next(
        (link for link in links if link.type == "Card Break" and link.label == label),
        None,
    )

    if not card:
        return False

    card_index = links.index(card)
    link_count = 0
    for link in links[card_index + 1 :]:
        if link.type == "Card Break":
            break
        if link.type == "Link":
            link_count += 1

    if card.link_count != link_count:
        card.link_count = link_count
        return True

    return False


def ensure_content(workspace):
    content_raw = workspace.content or "[]"

    try:
        content = json.loads(content_raw)
    except Exception:
        return False

    for block in content:
        if (
            isinstance(block, dict)
            and block.get("type") == "shortcut"
            and block.get("data", {}).get("shortcut_name") == SHORTCUT_LABEL
        ):
            return False

    shortcut_block = {
        "id": SHORTCUT_ID,
        "type": "shortcut",
        "data": {
            "shortcut_name": SHORTCUT_LABEL,
            "col": 3,
        },
    }

    insert_at = None
    for idx, block in enumerate(content):
        if (
            isinstance(block, dict)
            and block.get("type") == "shortcut"
            and block.get("data", {}).get("shortcut_name") == "POS Awesome App"
        ):
            insert_at = idx + 1
            break

    if insert_at is None:
        insert_at = 0

    content.insert(insert_at, shortcut_block)
    workspace.content = json.dumps(content)
    return True
