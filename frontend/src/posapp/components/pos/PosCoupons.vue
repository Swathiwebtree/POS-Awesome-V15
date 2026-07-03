<template>
	<div class="coupon-container">
		<v-card
			class="coupon-main-card"
			:class="['selection', isDarkTheme ? '' : 'bg-grey-lighten-5']"
			:style="isDarkTheme ? 'background-color:#1E1E1E' : ''"
		>
			<v-card-title>
				<span class="text-h6 text-primary">{{ __("Coupons") }}</span>
			</v-card-title>

			<!-- Input and Button Row - Same Level -->
			<v-row class="coupon-input-row px-4 pb-2" no-gutters>
				<v-col cols="8" class="pr-2">
					<v-tooltip
						location="top"
						:text="discountConflictMessage"
						:disabled="!isCouponActionsDisabled"
					>
						<template #activator="{ props }">
							<span
								v-bind="props"
								:class="['discount-lock-activator', { 'discount-lock-activator--disabled': isCouponActionsDisabled }]"
							>
								<v-text-field
									density="compact"
									variant="outlined"
									color="primary"
									:label="frappe._('Coupon')"
									:bg-color="isDarkTheme ? '#1E1E1E' : 'white'"
									hide-details
									v-model="new_coupon"
									class="coupon-input"
									:disabled="isCouponActionsDisabled"
									@keydown.enter.prevent="handleCouponEnter"
								>
								</v-text-field>
							</span>
						</template>
					</v-tooltip>
				</v-col>
				<v-col cols="4">
					<v-tooltip
						location="top"
						:text="discountConflictMessage"
						:disabled="!isCouponActionsDisabled"
					>
						<template #activator="{ props }">
							<span
								v-bind="props"
								:class="['discount-lock-activator', { 'discount-lock-activator--disabled': isCouponActionsDisabled }]"
							>
								<v-btn
									class="add-coupon-btn"
									color="success"
									theme="dark"
									block
									:disabled="isCouponActionsDisabled"
									@click="add_coupon(new_coupon)"
								>
									{{ __("add") }}
								</v-btn>
							</span>
						</template>
					</v-tooltip>
				</v-col>
			</v-row>

			<div class="coupon-scroll my-0 py-0" @mouseover="style = 'cursor: pointer'">
				<v-data-table
					class="coupon-table"
					:headers="items_headers"
					:items="posa_coupons"
					:single-expand="singleExpand"
					v-model:expanded="expanded"
					item-key="coupon"
					:items-per-page="itemsPerPage"
					hide-default-footer
				>
					<template v-slot:item.applied="{ item }">
						<v-btn
							:color="(item.raw || item).applied ? 'red' : 'green'"
							variant="flat"
							size="small"
							:disabled="isCouponActionsDisabled && !(item.raw || item).applied"
							@click="(item.raw || item).applied ? removeCoupon(item.raw || item) : applyCoupon(item.raw || item)"
						>
							{{ (item.raw || item).applied ? __("Remove") : __("Apply") }}
						</v-btn>
					</template>
				</v-data-table>
			</div>
		</v-card>

		<v-card flat class="coupon-footer-card">
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
	export default {
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
		customer: "",
		posa_coupons: [],
		new_coupon: null,
		discountConflictState: {
			activeType: null,
			message: "",
		},
		itemsPerPage: 1000,
		singleExpand: true,
		items_headers: [
			{ title: __("Coupon"), value: "coupon_code", align: "start" },
			{ title: __("Type"), value: "type", align: "start" },
			{ title: __("Offer"), value: "pos_offer", align: "start" },
			{ title: __("Applied"), value: "applied", align: "start" },
		],
	}),

	computed: {
		couponsCount() {
			return this.posa_coupons.length;
		},
		appliedCouponsCount() {
			return this.posa_coupons.filter((el) => !!el.applied).length;
		},
		isDarkTheme() {
			return this.$theme?.current === "dark";
		},
		isCouponActionsDisabled() {
			return ["offer", "loyalty"].includes(this.sharedActiveDiscountType);
		},
		discountConflictMessage() {
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
			this.eventBus.emit("show_coupons", "false");
		},
		handleCouponEnter() {
			if (this.isCouponActionsDisabled) {
				this.eventBus.emit("show_message", {
					title: this.discountConflictMessage,
					color: "error",
				});
				return;
			}
			this.add_coupon(this.new_coupon);
		},
		add_coupon(new_coupon) {
			if (this.isCouponActionsDisabled) {
				this.eventBus.emit("show_message", {
					title: this.discountConflictMessage,
					color: "error",
				});
				return;
			}

			if (!new_coupon) {
				this.eventBus.emit("show_message", {
					title: __("Enter coupon code"),
					color: "error",
				});
				return;
			}

			if (!this.customer) {
				this.eventBus.emit("show_message", {
					title: __("Select a customer to use coupon"),
					color: "error",
				});
				return;
			}

			new_coupon = String(new_coupon).trim().toUpperCase();

			const exist = this.posa_coupons.find((el) => el.coupon_code == new_coupon);
			if (exist) {
				this.eventBus.emit("show_message", {
					title: __("This coupon already used !"),
					color: "error",
				});
				return;
			}

			const vm = this;
			frappe.call({
				method: "posawesome.posawesome.api.offers.get_pos_coupon",
				args: {
					coupon: new_coupon,
					customer: vm.customer,
					company: vm.pos_profile.company,
				},
				callback: function (r) {
					if (r.message) {
						const res = r.message;
						if (res.msg != "Apply" || !res.coupon) {
							vm.eventBus.emit("show_message", {
								title: res.msg,
								color: "error",
							});
						} else {
							vm.new_coupon = null;
							const coupon = res.coupon;
							vm.posa_coupons.push({
								coupon: coupon.name,
								coupon_code: coupon.coupon_code,
								type: coupon.coupon_type,
								applied: 1,
								pos_offer: coupon.pos_offer,
								customer: coupon.customer || vm.customer,
							});
							console.log("====================================");
							console.log("[COUPON] Coupon added to POS");
							console.log(vm.posa_coupons);
							console.log("====================================");
							vm.setExclusiveCoupon(coupon.name);
							vm.updateInvoice();

							setTimeout(() => {
								console.log("[COUPON] Emitting handle_offers");
								vm.eventBus.emit("handle_offers");
							}, 300);
						}
					}
				},
			});
		},
		setExclusiveCoupon(activeCouponId) {
			this.posa_coupons.forEach((coupon) => {
				coupon.applied = coupon.coupon === activeCouponId;
			});
		},
		applyCoupon(coupon) {
			if (this.isCouponActionsDisabled) {
				this.eventBus.emit("show_message", {
					title: this.discountConflictMessage,
					color: "error",
				});
				return;
			}

			this.setExclusiveCoupon(coupon.coupon);
			coupon.applied = true;
			this.updateInvoice();
			this.eventBus.emit("handle_offers");
		},
		setActiveGiftCoupons() {
			if (!this.customer) return;
			const vm = this;
			frappe.call({
				method: "posawesome.posawesome.api.offers.get_active_gift_coupons",
				args: {
					customer: vm.customer,
					company: vm.pos_profile.company,
				},
				callback: function (r) {
					if (r.message) {
						const coupons = r.message;
						coupons.forEach((coupon_code) => {
							vm.add_coupon(coupon_code);
						});
					}
				},
			});
		},

		updatePosCoupons(offers) {
			this.posa_coupons.forEach((coupon) => {
				const offer = offers.find((el) => {
					return (
						el.offer_applied &&
						(
							el.coupon === coupon.coupon ||
							el.coupon_code === coupon.coupon_code ||
							el.pos_offer === coupon.pos_offer ||
							el.name === coupon.pos_offer
						)
						);
				});

				coupon.applied = !!offer;
			});

			this.updateCounters();
		},

		removeCoupon(target) {
			if (Array.isArray(target)) {
				this.posa_coupons = this.posa_coupons.filter((coupon) => !target.includes(coupon.coupon));
				return;
			}
			this.posa_coupons = this.posa_coupons.map((coupon) => ({
				...coupon,
				applied: coupon.coupon === target.coupon ? 0 : coupon.applied,
			}));
			this.updateInvoice();
			this.eventBus.emit("handle_offers");
		},
		updateInvoice() {
			this.eventBus.emit("update_invoice_coupons", this.posa_coupons);
		},
		updateCounters() {
			this.eventBus.emit("update_coupons_counters", {
				couponsCount: this.couponsCount,
				appliedCouponsCount: this.appliedCouponsCount,
			});
		},
	},

	watch: {
		posa_coupons: {
			deep: true,
			handler() {
				this.updateInvoice();
				this.updateCounters();
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
				const to_remove = [];
				this.posa_coupons.forEach((el) => {
					if (el.type == "Promotional") {
						el.customer = customer;
					} else {
						to_remove.push(el.coupon);
					}
				});
				this.customer = customer;
				if (to_remove.length) {
					this.removeCoupon(to_remove);
				}
			}
			this.setActiveGiftCoupons();
			console.log("Coupon customer updated:", customer);
		});
		this.eventBus.on("discount_conflict_state", this.updateDiscountConflictState);
		this.eventBus.on("update_pos_coupons", (data) => {
			this.updatePosCoupons(data);
		});
		this.eventBus.on("set_pos_coupons", (data) => {
			this.posa_coupons = data;
		});
	},
	beforeUnmount() {
		this.eventBus.off("discount_conflict_state", this.updateDiscountConflictState);
	},
};
</script>

