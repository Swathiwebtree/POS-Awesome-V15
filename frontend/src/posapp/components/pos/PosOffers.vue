<template>
	<div class="offer-container">
		<v-card
			class="offer-main-card"
			:class="['selection', isDarkTheme ? '' : 'bg-grey-lighten-5']"
			:style="isDarkTheme ? 'background-color:#1E1E1E' : ''"
		>
			<v-card-title>
				<span class="text-h6 text-primary">{{ __("Offers") }}</span>
			</v-card-title>
			<div class="my-0 py-0 overflow-y-auto" @mouseover="style = 'cursor: pointer'">
				<v-data-table
					:headers="items_headers"
					:items="displayOffers"
					:single-expand="singleExpand"
					v-model:expanded="expanded"
					show-expand
					item-value="row_id"
					:item-class="getOfferRowClass"
					class="elevation-1"
					:items-per-page="itemsPerPage"
					hide-default-footer
				>
					<template v-slot:item.offer_applied="{ item }">
						<v-tooltip
							v-if="!(item.raw || item).offer_applied"
							location="top"
							:text="offerConflictMessage"
							:disabled="!isOfferActionsDisabled"
						>
							<template #activator="{ props }">
								<span
									v-bind="props"
									:class="['discount-lock-activator', { 'discount-lock-activator--disabled': isOfferActionsDisabled }]"
								>
									<v-btn
										color="green"
										:disabled="
											isOfferActionsDisabled ||
											((item.raw || item).offer == 'Give Product' &&
												!(item.raw || item).give_item &&
												(!((item.raw || item).replace_cheapest_item) || !((item.raw || item).replace_item))) ||
											((item.raw || item).offer == 'Grand Total' &&
												discount_percentage_offer_name &&
												discount_percentage_offer_name != (item.raw || item).name)
										"
										@click.stop.prevent="applyOffer(item.raw || item)"
									>
										{{ __("Apply") }}
									</v-btn>
								</span>
							</template>
						</v-tooltip>
						<div v-else class="offer-applied-cell">
							<div class="d-flex flex-wrap align-center ga-2">
								<v-chip color="green" variant="tonal" size="small" label>
									{{ __("APPLIED") }}
								</v-chip>
								<span class="offer-applied-amount">
									{{ __("Applied") }}
									{{ currencySymbol(getOfferCurrencyCode()) }}{{ getOfferAppliedAmount(item.raw || item) }}
								</span>
							</div>
							<v-btn
								color="red"
								variant="tonal"
								size="small"
								prepend-icon="mdi-close"
								class="mt-1 offer-remove-btn"
								@click="removeOffer(item.raw || item)"
							>
								{{ __("REMOVE") }}
							</v-btn>
						</div>
					</template>
					<template v-slot:expanded-row="{ item }">
						<td :colspan="items_headers.length">
							<v-row class="mt-2">
								<v-col v-if="item.description">
									<div class="text-primary" v-html="handleNewLine(item.description)"></div>
								</v-col>
								<v-col v-if="item.offer == 'Give Product'">
									<v-autocomplete
										v-model="item.give_item"
										:items="get_give_items(item)"
										item-title="item_name"
										item-value="item_code"
										variant="outlined"
										density="compact"
										color="primary"
										:label="frappe._('Give Item')"
										:disabled="
											item.apply_type != 'Item Group' ||
											item.replace_item ||
											item.replace_cheapest_item
										"
									></v-autocomplete>
								</v-col>
							</v-row>
						</td>
					</template>
				</v-data-table>
			</div>
		</v-card>

		<v-card flat class="offer-footer-card">
			<v-row align="center" no-gutters>
				<v-col cols="12">
					<v-btn
						block
						class="back-btn"
						size="large"
						color="warning"
						theme="dark"
						@click="back_to_invoice"
					>
						<v-icon left>mdi-arrow-left</v-icon>
						{{ __("Back") }}
					</v-btn>
				</v-col>
			</v-row>
		</v-card>
	</div>
</template>

