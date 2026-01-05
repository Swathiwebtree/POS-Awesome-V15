frappe.ui.form.on("Material Request Item", {
    item_code(frm, cdt, cdn) {

        let row = locals[cdt][cdn];

        if (!row.item_code) return;

        frappe.call({
            method: "posawesome.posawesome.api.material_request.get_last_mr_rate",   // update path if in app
            args: {
                item_code: row.item_code
            },
            callback(r) {
                let last_rate = r.message || 0;
                frappe.model.set_value(cdt, cdn, "custom_last_purchase_rate", last_rate);
            }
        });
    }
});