<style scoped>
.coupon-container {
	display: flex;
	flex-direction: column;
	height: 100%;
}

.coupon-main-card {
	flex: 1;
	display: flex;
	flex-direction: column;
	overflow: hidden;
}

.coupon-scroll {
	flex: 1;
	min-height: 0;
	display: flex;
	flex-direction: column;
	justify-content: flex-start;
	padding-top: 0;
}

.selection {
	display: flex;
	flex-direction: column;
	height: 100%;
}

.selection > .coupon-scroll {
	flex: 1;
}

.coupon-scroll :deep(.v-data-table) {
	margin-top: 0 !important;
	flex: 1;
	min-height: 0;
}

.coupon-scroll :deep(.v-table__wrapper) {
	flex: 1;
	min-height: 0;
	overflow-y: auto;
	overflow-x: hidden;
}

.coupon-scroll :deep(.v-data-table__empty-wrapper) {
	margin-top: 0 !important;
	align-items: flex-start !important;
	justify-content: flex-start !important;
	padding-top: 0 !important;
	height: auto !important;
	vertical-align: top !important;
}

.coupon-table {
	margin-top: 0 !important;
	margin-bottom: auto !important;
	align-self: stretch;
}

.coupon-scroll :deep(.v-data-table),
.coupon-scroll :deep(.v-table) {
	margin-top: 0 !important;
	align-self: flex-start !important;
}

.coupon-input {
	height: 40px;
}

.coupon-input-row {
	flex: 0 0 auto;
	height: auto;
	min-height: 0;
	align-items: center;
	margin-bottom: 0;
}

.coupon-input-row :deep(.v-input) {
	margin-bottom: 0 !important;
}

.coupon-input-row :deep(.v-field) {
	margin-bottom: 0 !important;
}

.add-coupon-btn {
	height: 40px;
	font-weight: 600 !important;
	transition: all 0.3s ease !important;
}

.add-coupon-btn:hover {
	transform: translateY(-2px);
	box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
}

/* Footer Card */
.coupon-footer-card {
	background: white;
	border-top: 2px solid #e0e0e0;
	box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
	padding: 12px;
	height: 80px;
	flex-shrink: 0;
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

.discount-lock-activator {
	display: block;
	width: 100%;
}

.discount-lock-activator--disabled {
	cursor: not-allowed;
}

/* Responsive */
@media (max-width: 768px) {
	.coupon-footer-card {
		height: 70px;
		padding: 8px;
	}

	.back-btn {
		height: 48px !important;
		font-size: 1rem !important;
	}
}
</style>