<script>
/* global __, frappe */
import format from "../../format";
export default {
	mixins: [format],
	props: {
		activeDiscountType: {
			type: String,
			default: null,
		},
		activeDiscountMessage: {
			type: String,
			default: "",
		},
	},
	data: () => ({
		loading: false,
		pos_profile: "",
		pos_offers: [],
		allItems: [],
		groupItemCache: {},
		discount_percentage_offer_name: null,
		suppressPosOffersWatcher: false,
		discountConflictState: {
			activeType: null,
			message: "",
		},
		itemsPerPage: 1000,
		expanded: [],
		singleExpand: true,
		items_headers: [
			{ title: __("Name"), value: "name", align: "start" },
			{ title: __("Apply On"), value: "apply_on", align: "start" },
			{ title: __("Offer"), value: "offer", align: "start" },
			{ title: __("Applied"), value: "offer_applied", align: "start" },
		],
	}),

	computed: {
		offersCount() {
			return this.pos_offers.length;
		},
		appliedOffersCount() {
			return this.displayOffers.filter((el) => !!el.offer_applied).length;
		},
		displayOffers() {
			return this.pos_offers.filter((offer) => !offer.coupon_based);
		},
		isDarkTheme() {
			return this.$theme?.current === "dark";
		},
		isOfferActionsDisabled() {
			return !!this.sharedActiveDiscountType;
		},
		offerConflictMessage() {
			return this.activeDiscountMessage || this.discountConflictState.message || "";
		},
		sharedActiveDiscountType() {
			return this.activeDiscountType || this.discountConflictState.activeType || null;
		},
	},

	methods: {
		updateDiscountConflictState(payload = {}) {
			this.discountConflictState = {
				activeType: payload.activeType || null,
				message: payload.message || "",
			};
		},
		back_to_invoice() {
			this.eventBus.emit("show_offers", "false");
		},
		async fetchGroupItems(group) {
			try {
				const { message } = await frappe.call({
					method: "posawesome.posawesome.api.items.get_items",
					args: {
						pos_profile: JSON.stringify(this.pos_profile),
						item_group: group,
						// fetch complete inventory; backend paginates internally
					},
				});

				const fullItems = message || [];

				// cache minimal info for dropdown use
				this.groupItemCache[group] = fullItems.map((it) => ({
					item_code: it.item_code,
					item_name: it.item_name || it.item_code,
					rate: it.price_list_rate,
				}));

				// merge fetched items into allItems so offer application has details
				const existing = new Set(this.allItems.map((it) => it.item_code));
				const newItems = fullItems.filter((it) => !existing.has(it.item_code));
				if (newItems.length) {
					this.allItems.push(...newItems);
					this.eventBus.emit("set_all_items", this.allItems);
				}

				this.forceUpdateItem();
			} catch (error) {
				console.error("Failed to fetch group items", error);
			}
		},
		forceUpdateItem() {
			let list_offers = [];
			list_offers = [...this.pos_offers];
			this.pos_offers = list_offers;
		},
		applyOffer(offer) {
			console.log("[OFFER APPLY CLICK]", offer.name, offer);
			if (this.isOfferActionsDisabled) {
				this.eventBus.emit("show_message", {
					title: this.offerConflictMessage,
					color: "error",
				});
				return;
			}
			if (!offer.coupon_based) {
				offer.offer_applied = true;
			} else {
				return;
			}
			this.suppressPosOffersWatcher = true;
			this.$nextTick(() => {
				this.suppressPosOffersWatcher = false;
			});
			this.eventBus.emit("update_invoice_offers", [offer]);
		},
		getOfferRowClass(item) {
			const offer = item.raw || item;
			return offer.offer_applied ? "offer-row-applied" : "";
		},
		getOfferCurrencyCode() {
			return (
				this.$parent?.$refs?.invoiceComponent?.pos_profile?.currency ||
				this.$parent?.pos_profile?.currency ||
				"INR"
			);
		},
		getOfferCurrencyPrecision() {
			return Number(this.$parent?.$refs?.invoiceComponent?.currency_precision || this.currency_precision || 2);
		},
		getOfferAppliedAmount(item) {
			const offer = item.raw || item;
			const directAmount = Number(
				offer.applied_discount_amount ||
					offer.applied_amount ||
					offer.redeemed_offer_amount ||
					offer.discount_amount ||
					0,
			);
			const invoiceAmount = Number(
				this.$parent?.$refs?.invoiceComponent?.invoice_doc?.redeemed_offer_amount || 0,
			);
			const amount = directAmount > 0 ? directAmount : offer.offer_applied ? invoiceAmount : 0;
			return this.formatFloat(amount, this.getOfferCurrencyPrecision());
		},
		removeOffer(item) {
			const offer = item.raw || item;
			if (offer.coupon_based) return;

			offer.offer_applied = false;
			offer.applied_discount_amount = 0;
			offer.applied_amount = 0;
			offer.redeemed_offer_amount = 0;

			this.suppressPosOffersWatcher = true;

			this.pos_offers = this.pos_offers.map((row) => {
				if (row.row_id === offer.row_id || row.name === offer.name) {
					return {
						...row,
						offer_applied: false,
						coupon: null,
						coupon_code: null,
						applied_discount_amount: 0,
						applied_amount: 0,
						redeemed_offer_amount: 0,
					};
				}
				return row;
			});

			this.$nextTick(() => {
				this.suppressPosOffersWatcher = false;
			});

			const remainingOffers = this.pos_offers.filter(
				(row) => row.offer_applied && !row.coupon_based,
			);

			this.eventBus.emit("update_invoice_offers", remainingOffers);
			this.updateCounters();
		},
		makeid(length) {
			let result = "";
			const characters = "abcdefghijklmnopqrstuvwxyz0123456789";
			const charactersLength = characters.length;
			for (var i = 0; i < length; i++) {
				result += characters.charAt(Math.floor(Math.random() * charactersLength));
			}
			return result;
		},
		updatePosOffers(offers) {
			offers = Array.isArray(offers) ? offers : [];
			offers.forEach((offer) => {
				const pos_offer = this.pos_offers.find((pos_offer) => offer.name === pos_offer.name);
				if (pos_offer) {
					pos_offer.items = offer.items;
					const incomingApplied =
						!!offer.offer_applied || (!!offer.coupon_based && !!offer.coupon);

					if (Object.prototype.hasOwnProperty.call(offer, "offer_applied")) {
						pos_offer.offer_applied = incomingApplied;
					} else {
						pos_offer.offer_applied = !!pos_offer.offer_applied || incomingApplied;
					}
					if (
						pos_offer.offer === "Grand Total" &&
						!pos_offer.coupon_based &&
						!this.discount_percentage_offer_name
					) {
						pos_offer.offer_applied = !!pos_offer.auto;
					}
					if (
						offer.apply_on == "Item Group" &&
						offer.apply_type == "Item Group" &&
						offer.replace_cheapest_item
					) {
						pos_offer.give_item = offer.give_item;
						pos_offer.apply_item_code = offer.apply_item_code;
					}
				} else {
					const newOffer = { ...offer };
					if (!offer.row_id) {
						newOffer.row_id = this.makeid(20);
					}
					if (offer.apply_type == "Item Code") {
						newOffer.give_item = offer.apply_item_code || "Nothing";
					}
					if (offer.offer_applied) {
						newOffer.offer_applied = !!offer.offer_applied;
					} else {
						if (
							offer.apply_type == "Item Group" &&
							offer.offer == "Give Product" &&
							!offer.replace_cheapest_item &&
							!offer.replace_item
						) {
							newOffer.offer_applied = false;
						} else if (offer.offer === "Grand Total" && this.discount_percentage_offer_name) {
							newOffer.offer_applied = false;
						} else {
							newOffer.offer_applied = !!offer.auto;
						}
					}
					if (newOffer.offer == "Give Product" && !newOffer.give_item) {
						const giveItems = this.get_give_items(newOffer);
						if (giveItems.length) {
							newOffer.give_item = giveItems[0].item_code;
						}
					}
					this.pos_offers.push(newOffer);
					this.eventBus.emit("show_message", {
						title: __("New Offer Available"),
						color: "warning",
					});
				}
			});
		},
		removeOffers(offers_id_list) {
			this.pos_offers = this.pos_offers.filter((offer) => !offers_id_list.includes(offer.row_id));
		},
		handelOffers() {
			const applyedOffers = this.pos_offers.filter((offer) => offer.offer_applied);
			this.eventBus.emit("update_invoice_offers", applyedOffers);
		},
		handleNewLine(str) {
			if (str) {
				return str.replace(/(?:\r\n|\r|\n)/g, "<br />");
			} else {
				return "";
			}
		},
		get_give_items(offer) {
			if (offer.apply_type === "Item Code") {
				return [
					{
						item_code: offer.apply_item_code,
						item_name: offer.apply_item_code,
					},
				];
			} else if (offer.apply_type === "Item Group") {
				const group = offer.apply_item_group;
				if (!this.groupItemCache[group]) {
					this.fetchGroupItems(group);
					return [];
				}
				let filtered_items = this.groupItemCache[group];
				if (offer.less_then > 0) {
					filtered_items = filtered_items.filter((item) => item.rate < offer.less_then);
				}
				const unique = [];
				const seen = new Set();
				filtered_items.forEach((item) => {
					if (!seen.has(item.item_code)) {
						seen.add(item.item_code);
						unique.push({
							item_code: item.item_code,
							item_name: item.item_name || item.item_code,
						});
					}
				});
				return unique;
			}
			return [];
		},
		updateCounters() {
			this.eventBus.emit("update_offers_counters", {
				offersCount: this.offersCount,
				appliedOffersCount: this.appliedOffersCount,
			});
		},
		updatePosCoupuns() {
			const applyedOffers = this.pos_offers.filter(
				(offer) => offer.offer_applied && offer.coupon_based,
			);
			this.eventBus.emit("update_pos_coupons", applyedOffers);
		},
		setOffers(data) {
			this.pos_offers = Array.isArray(data) ? data.map((offer) => ({ ...offer })) : [];
		},
	},

	watch: {
		pos_offers: {
			deep: true,
			handler() {
				if (this.suppressPosOffersWatcher) {
					return;
				}
				this.handelOffers();
				this.updateCounters();
				this.updatePosCoupuns();
			},
		},
	},

	created: function () {
		this.$nextTick(function () {
			this.eventBus.on("register_pos_profile", (data) => {
				this.pos_profile = data.pos_profile;
			});
		});
		this.eventBus.on("update_customer", (customer) => {
			if (this.customer != customer) {
				this.offers = [];
			}
		});
		this.eventBus.on("update_pos_offers", (data) => {
			this.updatePosOffers(data);
		});
		this.eventBus.on("set_offers", this.setOffers);
		this.eventBus.on("update_discount_percentage_offer_name", (data) => {
			this.discount_percentage_offer_name = data.value;
		});
		this.eventBus.on("discount_conflict_state", this.updateDiscountConflictState);
		this.eventBus.on("set_all_items", (data) => {
			this.allItems = data;
		});
	},
	beforeUnmount() {
		this.eventBus.off("discount_conflict_state", this.updateDiscountConflictState);
		this.eventBus.off("set_offers", this.setOffers);
	},
};
</script>
<style scoped>
/* ===== FIX BOTTOM GAP ===== */
.offer-container {
	display: flex;
	flex-direction: column;
	height: 100%;
}

