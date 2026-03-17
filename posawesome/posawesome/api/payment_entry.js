frappe.ui.form.on("Payment Entry", {
	onload(frm) {
		if (!frm.is_new()) {
			return;
		}

		if (
			frappe.route_options &&
			frappe.route_options.payment_type &&
			frm.doc.payment_type !== frappe.route_options.payment_type
		) {
			frm.set_value("payment_type", frappe.route_options.payment_type);
		}

		frappe.route_options = null;
	},
});
