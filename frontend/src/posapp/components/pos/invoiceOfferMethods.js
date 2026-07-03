import { silentPrint } from "../../plugins/print.js";
import { formatUtils } from "../../format.js";
/* global __, frappe, flt */

export default {
	normalizeBrand(brand) {
		return (brand || "").trim().toLowerCase();
	},
	getItemBrand(item) {
		let brand = this.normalizeBrand(item.brand);
		if (brand) {
			item.brand = brand;
			return brand;
		}
		if (this.brand_cache && this.brand_cache[item.item_code]) {
			brand = this.brand_cache[item.item_code];
		} else {
			frappe.call({
				method: "posawesome.posawesome.api.items.get_item_brand",
				args: { item_code: item.item_code },
				async: false,
				callback: (r) => {
					brand = this.normalizeBrand(r.message);
				},
			});
			this.brand_cache = this.brand_cache || {};
			this.brand_cache[item.item_code] = brand;
		}
		item.brand = brand;
		return brand;
	},
	checkOfferIsAppley(item, offer) {
		let applied = false;
		const item_offers = JSON.parse(item.posa_offers);
		for (const row_id of item_offers) {
			const exist_offer = this.posa_offers.find((el) => row_id == el.row_id);
			if (exist_offer && exist_offer.offer_name == offer.name) {
				applied = true;
				break;
			}
		}
		return applied;
	},

	handelOffers() {
		console.log("[handelOffers] RAW DATA", {
			posOffersLength: this.posOffers?.length,
			couponsLength: this.posa_coupons?.length,
			firstOffer: this.posOffers?.[0],
			firstCoupon: this.posa_coupons?.[0],
			firstItem: this.items?.[0],
		});

		const offers = [];

		(this.posOffers || []).forEach((rawOffer) => {
			console.log("[OFFER LOOP]", {
				name: rawOffer.name,
				apply_on: rawOffer.apply_on,
				item: rawOffer.item,
				item_group: rawOffer.item_group,
				coupon_based: rawOffer.coupon_based,
			});

			const offer = { ...rawOffer };
			const isNormalAppliedOffer = !offer.coupon_based && !!offer.offer_applied;
			const isCouponOffer = !!offer.coupon_based;

			if (!isNormalAppliedOffer && !isCouponOffer) {
				return;
			}
			const applyOn = String(offer.apply_on || "")
				.trim()
				.toLowerCase();

			if (applyOn === "item code") {
				const itemOffer = this.getItemOffer(offer);
				if (itemOffer) offers.push(itemOffer);
			} else if (applyOn === "item group") {
				const groupOffer = this.getGroupOffer(offer);
				if (groupOffer) offers.push(groupOffer);
			} else if (applyOn === "brand") {
				const brandOffer = this.getBrandOffer(offer);
				if (brandOffer) offers.push(brandOffer);
			} else if (applyOn === "transaction") {
				const transactionOffer = this.getTransactionOffer(offer);
				if (transactionOffer) offers.push(transactionOffer);
			}
		});

		console.log("[handelOffers] APPLICABLE OFFERS", offers);

		this.setItemGiveOffer(offers);
		this.updateInvoiceOffers(offers);
		this.updatePosOffers(this.posa_offers);
		this.eventBus.emit("update_pos_coupons", this.posa_offers);
	},

	setItemGiveOffer(offers) {
		// Set item give offer for replace
		offers.forEach((offer) => {
			if (offer.apply_on == "Item Code" && offer.apply_type == "Item Code" && offer.replace_item) {
				offer.give_item = offer.item;
				offer.apply_item_code = offer.item;
			} else if (
				offer.apply_on == "Item Group" &&
				offer.apply_type == "Item Group" &&
				offer.replace_cheapest_item
			) {
				const offerItemCode = this.getCheapestItem(offer).item_code;
				offer.give_item = offerItemCode;
				offer.apply_item_code = offerItemCode;
			}
		});
	},

	getCheapestItem(offer) {
		let itemsRowID;
		if (typeof offer.items === "string") {
			itemsRowID = JSON.parse(offer.items);
		} else {
			itemsRowID = offer.items;
		}
		const itemsList = [];
		itemsRowID.forEach((row_id) => {
			itemsList.push(this.getItemFromRowID(row_id));
		});
		const result = itemsList.reduce(function (res, obj) {
			return !obj.posa_is_replace && !obj.posa_is_offer && obj.price_list_rate < res.price_list_rate
				? obj
				: res;
		});
		return result;
	},

	getItemFromRowID(row_id) {
		const combined = [...this.items, ...this.packed_items];
		return combined.find((el) => el.posa_row_id == row_id);
	},
	normalizeOfferMatchValue(value) {
		return String(value ?? "")
			.trim()
			.toLowerCase();
	},

	checkQtyAnountOffer(offer, qty, amount) {
		let min_qty = false;
		let max_qty = false;
		let min_amt = false;
		let max_amt = false;
		const applys = [];

		if (offer.min_qty || offer.min_qty == 0) {
			if (qty >= offer.min_qty) {
				min_qty = true;
			}
			applys.push(min_qty);
		}

		if (offer.max_qty > 0) {
			if (qty <= offer.max_qty) {
				max_qty = true;
			}
			applys.push(max_qty);
		}

		if (offer.min_amt > 0) {
			if (amount >= offer.min_amt) {
				min_amt = true;
			}
			applys.push(min_amt);
		}

		if (offer.max_amt > 0) {
			if (amount <= offer.max_amt) {
				max_amt = true;
			}
			applys.push(max_amt);
		}
		let apply = false;
		if (!applys.includes(false)) {
			apply = true;
		}
		const res = {
			apply: apply,
			conditions: { min_qty, max_qty, min_amt, max_amt },
		};
		return res;
	},

	checkOfferCoupon(offer) {
		console.log("[checkOfferCoupon]", {
			offer: offer.name,
			coupon_based: offer.coupon_based,
			coupons: this.posa_coupons,
		});

		const hasAppliedCoupon = Array.isArray(this.posa_coupons)
			? this.posa_coupons.some((coupon) => !!coupon.applied)
			: false;

		const hasAppliedOffer = Array.isArray(this.posa_offers)
			? this.posa_offers.some((posOffer) => !!posOffer.offer_applied && !posOffer.coupon_based)
			: false;

		const hasLoyalty = Number(
			this.loyalty_redemption_points ||
				this.loyalty_redemption_amount ||
				this.invoice_doc?.custom_redeemed_loyalty_points ||
				this.invoice_doc?.redeemed_loyalty_points ||
				this.invoice_doc?.redeem_loyalty_points ||
				this.invoice_doc?.loyalty_amount ||
				this.invoice_doc?.loyalty_discount_amount ||
				0,
		);

		if (hasLoyalty > 0) {
			offer.coupon = null;
			offer.coupon_code = null;
			offer.offer_applied = false;
			return false;
		}

		if (hasAppliedCoupon && !offer.coupon_based) {
			offer.coupon = null;
			offer.coupon_code = null;
			offer.offer_applied = false;
			return false;
		}

		if (hasAppliedOffer && offer.coupon_based) {
			offer.coupon = null;
			offer.coupon_code = null;
			offer.offer_applied = false;
			return false;
		}

		if (offer.coupon_based) {
			const coupon = (this.posa_coupons || []).find((el) => {
				if (!el.applied) return false;

				return el.pos_offer === offer.name || el.pos_offer === offer.offer_name;
			});

			if (coupon) {
				console.log("[COUPON MATCHED]", coupon);
				offer.coupon = coupon.coupon;
				offer.coupon_code = coupon.coupon_code;
				offer.offer_applied = true;
				return true;
			}

			console.log("[COUPON NOT MATCHED]", offer);
			offer.coupon = null;
			offer.coupon_code = null;
			offer.offer_applied = false;
			return false;
		}

		// Normal non-coupon offer.
		// Do not reset offer.offer_applied here.
		// Manual APPLY already set offer.offer_applied = true.
		offer.coupon = null;
		offer.coupon_code = null;
		return true;
	},
	applyOfferDiscountAmount(offer, amount) {
		if (!this.invoice_doc) return;
		const discountAmount = Number(amount || 0);
		if (offer.coupon_based) {
			this.invoice_doc.redeemed_coupon_amount = discountAmount;
			this.invoice_doc.redeemed_offer_amount = 0;
			if (this.lockInvoiceDiscountState) {
				this.lockInvoiceDiscountState("coupon", discountAmount);
			}
		} else {
			this.invoice_doc.redeemed_coupon_amount = 0;
			this.invoice_doc.redeemed_offer_amount = discountAmount;
			if (this.lockInvoiceDiscountState) {
				this.lockInvoiceDiscountState("offer", discountAmount);
			}
		}
	},
	clearOfferDiscountAmount(offer) {
		if (!this.invoice_doc) return;
		this.discount_amount = 0;
		this.additional_discount = 0;
		this.additional_discount_percentage = 0;
		this.discount_percentage_offer_name = null;
		if (offer.coupon_based) {
			this.invoice_doc.redeemed_coupon_amount = 0;
			if (this.clearInvoiceDiscountLock) {
				this.clearInvoiceDiscountLock("coupon");
			}
		} else {
			this.invoice_doc.redeemed_offer_amount = 0;
			if (this.clearInvoiceDiscountLock) {
				this.clearInvoiceDiscountLock("offer");
			}
		}
	},
	restoreOfferItemState(item) {
		if (!item) return;

		item.posa_is_offer = 0;
		item.posa_offer_applied = 0;
		item.posa_offers = JSON.stringify([]);
		item.discount_percentage = 0;
		item.discount_amount = 0;
		item.base_discount_amount = 0;
		item.discount_amount_per_item = 0;
		item.is_free_item = 0;

		if (item.original_rate !== undefined && item.original_rate !== null) {
			item.rate = item.original_rate;
		}
		if (item.original_price_list_rate !== undefined && item.original_price_list_rate !== null) {
			item.price_list_rate = item.original_price_list_rate;
		}
		if (item.original_base_rate !== undefined && item.original_base_rate !== null) {
			item.base_rate = item.original_base_rate;
		}
		if (item.original_base_price_list_rate !== undefined && item.original_base_price_list_rate !== null) {
			item.base_price_list_rate = item.original_base_price_list_rate;
		}

		item.original_rate = null;
		item.original_price_list_rate = null;
		item.original_base_rate = null;
		item.original_base_price_list_rate = null;

		if (typeof this.update_item_detail === "function" && item.item_code) {
			this.update_item_detail(item, true);
		}
	},
	getOfferDiscountBaseItems(offer) {
		const combined = [...this.items, ...this.packed_items];
		const offerItems = Array.isArray(offer?.items)
			? offer.items
			: typeof offer?.items === "string"
				? JSON.parse(offer.items || "[]")
				: [];

		if (!Array.isArray(offerItems) || !offerItems.length) {
			return [];
		}

		return combined.filter((item) => item && offerItems.includes(item.posa_row_id));
	},
	getOfferDiscountAmount(offer) {
		if (!offer) return 0;

		const items = this.getOfferDiscountBaseItems(offer);
		if (!items.length) return 0;

		const baseCurrency = this.price_list_currency || this.pos_profile.currency;
		const selectedCurrency = this.selected_currency || baseCurrency;
		const currencyFactor = selectedCurrency !== baseCurrency ? this.exchange_rate || 1 : 1;

		const grossAmount = items.reduce((total, item) => {
			return total + this.flt(Number(item.qty || 0) * Number(item.rate || 0), this.currency_precision);
		}, 0);

		if (offer.discount_type === "Rate") {
			const targetRate =
				selectedCurrency !== baseCurrency
					? this.flt(Number(offer.rate || 0) * currencyFactor, this.currency_precision)
					: this.flt(Number(offer.rate || 0), this.currency_precision);
			const targetAmount = items.reduce((total, item) => {
				return total + this.flt(Number(item.qty || 0) * targetRate, this.currency_precision);
			}, 0);
			return Math.max(0, this.flt(grossAmount - targetAmount, this.currency_precision));
		}

		if (offer.discount_type === "Discount Percentage") {
			return this.flt(
				(grossAmount * Number(offer.discount_percentage || 0)) / 100,
				this.currency_precision,
			);
		}

		if (offer.discount_type === "Discount Amount") {
			return this.flt(Number(offer.discount_amount || 0), this.currency_precision);
		}

		return 0;
	},
	syncInvoiceLevelOfferDiscount(offer, discountAmount) {
		const amount = this.flt(Number(discountAmount || 0), this.currency_precision);

		this.discount_amount = amount;
		this.additional_discount = amount;
		this.additional_discount_percentage = this.Total
			? this.flt((amount / this.Total) * 100, this.currency_precision)
			: 0;

		if (offer?.offer === "Grand Total" || offer?.discount_type === "Discount Percentage") {
			this.discount_percentage_offer_name = offer.name || offer.offer_name || null;
		}

		this.applyOfferDiscountAmount(offer, amount);
		this.apply_additional_discount();
	},
	getItemOffer(offer) {
		console.log("[getItemOffer] called", offer);

		let apply_offer = null;
		const combined = [...this.items, ...this.packed_items];
		let matchedItems = [];
		const targetItem = this.normalizeOfferMatchValue(offer.item);

		if (
			String(offer.apply_on || "")
				.trim()
				.toLowerCase() === "item code"
		) {
			if (this.checkOfferCoupon(offer)) {
				combined.forEach((item) => {
					console.log("[ITEM MATCH CHECK]", {
						cart_item: item.item_code,
						offer_item: offer.item,
					});

					const rowCandidates = [
						item.item_code,
						item.item_name,
						item.name,
						item.item_name_display,
					].map((value) => this.normalizeOfferMatchValue(value));

					if (!item.posa_is_offer && rowCandidates.includes(targetItem)) {
						if (
							offer.offer === "Item Price" &&
							item.posa_offer_applied &&
							!this.checkOfferIsAppley(item, offer)
						) {
							return;
						}

						const items = [];
						const rate = item.original_price_list_rate || item.price_list_rate;
						const qty = item.stock_qty || item.qty || 1;
						const res = this.checkQtyAnountOffer(offer, qty, qty * rate);

						console.log("[ITEM OFFER CONDITION]", {
							item: item.item_code,
							qty,
							rate,
							res,
						});

						if (res.apply || offer.coupon_based) {
							items.push(item.posa_row_id);
							offer.items = items;
							matchedItems = items;
							apply_offer = offer;
						}
					}
				});

				if (offer.coupon_based && matchedItems.length) {
					offer.items = matchedItems;
					apply_offer = offer;
				}
			}
		}

		if (!apply_offer) {
			const sourceOffer = (this.posOffers || []).find((row) => row.row_id === offer.row_id);
			if (sourceOffer) {
				sourceOffer.offer_applied = false;
				sourceOffer.coupon = null;
				sourceOffer.coupon_code = null;
			}
			if (offer.apply_on === "Item Code" && targetItem) {
				this.eventBus.emit("show_message", {
					title: __("Offer applies only to {0}", [offer.item]),
					color: "warning",
				});
			}
		}

		console.log("[getItemOffer] RESULT", apply_offer);
		return apply_offer;
	},

	getGroupOffer(offer) {
		let apply_offer = null;
		if (offer.apply_on === "Item Group") {
			if (this.checkOfferCoupon(offer)) {
				const items = [];
				let total_count = 0;
				let total_amount = 0;
				const combined = [...this.items, ...this.packed_items];
				combined.forEach((item) => {
					if (
						!item.posa_is_offer &&
						String(item.item_group || "")
							.trim()
							.toLowerCase() ===
							String(offer.item_group || "")
								.trim()
								.toLowerCase()
					) {
						if (
							offer.offer === "Item Price" &&
							item.posa_offer_applied &&
							!this.checkOfferIsAppley(item, offer)
						) {
							return;
						}
						total_count += item.stock_qty;
						const rate = item.original_price_list_rate || item.price_list_rate;
						total_amount += item.stock_qty * rate;
						items.push(item.posa_row_id);
					}
				});
				if (total_count || total_amount) {
					const res = this.checkQtyAnountOffer(offer, total_count, total_amount);
					if (res.apply || offer.coupon_based) {
						offer.items = items;
						apply_offer = offer;
					}
				}

				if (offer.coupon_based && items.length) {
					offer.items = items;
					apply_offer = offer;
				}
			}
		}
		return apply_offer;
	},

	getBrandOffer(offer) {
		let apply_offer = null;
		if (offer.apply_on === "Brand") {
			if (this.checkOfferCoupon(offer)) {
				const items = [];
				let total_count = 0;
				let total_amount = 0;
				const offer_brand = this.normalizeBrand(offer.brand);
				const combined = [...this.items, ...this.packed_items];
				combined.forEach((item) => {
					const item_brand = this.getItemBrand(item);
					if (!item.posa_is_offer && item_brand && item_brand === offer_brand) {
						if (
							offer.offer === "Item Price" &&
							item.posa_offer_applied &&
							!this.checkOfferIsAppley(item, offer)
						) {
							return;
						}
						total_count += item.stock_qty;
						const rate = item.original_price_list_rate || item.price_list_rate;
						total_amount += item.stock_qty * rate;
						items.push(item.posa_row_id);
					}
				});
				if (total_count || total_amount) {
					const res = this.checkQtyAnountOffer(offer, total_count, total_amount);
					if (res.apply || offer.coupon_based) {
						offer.items = items;
						apply_offer = offer;
					}
				}

				if (offer.coupon_based && items.length) {
					offer.items = items;
					apply_offer = offer;
				}
			}
		}
		return apply_offer;
	},
	getTransactionOffer(offer) {
		let apply_offer = null;
		if (offer.apply_on === "Transaction") {
			if (this.checkOfferCoupon(offer)) {
				const combined = [...this.items, ...this.packed_items];
				let total_qty = 0;
				let total_amount = 0;
				const items = [];
				combined.forEach((item) => {
					if (!item.posa_is_offer && !item.posa_is_replace) {
						total_qty += item.stock_qty;
						const rate = item.original_price_list_rate || item.price_list_rate;
						total_amount += item.stock_qty * rate;
						items.push(item.posa_row_id);
					}
				});
				const total_count = total_qty;
				if (total_count || total_amount) {
					const res = this.checkQtyAnountOffer(offer, total_count, total_amount);
					if (res.apply || offer.coupon_based) {
						offer.items = items;
						apply_offer = offer;
					}
				}

				if (offer.coupon_based && items.length) {
					offer.items = items;
					apply_offer = offer;
				}
			}
		}
		return apply_offer;
	},

	updatePosOffers(offers) {
		this.eventBus.emit("update_pos_offers", offers);
	},

	updateInvoiceOffers(offers) {
		this.posa_offers.forEach((invoiceOffer) => {
			const existOffer = offers.find((offer) => invoiceOffer.row_id == offer.row_id);
			if (!existOffer) {
				this.removeApplyOffer(invoiceOffer);
			}
		});
		offers.forEach((offer) => {
			if (!offer.items || !offer.items.length) {
				if (
					String(offer.apply_on || "")
						.trim()
						.toLowerCase() === "item code"
				) {
					offer = this.getItemOffer(offer) || offer;
				}
			}
			const existOffer = this.posa_offers.find((invoiceOffer) => invoiceOffer.row_id == offer.row_id);
			if (existOffer) {
				existOffer.items = JSON.stringify(offer.items);
				existOffer.offer_applied = !!offer.offer_applied || (!!offer.coupon_based && !!offer.coupon);
				existOffer.coupon = offer.coupon || existOffer.coupon || null;
				existOffer.coupon_code = offer.coupon_code || existOffer.coupon_code || null;
				existOffer.pos_offer = offer.name || offer.offer_name || existOffer.pos_offer || null;
				existOffer.name = offer.name || existOffer.name || null;
				if (
					existOffer.offer === "Give Product" &&
					existOffer.give_item &&
					existOffer.give_item != offer.give_item
				) {
					const combined = [...this.items, ...this.packed_items];
					const item_to_remove = combined.find(
						(item) => item.posa_row_id == existOffer.give_item_row_id,
					);
					if (item_to_remove) {
						const updated_item_offers = offer.items.filter(
							(row_id) => row_id != item_to_remove.posa_row_id,
						);
						offer.items = updated_item_offers;
						const collection = this.items.includes(item_to_remove)
							? this.items
							: this.packed_items;
						const idx = collection.findIndex(
							(el) => el.posa_row_id == item_to_remove.posa_row_id,
						);
						if (idx > -1) collection.splice(idx, 1);
						existOffer.give_item_row_id = null;
						existOffer.give_item = null;
					}
					const newItemOffer = this.ApplyOnGiveProduct(offer);
					if (offer.replace_cheapest_item) {
						const cheapestItem = this.getCheapestItem(offer);
						const oldBaseItem = combined.find(
							(el) => el.posa_row_id == item_to_remove.posa_is_replace,
						);
						newItemOffer.qty = item_to_remove.qty;
						if (oldBaseItem && !oldBaseItem.posa_is_replace) {
							oldBaseItem.qty += item_to_remove.qty;
						} else {
							const restoredItem = this.ApplyOnGiveProduct(
								{
									given_qty: item_to_remove.qty,
								},
								item_to_remove.item_code,
							);
							restoredItem.posa_is_offer = 0;
							this.items.unshift(restoredItem);
						}
						newItemOffer.posa_is_offer = 0;
						newItemOffer.posa_is_replace = cheapestItem.posa_row_id;
						const diffQty = cheapestItem.qty - newItemOffer.qty;
						if (diffQty <= 0) {
							newItemOffer.qty += diffQty;
							const baseCollection = this.items.includes(cheapestItem)
								? this.items
								: this.packed_items;
							const baseIndex = baseCollection.findIndex(
								(el) => el.posa_row_id == cheapestItem.posa_row_id,
							);
							if (baseIndex > -1) baseCollection.splice(baseIndex, 1);
							newItemOffer.posa_row_id = cheapestItem.posa_row_id;
							newItemOffer.posa_is_replace = newItemOffer.posa_row_id;
						} else {
							cheapestItem.qty = diffQty;
						}
					}
					this.items.unshift(newItemOffer);
					existOffer.give_item_row_id = newItemOffer.posa_row_id;
					existOffer.give_item = newItemOffer.item_code;
				} else if (
					existOffer.offer === "Give Product" &&
					existOffer.give_item &&
					existOffer.give_item == offer.give_item &&
					(offer.replace_item || offer.replace_cheapest_item)
				) {
					this.$nextTick(function () {
						const offerItem = this.getItemFromRowID(existOffer.give_item_row_id);
						const diff = offer.given_qty - offerItem.qty;
						if (diff > 0) {
							const itemsRowID = JSON.parse(existOffer.items);
							const itemsList = [];
							itemsRowID.forEach((row_id) => {
								itemsList.push(this.getItemFromRowID(row_id));
							});
							const existItem = itemsList.find(
								(el) =>
									el.item_code == offerItem.item_code &&
									el.posa_is_replace != offerItem.posa_row_id,
							);
							if (existItem) {
								const diffExistQty = existItem.qty - diff;
								if (diffExistQty > 0) {
									offerItem.qty += diff;
									existItem.qty -= diff;
								} else {
									offerItem.qty += existItem.qty;
									const col = this.items.includes(existItem)
										? this.items
										: this.packed_items;
									const idx2 = col.findIndex(
										(el) => el.posa_row_id == existItem.posa_row_id,
									);
									if (idx2 > -1) col.splice(idx2, 1);
								}
							}
						}
					});
				} else if (existOffer.offer === "Item Price") {
					this.ApplyOnPrice(offer);
				} else if (existOffer.offer === "Grand Total") {
					this.ApplyOnTotal(offer);
				}
				this.addOfferToItems(existOffer);
			} else {
				this.applyNewOffer(offer);
			}
		});
	},
	removeAppliedOffer(offerName = null) {
		const nextOffers = (this.posOffers || []).map((offer) => {
			if (!offer.offer_applied || offer.coupon_based) {
				return { ...offer };
			}

			if (
				offerName &&
				offerName !== offer.row_id &&
				offerName !== offer.name &&
				offerName !== offer.offer_name
			) {
				return { ...offer };
			}

			return {
				...offer,
				offer_applied: false,
				coupon: null,
				coupon_code: null,
			};
		});

		this.eventBus.emit("update_pos_offers", nextOffers);
	},

	removeApplyOffer(invoiceOffer) {
		const offerItems = this.getOfferDiscountBaseItems(invoiceOffer);
		offerItems.forEach((item) => {
			this.restoreOfferItemState(item);
		});

		if (invoiceOffer.offer === "Item Price") {
			this.RemoveOnPrice(invoiceOffer);
			this.clearOfferDiscountAmount(invoiceOffer);
			const index = this.posa_offers.findIndex((el) => el.row_id === invoiceOffer.row_id);
			this.posa_offers.splice(index, 1);
		}
		if (invoiceOffer.offer === "Give Product") {
			const combined = [...this.items, ...this.packed_items];
			const item_to_remove = combined.find((item) => item.posa_row_id == invoiceOffer.give_item_row_id);
			const index = this.posa_offers.findIndex((el) => el.row_id === invoiceOffer.row_id);
			this.posa_offers.splice(index, 1);
			if (item_to_remove) {
				const collection = this.items.includes(item_to_remove) ? this.items : this.packed_items;
				const idx = collection.findIndex((el) => el.posa_row_id == item_to_remove.posa_row_id);
				if (idx > -1) collection.splice(idx, 1);
			}
		}
		if (invoiceOffer.offer === "Grand Total") {
			this.RemoveOnTotal(invoiceOffer);
			this.clearOfferDiscountAmount(invoiceOffer);
			const index = this.posa_offers.findIndex((el) => el.row_id === invoiceOffer.row_id);
			this.posa_offers.splice(index, 1);
		}
		if (invoiceOffer.offer === "Loyalty Point") {
			const index = this.posa_offers.findIndex((el) => el.row_id === invoiceOffer.row_id);
			this.posa_offers.splice(index, 1);
		}
		if (this.invoice_doc) {
			if (invoiceOffer.coupon_based) {
				this.invoice_doc.redeemed_coupon_amount = 0;
			} else {
				this.invoice_doc.redeemed_offer_amount = 0;
			}
		}
		this.discount_amount = 0;
		this.additional_discount = 0;
		this.additional_discount_percentage = 0;
		this.discount_percentage_offer_name = null;
		this.deleteOfferFromItems(invoiceOffer);
	},

	applyNewOffer(offer) {
		this.isApplyingOffer = true;
		if (offer.offer === "Item Price") {
			this.ApplyOnPrice(offer);
		}
		if (offer.offer === "Give Product") {
			let itemsRowID;
			if (typeof offer.items === "string") {
				itemsRowID = JSON.parse(offer.items);
			} else {
				itemsRowID = offer.items;
			}
			if (offer.apply_on == "Item Code" && offer.apply_type == "Item Code" && offer.replace_item) {
				const item = this.ApplyOnGiveProduct(offer, offer.item);
				item.posa_is_replace = itemsRowID[0];
				const combined = [...this.items, ...this.packed_items];
				const baseItem = combined.find((el) => el.posa_row_id == item.posa_is_replace);
				const diffQty = baseItem.qty - offer.given_qty;
				item.posa_is_offer = 0;
				if (diffQty <= 0) {
					item.qty = baseItem.qty;
					const collection = this.items.includes(baseItem) ? this.items : this.packed_items;
					const idx = collection.findIndex((el) => el.posa_row_id == baseItem.posa_row_id);
					if (idx > -1) collection.splice(idx, 1);
					item.posa_row_id = item.posa_is_replace;
				} else {
					baseItem.qty = diffQty;
				}
				this.items.unshift(item);
				offer.give_item_row_id = item.posa_row_id;
			} else if (
				offer.apply_on == "Item Group" &&
				offer.apply_type == "Item Group" &&
				offer.replace_cheapest_item
			) {
				const itemsList = [];
				itemsRowID.forEach((row_id) => {
					itemsList.push(this.getItemFromRowID(row_id));
				});
				const baseItem = itemsList.find((el) => el.item_code == offer.give_item);
				const item = this.ApplyOnGiveProduct(offer, offer.give_item);
				item.posa_is_offer = 0;
				item.posa_is_replace = baseItem.posa_row_id;
				const diffQty = baseItem.qty - offer.given_qty;
				if (diffQty <= 0) {
					item.qty = baseItem.qty;
					const collection = this.items.includes(baseItem) ? this.items : this.packed_items;
					const idx = collection.findIndex((el) => el.posa_row_id == baseItem.posa_row_id);
					if (idx > -1) collection.splice(idx, 1);
					item.posa_row_id = item.posa_is_replace;
				} else {
					baseItem.qty = diffQty;
				}
				this.items.unshift(item);
				offer.give_item_row_id = item.posa_row_id;
			} else {
				const item = this.ApplyOnGiveProduct(offer);
				this.items.unshift(item);
				if (item) {
					offer.give_item_row_id = item.posa_row_id;
				}
			}
		}
		if (offer.offer === "Grand Total") {
			this.ApplyOnTotal(offer);
		}
		if (offer.offer === "Loyalty Point") {
			this.eventBus.emit("show_message", {
				title: __("Loyalty Point Offer Applied"),
				color: "success",
			});
		}

		const newOffer = {
			offer_name: offer.name,
			name: offer.name,
			row_id: offer.row_id,
			apply_on: offer.apply_on,
			offer: offer.offer,
			items: JSON.stringify(offer.items || []),
			give_item: offer.give_item,
			give_item_row_id: offer.give_item_row_id,
			offer_applied: true,
			coupon_based: offer.coupon_based,
			coupon: offer.coupon || null,
			coupon_code: offer.coupon_code || null,
			pos_offer: offer.name,
		};
		this.posa_offers.push(newOffer);
		this.addOfferToItems(newOffer);
		this.isApplyingOffer = false;
	},

	ApplyOnGiveProduct(offer, item_code) {
		if (!item_code) {
			item_code = offer.give_item;
		}
		const items = this.allItems;
		const item = items.find((item) => item.item_code == item_code);
		if (!item) {
			return;
		}
		const new_item = { ...item };
		new_item.qty = offer.given_qty;
		new_item.stock_qty = offer.given_qty;

		// Handle rate based on currency
		if (offer.discount_type === "Rate") {
			// offer.rate is always in base currency (PKR)
			new_item.base_rate = offer.rate;
			const baseCurrency = this.price_list_currency || this.pos_profile.currency;
			if (this.selected_currency !== baseCurrency) {
				// If exchange rate is 300 PKR = 1 USD
				// Convert PKR to USD by multiplying
				new_item.rate = this.flt(offer.rate * this.exchange_rate, this.currency_precision);
			} else {
				new_item.rate = offer.rate;
			}
		} else if (offer.discount_type === "Discount Percentage") {
			// Apply percentage discount on item's base rate
			const base_price = item.base_rate || item.rate / this.exchange_rate;
			const base_discount = this.flt(
				(base_price * offer.discount_percentage) / 100,
				this.currency_precision,
			);
			new_item.base_discount_amount = base_discount;
			new_item.base_rate = this.flt(base_price - base_discount, this.currency_precision);

			const baseCurrency = this.price_list_currency || this.pos_profile.currency;
			if (this.selected_currency !== baseCurrency) {
				new_item.discount_amount = this.flt(
					base_discount * this.exchange_rate,
					this.currency_precision,
				);
				new_item.rate = this.flt(new_item.base_rate * this.exchange_rate, this.currency_precision);
			} else {
				new_item.discount_amount = base_discount;
				new_item.rate = new_item.base_rate;
			}
		} else {
			// Use item's original rate
			const baseCurrency = this.price_list_currency || this.pos_profile.currency;
			if (this.selected_currency !== baseCurrency) {
				new_item.base_rate = item.base_rate || item.rate / this.exchange_rate;
				new_item.rate = item.rate;
			} else {
				new_item.base_rate = item.rate;
				new_item.rate = item.rate;
			}
		}

		// Handle discount amount based on currency
		if (offer.discount_type === "Discount Amount") {
			// offer.discount_amount is always in base currency (PKR)
			new_item.base_discount_amount = offer.discount_amount;
			const baseCurrency = this.price_list_currency || this.pos_profile.currency;
			if (this.selected_currency !== baseCurrency) {
				// Convert PKR to USD by multiplying
				new_item.discount_amount = this.flt(
					offer.discount_amount * this.exchange_rate,
					this.currency_precision,
				);
			} else {
				new_item.discount_amount = offer.discount_amount;
			}
		} else if (offer.discount_type !== "Discount Percentage") {
			new_item.base_discount_amount = 0;
			new_item.discount_amount = 0;
		}

		new_item.discount_percentage =
			offer.discount_type === "Discount Percentage" ? offer.discount_percentage : 0;
		new_item.discount_amount_per_item = 0;
		new_item.uom = item.uom ? item.uom : item.stock_uom;
		new_item.actual_batch_qty = "";
		new_item.conversion_factor = 1;
		new_item.posa_offers = JSON.stringify([]);
		new_item.posa_offer_applied =
			offer.discount_type === "Rate" ||
			offer.discount_type === "Discount Amount" ||
			offer.discount_type === "Discount Percentage"
				? 1
				: 0;
		new_item.posa_is_offer = 1;
		new_item.posa_is_replace = null;
		new_item.posa_notes = "";
		new_item.posa_delivery_date = "";

		// Handle free items
		const is_free =
			(offer.discount_type === "Rate" && !offer.rate) ||
			(offer.discount_type === "Discount Percentage" && offer.discount_percentage == 100);

		new_item.is_free_item = is_free ? 1 : 0;

		// Set price list rate based on currency similar to invoice logic
		if (is_free) {
			new_item.base_price_list_rate = 0;
			new_item.price_list_rate = 0;
		} else {
			// Use the item's price list rate if available
			new_item.price_list_rate = item.price_list_rate || item.rate;
			// Determine base price list rate just like invoice items
			const baseCurrency = this.price_list_currency || this.pos_profile.currency;
			if (this.selected_currency !== baseCurrency) {
				new_item.base_price_list_rate = this.flt(
					item.base_price_list_rate !== undefined
						? item.base_price_list_rate
						: item.rate / this.exchange_rate,
					this.currency_precision,
				);
			} else {
				new_item.base_price_list_rate =
					item.base_price_list_rate !== undefined ? item.base_price_list_rate : item.rate;
			}
		}

		new_item.posa_row_id = this.makeid(20);

		if ((!this.pos_profile.posa_auto_set_batch && new_item.has_batch_no) || new_item.has_serial_no) {
			// Store only the item's row ID for the expanded state
			this.expanded.push(new_item.posa_row_id);
		}

		this.update_item_detail(new_item);
		return new_item;
	},

	ApplyOnPrice(offer) {
		if (!offer) return;

		const items = this.getOfferDiscountBaseItems(offer);
		let discountAmount = 0;

		if (!items.length) return;

		items.forEach((item) => {
			const qty = Number(item.qty || item.stock_qty || 1);
			const rate = Number(item.rate || item.price_list_rate || 0);

			let itemDiscount = 0;

			if (offer.discount_type === "Discount Percentage") {
				itemDiscount = this.flt(
					(rate * qty * Number(offer.discount_percentage || 0)) / 100,
					this.currency_precision,
				);
				item.discount_percentage = Number(offer.discount_percentage || 0);
			} else if (offer.discount_type === "Discount Amount") {
				itemDiscount = this.flt(Number(offer.discount_amount || 0), this.currency_precision);
				item.discount_percentage = 0;
			}

			item.discount_amount = itemDiscount;
			item.base_discount_amount = itemDiscount;
			item.amount = this.flt(rate * qty - itemDiscount, this.currency_precision);
			item.base_amount = item.amount;

			item.posa_offer_applied = 1;
			item.posa_is_offer = 1;
			item.posa_offers = JSON.stringify([offer.row_id]);

			discountAmount += itemDiscount;

			if (typeof this.calc_item_price === "function") {
				this.calc_item_price(item);
			}
		});

		offer.offer_applied = true;

		if (offer.coupon_based) {
			this.invoice_doc.redeemed_coupon_amount = discountAmount;
			this.invoice_doc.redeemed_offer_amount = 0;
		} else {
			this.invoice_doc.redeemed_offer_amount = discountAmount;
			this.invoice_doc.redeemed_coupon_amount = 0;
		}

		this.discount_amount = discountAmount;
		this.additional_discount = discountAmount;
		this.additional_discount_percentage = this.Total
			? this.flt((discountAmount / this.Total) * 100, this.currency_precision)
			: 0;

		this.apply_additional_discount();
		this.$forceUpdate();
	},

	RemoveOnPrice(offer) {
		if (!offer) return;
		this.clearOfferDiscountAmount(offer);
		this.apply_additional_discount();
	},

	ApplyOnTotal(offer) {
		if (!offer.name) {
			offer = this.posOffers.find((el) => el.name == offer.offer_name);
		}
		if (this.discount_percentage_offer_name === offer.name && this.discount_amount !== 0) {
			return;
		}
		if (this.discount_percentage_offer_name && this.discount_percentage_offer_name !== offer.name) {
			return;
		}

		const discountAmount = this.getOfferDiscountAmount(offer);
		if (discountAmount <= 0 && !offer.coupon_based) {
			return;
		}

		this.discount_percentage_offer_name = offer.name;
		this.syncInvoiceLevelOfferDiscount(offer, discountAmount);
	},

	RemoveOnTotal(offer) {
		if (this.discount_percentage_offer_name && this.discount_percentage_offer_name == offer.offer_name) {
			this.discount_amount = 0;
			this.discount_percentage_offer_name = null;

			// Reset invoice discount fields when offer is removed
			this.additional_discount = 0;
			this.additional_discount_percentage = 0;
			this.clearOfferDiscountAmount(offer);
			this.apply_additional_discount();
		}
	},

	addOfferToItems(offer) {
		if (!offer || !offer.items) return;

		try {
			const offer_items = typeof offer.items === "string" ? JSON.parse(offer.items) : offer.items;
			if (!Array.isArray(offer_items)) return;

			const combined = [...this.items, ...this.packed_items];
			offer_items.forEach((el) => {
				combined.forEach((exist_item) => {
					if (!exist_item || !exist_item.posa_row_id) return;

					if (exist_item.posa_row_id == el) {
						const item_offers = exist_item.posa_offers ? JSON.parse(exist_item.posa_offers) : [];
						if (!Array.isArray(item_offers)) return;

						if (!item_offers.includes(offer.row_id)) {
							item_offers.push(offer.row_id);
							exist_item.posa_offer_applied = 1;
						}
						exist_item.posa_offers = JSON.stringify(item_offers);
					}
				});
			});
		} catch (error) {
			console.error("Error adding offer to items:", error);
			this.eventBus.emit("show_message", {
				title: __("Error adding offer to items"),
				color: "error",
				message: error.message,
			});
		}
	},

	deleteOfferFromItems(offer) {
		if (!offer || !offer.items) return;

		try {
			const offer_items = typeof offer.items === "string" ? JSON.parse(offer.items) : offer.items;
			if (!Array.isArray(offer_items)) return;

			const combined = [...this.items, ...this.packed_items];
			offer_items.forEach((el) => {
				combined.forEach((exist_item) => {
					if (!exist_item || !exist_item.posa_row_id) return;

					if (exist_item.posa_row_id == el) {
						const item_offers = exist_item.posa_offers ? JSON.parse(exist_item.posa_offers) : [];
						if (!Array.isArray(item_offers)) return;

						const updated_item_offers = item_offers.filter((row_id) => row_id != offer.row_id);
						if (updated_item_offers.length === 0) {
							exist_item.posa_offer_applied = 0;
						}
						exist_item.posa_offers = JSON.stringify(updated_item_offers);
					}
				});
			});
		} catch (error) {
			console.error("Error deleting offer from items:", error);
			this.eventBus.emit("show_message", {
				title: __("Error deleting offer from items"),
				color: "error",
				message: error.message,
			});
		}
	},

	validate_due_date(item) {
		const today = frappe.datetime.now_date();
		const parse_today = Date.parse(today);
		// Convert to backend format for comparison
		const backend_date = this.formatDateForBackend(item.posa_delivery_date);
		const new_date = Date.parse(backend_date);
		if (isNaN(new_date) || new_date < parse_today) {
			setTimeout(() => {
				item.posa_delivery_date = this.formatDateForDisplay(today);
			}, 0);
		} else {
			item.posa_delivery_date = this.formatDateForDisplay(backend_date);
		}
	},
	load_print_page(invoice_name) {
		const print_format = this.pos_profile.print_format_for_online || this.pos_profile.print_format;
		// POS should always print without letterhead.
		const no_letterhead = 1;
		const doctype = this.pos_profile.create_pos_invoice_instead_of_sales_invoice
			? "POS Invoice"
			: "Sales Invoice";
		const url =
			frappe.urllib.get_base_url() +
			"/printview?doctype=" +
			encodeURIComponent(doctype) +
			"&name=" +
			invoice_name +
			"&trigger_print=1" +
			"&format=" +
			print_format +
			"&no_letterhead=" +
			no_letterhead;

		if (this.pos_profile.posa_silent_print) {
			silentPrint(url);
		} else {
			const printWindow = window.open(url, "Print");
			printWindow.addEventListener(
				"load",
				function () {
					printWindow.print();
				},
				{ once: true },
			);
		}
	},

	formatDateForBackend(date) {
		if (!date) return null;
		if (typeof date === "string") {
			const western = formatUtils.fromArabicNumerals(date);
			if (/^\d{4}-\d{2}-\d{2}$/.test(western)) {
				return western;
			}
			if (/^\d{1,2}-\d{1,2}-\d{4}$/.test(western)) {
				const [d, m, y] = western.split("-");
				return `${y}-${m.padStart(2, "0")}-${d.padStart(2, "0")}`;
			}
			date = western;
		}
		const d = new Date(formatUtils.fromArabicNumerals(String(date)));
		if (!isNaN(d.getTime())) {
			const year = d.getFullYear();
			const month = `0${d.getMonth() + 1}`.slice(-2);
			const day = `0${d.getDate()}`.slice(-2);
			return `${year}-${month}-${day}`;
		}
		return formatUtils.fromArabicNumerals(String(date));
	},

	formatDateForDisplay(date) {
		if (!date) return "";
		const western = formatUtils.fromArabicNumerals(String(date));
		if (typeof date === "string" && /^\d{4}-\d{2}-\d{2}$/.test(western)) {
			const [y, m, d] = western.split("-");
			return formatUtils.toArabicNumerals(`${d}-${m}-${y}`);
		}
		const d = new Date(western);
		if (!isNaN(d.getTime())) {
			const year = d.getFullYear();
			const month = `0${d.getMonth() + 1}`.slice(-2);
			const day = `0${d.getDate()}`.slice(-2);
			return formatUtils.toArabicNumerals(`${day}-${month}-${year}`);
		}
		return formatUtils.toArabicNumerals(western);
	},

	toggleOffer(item) {
		this.$nextTick(() => {
			if (item.posa_offer_applied) {
				// Remove applied offer and restore original pricing
				item.posa_is_offer = 1;
				item.posa_offers = JSON.stringify([]);
				item.posa_offer_applied = 0;
				item.discount_percentage = 0;
				item.discount_amount = 0;
				item.base_discount_amount = 0;

				// Restore previous rates if stored, adjusted for current UOM
				const cf = flt(item.conversion_factor || 1);
				item.rate = item.original_rate ? item.original_rate * cf : item.price_list_rate;
				item.price_list_rate = item.original_price_list_rate
					? item.original_price_list_rate * cf
					: item.price_list_rate;
				item.base_rate = item.original_base_rate ? item.original_base_rate * cf : item.base_rate;
				item.base_price_list_rate = item.original_base_price_list_rate
					? item.original_base_price_list_rate * cf
					: item.base_price_list_rate;

				// Clear stored original rates
				item.original_rate = null;
				item.original_price_list_rate = null;
				item.original_base_rate = null;
				item.original_base_price_list_rate = null;

				this.calc_item_price(item);
				this.handelOffers();
			} else {
				// Allow offers to be applied
				item.posa_is_offer = 0;
				this.handelOffers();
			}

			// Ensure Vue reactivity
			this.$forceUpdate();
		});
	},
};