.offer-main-card {
	flex: 1;
	overflow: hidden;
}

.offer-footer-card {
	margin-top: auto;
}

/* Footer Card */
.offer-footer-card {
	background: white;
	border-top: 2px solid #e0e0e0;
	box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
	padding: 12px;
	height: 80px;
}

.back-btn {
	height: 56px !important;
	font-size: 1.1rem !important;
	font-weight: 700 !important;
	letter-spacing: 0.5px;
	transition: all 0.2s ease;
}

.back-btn:hover {
	transform: translateY(-2px);
	box-shadow: 0 6px 16px rgba(255, 152, 0, 0.4) !important;
}

.back-btn .v-icon {
	font-size: 24px;
	margin-right: 8px;
}

/* Responsive */
@media (max-width: 768px) {
	.offer-footer-card {
		height: 70px;
		padding: 8px;
	}

	.back-btn {
		height: 48px !important;
		font-size: 1rem !important;
	}
}
/* ===== FINAL OFFERS LAYOUT FIX ===== */

.offer-container {
	height: 100%;
	display: flex;
	flex-direction: column;
}

/* main card fills space */
.offer-main-card {
	flex: 1;
	display: flex;
	flex-direction: column;
	overflow: hidden;
}

/* table scrolls */
.offer-scroll {
	flex: 1;
	min-height: 0;
}

