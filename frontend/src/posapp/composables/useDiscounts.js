export function useDiscounts() {
	const getItemType = (item) => {
		const itemType = (item?.item_type || "").toString().toLowerCase();
		if (itemType && itemType !== "unknown") {
			return itemType;
		}
		if (Number(item?.custom_service_item || 0) === 1) {
			return "service";
		}
		if (Number(item?.is_stock_item || 0) === 1) {
			return "stock";
		}
		return "unknown";
	};

	// -----------------------------
	// Update additional discount amount based on percentage
	// -----------------------------
	const updateDiscountAmount = (context) => {
		const value = flt(context.additional_discount_percentage);

		// Guard invalid values
		if (value < -100 || value > 100) {
			context.additional_discount_percentage = 0;
			context.additional_discount = 0;
			return;
		}

		//  ENFORCE CUSTOMER-TYPE MAX DISCOUNT
		if (context.maxDiscountInfo) {
			const max = context.maxDiscountInfo.invoice_max_discount || 0;

			if (value > max) {
				frappe.show_alert({
					message: __("Maximum allowed discount for this customer is {0}%", [max]),
					indicator: "red",
				});
				context.additional_discount_percentage = max;
			}
		}

		if (context.Total && context.Total !== 0) {
			context.additional_discount = (context.Total * context.additional_discount_percentage) / 100;
		} else {
			context.additional_discount = 0;
		}
	};

	// -----------------------------
	// Calculate prices on field change
	const calcPrices = (item, value, $event, context) => {
		if (!item || !$event?.target?.id) return;

		// ==================================================
		// 🛢 ENGINE OIL — DISCOUNT NOT ALLOWED (HARD BLOCK)
		// ==================================================
		if (getItemType(item) === "engine_oil") {
			item.discount_percentage = 0;
			item.discount_amount = 0;

			// rate must always equal price list rate
			item.rate = context.flt(item.price_list_rate, context.currency_precision);
			item.base_rate = context.flt(
				item.price_list_rate / (context.exchange_rate || 1),
				context.currency_precision,
			);

			item.amount = context.flt(item.qty * item.rate, context.currency_precision);
			item.base_amount = context.flt(
				item.amount / (context.exchange_rate || 1),
				context.currency_precision,
			);

			if (context.forceUpdate) context.forceUpdate();
			return; // ⛔ STOP ALL DISCOUNT LOGIC
		}

		const fieldId = $event.target.id;
		let newValue = flt(value, context.currency_precision);

		// ==================================================
		// 🔒 CUSTOMER TYPE / MAX DISCOUNT VALIDATION (ADDED)
		// ==================================================
		if (
			(fieldId === "discount_percentage" || fieldId === "discount_amount") &&
			typeof context.validateDiscount === "function"
		) {
			let pct = 0;

			if (fieldId === "discount_percentage") {
				pct = flt(newValue);
			}

			if (fieldId === "discount_amount") {
				const gross = item.price_list_rate * item.qty;
				pct = gross ? (flt(newValue) / gross) * 100 : 0;
			}

			if (!context.validateDiscount(item, pct)) {
				item.discount_percentage = 0;
				item.discount_amount = 0;

				// reset rate safely
				item.rate = context.flt(item.price_list_rate, context.currency_precision);
				item.base_rate = context.flt(
					item.price_list_rate / (context.exchange_rate || 1),
					context.currency_precision,
				);

				item.amount = context.flt(item.qty * item.rate, context.currency_precision);
				item.base_amount = context.flt(
					item.amount / (context.exchange_rate || 1),
					context.currency_precision,
				);

				if (context.forceUpdate) context.forceUpdate();
				return; // ⛔ STOP INVALID DISCOUNT
			}
		}

		try {
			// Mark manual rate edits
			if (fieldId === "rate") {
				item._manual_rate_set = true;
			}

			// No negatives
			if (newValue < 0) {
				newValue = 0;
				context.eventBus.emit("show_message", {
					title: __("Negative values not allowed"),
					color: "error",
				});
			}

			const baseCurrency = context.price_list_currency || context.pos_profile.currency;

			const converted_price_list_rate =
				context.selected_currency !== baseCurrency
					? context.flt(
							item.price_list_rate / (context.exchange_rate || 1),
							context.currency_precision,
						)
					: item.price_list_rate;

			switch (fieldId) {
				case "rate":
					item.base_rate = context.flt(
						newValue / (context.exchange_rate || 1),
						context.currency_precision,
					);
					item.rate = newValue;

					item.discount_amount = context.flt(
						converted_price_list_rate - item.rate,
						context.currency_precision,
					);
					item.base_discount_amount = context.flt(
						item.price_list_rate - item.base_rate,
						context.currency_precision,
					);

					if (converted_price_list_rate) {
						item.discount_percentage = context.flt(
							(item.discount_amount / converted_price_list_rate) * 100,
							context.float_precision,
						);
					}
					break;

				case "discount_amount":
					item._manual_discount_set = true;
					item._manual_rate_set = true;

					newValue = Math.min(newValue, converted_price_list_rate);

					item.discount_amount = newValue;
					item.base_discount_amount = context.flt(
						newValue / (context.exchange_rate || 1),
						context.currency_precision,
					);

					item.rate = context.flt(
						converted_price_list_rate - item.discount_amount,
						context.currency_precision,
					);
					item.base_rate = context.flt(
						item.price_list_rate - item.base_discount_amount,
						context.currency_precision,
					);

					if (converted_price_list_rate) {
						item.discount_percentage = context.flt(
							(item.discount_amount / converted_price_list_rate) * 100,
							context.float_precision,
						);
					}
					break;

				case "discount_percentage":
					item._manual_discount_set = true;
					item._manual_rate_set = true;

					newValue = Math.min(newValue, 100);
					item.discount_percentage = context.flt(newValue, context.float_precision);

					item.discount_amount = context.flt(
						(converted_price_list_rate * item.discount_percentage) / 100,
						context.currency_precision,
					);
					item.base_discount_amount = context.flt(
						(item.price_list_rate * item.discount_percentage) / 100,
						context.currency_precision,
					);

					item.rate = context.flt(
						converted_price_list_rate - item.discount_amount,
						context.currency_precision,
					);
					item.base_rate = context.flt(
						item.price_list_rate - item.base_discount_amount,
						context.currency_precision,
					);
					break;
			}

			// Clamp safety
			if (item.rate < 0) {
				item.rate = 0;
				item.base_rate = 0;
				item.discount_amount = converted_price_list_rate;
				item.base_discount_amount = item.price_list_rate;
				item.discount_percentage = 100;
			}

			if (context.calc_stock_qty) {
				context.calc_stock_qty(item, item.qty);
			}
			if (context.forceUpdate) context.forceUpdate();
		} catch (err) {
			console.error("calcPrices error:", err);
			context.eventBus.emit("show_message", {
				title: __("Error calculating prices"),
				color: "error",
			});
		}
	};

	// -----------------------------
	// Final price calculation (currency / reload / offers)
	// -----------------------------
	const calcItemPrice = (item, context) => {
		if (!item) return;

		// Skip double calculation
		if (item._skip_calc) {
			item._skip_calc = false;
			return;
		}

		// ==================================================
		// 🛢 ENGINE OIL — FINAL SAFETY BLOCK
		// ==================================================
		if (getItemType(item) === "engine_oil") {
			item.discount_percentage = 0;
			item.discount_amount = 0;

			item.amount = context.flt(item.qty * item.rate, context.currency_precision);

			const baseCurrency = context.price_list_currency || context.pos_profile.currency;

			item.base_amount =
				context.selected_currency !== baseCurrency
					? context.flt(item.amount / (context.exchange_rate || 1), context.currency_precision)
					: item.amount;

			if (context.forceUpdate) context.forceUpdate();
			return;
		}

		// Locked / offer items
		if (item.locked_price || item.posa_offer_applied) {
			item.amount = context.flt(item.qty * item.rate, context.currency_precision);

			const baseCurrency = context.price_list_currency || context.pos_profile.currency;

			item.base_amount =
				context.selected_currency !== baseCurrency
					? context.flt(item.amount / (context.exchange_rate || 1), context.currency_precision)
					: item.amount;

			if (context.forceUpdate) context.forceUpdate();
			return;
		}

		// Price list conversion
		if (item.price_list_rate) {
			if (!item.base_price_list_rate) {
				item.base_price_list_rate = item.price_list_rate;
				item.base_rate = item.rate;
			}

			const baseCurrency = context.price_list_currency || context.pos_profile.currency;

			if (context.selected_currency !== baseCurrency) {
				item.price_list_rate = context.flt(
					item.base_price_list_rate / (context.exchange_rate || 1),
					context.currency_precision,
				);
				item.rate = context.flt(
					item.base_rate / (context.exchange_rate || 1),
					context.currency_precision,
				);
			} else {
				item.price_list_rate = item.base_price_list_rate;
				item.rate = item.base_rate;
			}
		}

		// Discount calculation (NON-ENGINE OIL ONLY)
		if (item.discount_percentage) {
			const price_list_rate = item.price_list_rate;

			item.discount_amount = context.flt(
				(price_list_rate * item.discount_percentage) / 100,
				context.currency_precision,
			);

			item.rate = context.flt(price_list_rate - item.discount_amount, context.currency_precision);
		}

		// Amounts
		item.amount = context.flt(item.qty * item.rate, context.currency_precision);

		const baseCurrency = context.price_list_currency || context.pos_profile.currency;

		item.base_amount =
			context.selected_currency !== baseCurrency
				? context.flt(item.amount / (context.exchange_rate || 1), context.currency_precision)
				: item.amount;

		if (context.forceUpdate) context.forceUpdate();
	};

	return {
		updateDiscountAmount,
		calcPrices,
		calcItemPrice,
	};
}
