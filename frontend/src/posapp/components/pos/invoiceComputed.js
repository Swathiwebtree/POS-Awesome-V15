export default {
	// Calculate total quantity of all items
	total_qty() {
		this.close_payments();
		let qty = 0;
		this.items.forEach((item) => {
			qty += this.flt(item.qty || 0);
		});
		const result = this.flt(qty, this.float_precision);
		console.log("[invoiceComputed] total_qty:", result);
		return result;
	},

	// Calculate total amount for all items (before discounts)
	Total() {
		let sum = 0;
		this.items.forEach((item) => {
			// For returns, use absolute value for correct calculation
			const qty = this.isReturnInvoice ? Math.abs(this.flt(item.qty)) : this.flt(item.qty);
			const rate = this.flt(item.rate);
			sum += qty * rate;
		});
		const result = this.flt(sum, this.currency_precision);
		console.log("[invoiceComputed] Total:", result);
		return result;
	},

	// Calculate subtotal (base total without taxes/discounts)
	subtotal() {
		this.close_payments();
		let sum = 0;
		this.items.forEach((item) => {
			// Calculate item amount from qty * rate
			const qty = this.isReturnInvoice ? Math.abs(this.flt(item.qty)) : this.flt(item.qty);
			const rate = this.flt(item.rate);
			sum += qty * rate;
		});

		const result = this.flt(sum, this.currency_precision);
		console.log("[invoiceComputed] subtotal:", result);
		return result;
	},

	// Calculate net total (subtotal + delivery - additional discount)
	net_total() {
		let total = this.subtotal;

		// Add delivery charges
		const delivery_charges = this.flt(this.delivery_charges_rate);
		total += delivery_charges;

		// Subtract additional discount
		const additional_discount = this.flt(this.additional_discount);
		total -= additional_discount;

		const result = this.flt(total, this.currency_precision);
		console.log("[invoiceComputed] net_total:", result);
		return result;
	},

	// Calculate grand total (net_total + taxes - discount_amount)
	grand_total() {
		const subtotal = this.flt(this.subtotal || 0);
		const tax = this.flt(this.total_tax || 0);
		const discount = this.flt(this.discount_amount || 0);
		const delivery = this.flt(this.delivery_charges_rate || 0);

		const total = this.flt(subtotal + tax - discount + delivery);

		console.log("[invoiceComputed] grand_total:", {
			subtotal,
			tax,
			discount,
			delivery,
			result: total,
		});

		return total;
	},

	// Calculate rounded total
	rounded_total() {
		const rounded = this.roundAmount(this.grand_total);
		console.log("[invoiceComputed] rounded_total:", rounded);
		return rounded;
	},

	// Calculate total discount amount for all items
	total_items_discount_amount() {
		let sum = 0;
		this.items.forEach((item) => {
			// For returns, use absolute value for correct calculation
			if (this.isReturnInvoice) {
				sum += Math.abs(this.flt(item.qty)) * this.flt(item.discount_amount);
			} else {
				sum += this.flt(item.qty) * this.flt(item.discount_amount);
			}
		});
		const result = this.flt(sum, this.float_precision);
		console.log("[invoiceComputed] total_items_discount_amount:", result);
		return result;
	},

	// Format posting_date for display as DD-MM-YYYY
	formatted_posting_date: {
		get() {
			if (!this.posting_date) return "";
			const parts = this.posting_date.split("-");
			if (parts.length === 3) {
				return `${parts[2]}-${parts[1]}-${parts[0]}`;
			}
			return this.posting_date;
		},
		set(val) {
			const parts = val.split("-");
			if (parts.length === 3) {
				this.posting_date = `${parts[2]}-${parts[1]}-${parts[0]}`;
			} else {
				this.posting_date = val;
			}
		},
	},

	// Get currency symbol for display
	currencySymbol() {
		return (currency) => {
			return get_currency_symbol(currency || this.selected_currency || this.pos_profile.currency);
		};
	},

	// Get display currency
	displayCurrency() {
		return this.selected_currency || this.pos_profile?.currency || "USD";
	},

	// Determine if current invoice is a return
	isReturnInvoice() {
		return this.invoiceType === "Return" || (this.invoice_doc && this.invoice_doc.is_return);
	},

	// Table headers for item table
	itemTableHeaders() {
		return [
			{
				text: __("Item"),
				value: "item_name",
				width: "35%",
			},
			{
				text: __("Qty"),
				value: "qty",
				width: "15%",
			},
			{
				text: __(`Rate (${this.displayCurrency})`),
				value: "rate",
				width: "20%",
			},
			{
				text: __(`Amount (${this.displayCurrency})`),
				value: "amount",
				width: "20%",
			},
			{
				text: __("Action"),
				value: "actions",
				sortable: false,
				width: "10%",
			},
		];
	},
};