/* footer sticks to bottom */
.offer-footer-card {
	flex-shrink: 0;
	background: white;
	border-top: 2px solid #e0e0e0;
	box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
	padding: 12px;
	height: 80px;
}

.discount-lock-activator {
	display: block;
	width: 100%;
}

.discount-lock-activator--disabled {
	cursor: not-allowed;
}

/* FIX bottom white gap in Offers */
.selection {
	display: flex;
	flex-direction: column;
	height: 100%;
}

.selection > .overflow-y-auto {
	flex: 1;
}

:deep(.offer-row-applied > td) {
	background-color: rgba(76, 175, 80, 0.08);
}

:deep(.offer-row-applied:hover > td) {
	background-color: rgba(76, 175, 80, 0.12);
}

.offer-applied-cell {
	display: flex;
	flex-direction: column;
	align-items: flex-start;
}

.offer-applied-amount {
	font-size: 0.875rem;
	font-weight: 600;
	color: rgba(0, 0, 0, 0.72);
}

:deep(.theme--dark) .offer-applied-amount {
	color: rgba(255, 255, 255, 0.8);
}
.offer-applied-cell {
	display: flex;
	flex-direction: column;
	gap: 4px;
	align-items: flex-start;
	min-width: 110px;
}

.offer-applied-amount {
	font-size: 12px;
	font-weight: 700;
	color: #2e7d32;
	white-space: nowrap;
}

.offer-remove-btn {
	height: 24px !important;
	min-width: 74px !important;
	font-size: 11px !important;
	font-weight: 700 !important;
}
</style>
