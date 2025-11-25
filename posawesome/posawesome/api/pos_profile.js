// Copyright (c) 20201 Youssef Restom and contributors
// For license information, please see license.txt

frappe.ui.form.on("POS Profile", {
	setup: function (frm) {

		// Filter to only Cash payment types
		frm.set_query("posa_cash_mode_of_payment", function (doc) {
			return {
				filters: { type: "Cash" },
			};
		});

		// Load language options dynamically
		frappe.call({
			method: "posawesome.posawesome.api.utilities.get_language_options",
			callback: function (r) {
				if (!r.exc) {
					frm.fields_dict["posa_language"].df.options = r.message;
					frm.refresh_field("posa_language");
				}
			},
		});
	},
});


// ✅ Child table script MUST be separate
frappe.ui.form.on("POS Payment Method", {
	mode_of_payment: function (frm, cdt, cdn) {

		let row = locals[cdt][cdn];

		if (!row.mode_of_payment) {
			return;
		}

		frappe.call({
			method: "frappe.client.get",
			args: {
				doctype: "Mode of Payment",
				name: row.mode_of_payment
			},
			callback: function (r) {
				if (r.message && r.message.accounts) {

					// get company from parent POS Profile
					let company = frm.doc.company;

					// find matching account for company
					let acc_row = r.message.accounts.find(acc => acc.company === company);

					if (acc_row) {
						frappe.model.set_value(
							cdt, cdn,
							"custom_account",
							acc_row.default_account || acc_row.account
						);
					}
				}
			}
		});
	}
});
