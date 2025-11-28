<template>
	<div class="pos-app-container">
		<!-- Main POS Container -->
		<div
			class="pos-main-container"
			:class="[rtlClasses, { 'fullscreen-mode': isFullscreen }]"
			:style="[responsiveStyles, rtlStyles]"
		>
			<ClosingDialog></ClosingDialog>
			<UpdateCustomer />
			<UpdateVehicle />
			<SalesOrders></SalesOrders>
			<Returns></Returns>
			<NewAddress></NewAddress>
			<MpesaPayments></MpesaPayments>
			<Variants></Variants>
			<OpeningDialog v-if="dialog" :dialog="dialog"></OpeningDialog>

			<div v-show="!dialog" class="pos-layout">
				<!-- Left Column: Drafts (25% width) -->
				<div class="pos-column drafts-column">
					<div v-show="!showOffers && !coupons && !payment" class="column-card drafts-card">
						<div class="column-header">
							<v-icon left color="primary">mdi-file-document</v-icon>
							<span>{{ __("Job orders") }}</span>
							<v-spacer></v-spacer>
							<v-btn
								icon
								size="small"
								@click="refreshDrafts"
								:loading="loadDraftsLoading"
								:aria-label="__('Refresh Drafts')"
							>
								<v-icon>mdi-refresh</v-icon>
							</v-btn>
						</div>
						<v-divider></v-divider>

						<div class="drafts-wrapper-container">
							<Drafts :use-as-modal="false" ref="draftsComponent"></Drafts>
						</div>
					</div>

					<!-- Additional components with proper card styling -->
					<div v-show="showOffers" class="column-card offers-coupons-card">
						<PosOffers></PosOffers>
					</div>
					<div v-show="coupons" class="column-card offers-coupons-card">
						<PosCoupons></PosCoupons>
					</div>
					<div v-show="payment" class="column-card payment-card">
						<Payments></Payments>
					</div>
				</div>

				<!-- Middle Column: Invoice (50% width) -->
				<div class="pos-column invoice-column">
					<div class="column-card invoice-card">
						<v-divider></v-divider>

						<div class="invoice-wrapper">
							<Invoice
								ref="invoiceComponent"
								:items_group="items_group"
								:item_group="item_group"
								@update:item_group="handleItemGroupUpdate"
							></Invoice>
						</div>
					</div>
				</div>

				<!-- Right Column: Items (25% width) -->
				<div class="pos-column items-column">
					<div class="column-card items-card">
						<div class="column-header">
							<span>{{ __("Search Items") }}</span>
							<v-spacer></v-spacer>
							<!-- <v-btn-group density="compact" variant="outlined">
								<v-btn
									size="small"
									:color="items_view === 'list' ? 'primary' : ''"
									@click="switchToListView"
									:aria-label="__('List View')"
								>
									<v-icon>mdi-view-list</v-icon>
								</v-btn>
								<v-btn
									size="small"
									:color="items_view === 'card' ? 'primary' : ''"
									@click="switchToCardView"
									:aria-label="__('Card View')"
								>
									<v-icon>mdi-view-grid</v-icon>
								</v-btn>
							</v-btn-group> -->
							<v-btn
								icon
								size="small"
								color="primary"
								variant="text"
								@click="toggleFullscreen"
								:title="isFullscreen ? __('Exit Fullscreen') : __('Fullscreen')"
								class="ml-2"
							>
								<v-icon>{{
									isFullscreen ? "mdi-arrow-collapse" : "mdi-arrow-expand"
								}}</v-icon>
							</v-btn>
						</div>
						<v-divider></v-divider>

						<!-- Scrollable Items List -->
						<div class="column-scroll-content items-scroll">
							<!-- KEY FIX: make view reactive for ItemsSelector -->
							<ItemsSelector
								:initial-view-mode="items_view"
								:view-mode="items_view"
								@update-view-mode="handleItemsViewUpdate"
								:is-modal="false"
								:hide-filters="true"
								ref="itemsSelectorComponent"
							/>
						</div>

						<!-- FOOTER FILTERS IN ITEMS COLUMN -->
						<div class="items-footer-filters">
							<!-- Filter and Action Controls -->
							<v-col cols="12">
								<v-row no-gutters align="center" justify="center" class="dynamic-spacing-sm">
									<!-- Item Group and Price List -->
									<!-- <v-col cols="12" class="mb-2">
										<v-row dense>
											<v-col cols="12" md="6" class="pr-md-2">
												<v-select
													:items="items_group"
													:label="__('Items Group')"
													density="compact"
													variant="solo"
													hide-details
													:model-value="item_group"
													@update:model-value="handleItemGroupUpdate"
												></v-select>
											</v-col>

											<v-col
												cols="12"
												md="6"
												class="pl-md-2"
												v-if="
													pos_profile &&
													pos_profile.posa_enable_price_list_dropdown !== false
												"
											>
												<v-text-field
													density="compact"
													variant="solo"
													color="primary"
													:label="__('Price List')"
													:model-value="priceListToShow"
													readonly
												></v-text-field>
											</v-col>
										</v-row>
									</v-col> -->

									<!-- Offers & Coupons -->
									<v-col cols="12" class="mt-2 mb-2">
										<v-row dense align="center">
											<v-col cols="12" sm="4" class="py-1">
												<v-btn class="offer-style-btn" @click="handleShowOffers">
													<v-icon left size="18">mdi-tag-multiple</v-icon>
													<div class="btn-text">
														<div class="btn-title">
															{{ offersCount }} {{ __("Offers") }}
														</div>
													</div>
												</v-btn>
											</v-col>

											<v-col sm="2"></v-col>

											<v-col cols="12" sm="4" class="py-1 text-right">
												<v-btn class="coupon-style-btn" @click="handleShowCoupons">
													<v-icon left size="18">mdi-ticket-percent</v-icon>
													<div class="btn-text">
														<div class="btn-title">
															{{ couponsCount }} {{ __("Coupons") }}
														</div>
													</div>
												</v-btn>
											</v-col>
										</v-row>
									</v-col>
								</v-row>
							</v-col>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- dialogs omitted -->
	</div>
</template>

<script>
// Component Imports
import ItemsSelector from "./ItemsSelector.vue";
import Invoice from "./Invoice.vue";
import OpeningDialog from "./OpeningDialog.vue";
import Payments from "./Payments.vue";
import PosOffers from "./PosOffers.vue";
import PosCoupons from "./PosCoupons.vue";
import Drafts from "./Drafts.vue";
import SalesOrders from "./SalesOrders.vue";
import ClosingDialog from "./ClosingDialog.vue";
import NewAddress from "./NewAddress.vue";
import Variants from "./Variants.vue";
import Returns from "./Returns.vue";
import MpesaPayments from "./Mpesa-Payments.vue";
import UpdateCustomer from "./UpdateCustomer.vue";
import UpdateVehicle from "./UpdateVehicle.vue";

import { getCurrentInstance } from "vue";
import { usePosShift } from "../../composables/usePosShift.js";
import { useOffers } from "../../composables/useOffers.js";
import { clearExpiredCustomerBalances } from "../../../offline/index.js";
import { useResponsive } from "../../composables/useResponsive.js";
import { useRtl } from "../../composables/useRtl.js";

export default {
	setup() {
		const instance = getCurrentInstance();
		const responsive = useResponsive();
		const rtl = useRtl();
		const shift = usePosShift(() => {
			if (instance && instance.proxy) {
				instance.proxy.dialog = true;
			}
		});
		const offers = useOffers();
		return { ...responsive, ...rtl, ...shift, ...offers };
	},
	data: function () {
		return {
			items_view: "list",
			item_group: "ALL",
			items_group: ["ALL"],
			dialog: false,
			loadDraftsLoading: false,
			pos_profile: null,
			pos_opening_shift: null,
			payment: false,
			showOffers: false,
			coupons: false,
			itemsLoaded: false,
			customersLoaded: false,
			isFullscreen: false,
			showItemGroupDialog: false,
			showPriceListDialog: false,
			offersCount: 0,
			couponsCount: 0,
			active_price_list: "",
		};
	},

	components: {
		ItemsSelector,
		Invoice,
		OpeningDialog,
		Payments,
		Drafts,
		ClosingDialog,
		Returns,
		PosOffers,
		PosCoupons,
		NewAddress,
		Variants,
		MpesaPayments,
		UpdateCustomer,
		UpdateVehicle,
		SalesOrders,
	},

	computed: {
		// reflect backend price list
		priceListToShow() {
			if (this.pos_profile && this.pos_profile.selling_price_list) {
				return this.pos_profile.selling_price_list;
			}
			return this.active_price_list || "";
		},
	},

	watch: {
		// Watch items_view and sync with ItemsSelector
		items_view: {
			handler(newVal, oldVal) {
				console.log("[POS] items_view watcher triggered:", { from: oldVal, to: newVal });

				if (newVal !== oldVal) {
					this.$nextTick(() => {
						if (this.$refs.itemsSelectorComponent) {
							console.log("[POS] Calling updateViewMode from watcher:", newVal);
							this.$refs.itemsSelectorComponent.updateViewMode(newVal);
						}
					});
				}
			},
			immediate: false,
		},
	},

	methods: {
		toggleFullscreen() {
			this.isFullscreen = !this.isFullscreen;
			this.$emit("toggle-fullscreen", this.isFullscreen);
			if (this.isFullscreen) {
				document.body.style.overflow = "hidden";
				document.body.style.paddingTop = "0";
			} else {
				document.body.style.overflow = "";
				document.body.style.paddingTop = "";
			}
		},

		// Footer buttons -> open panels like before
		handleShowOffers() {
			this.showOffers = true;
			this.coupons = false;
			this.payment = false;
			this.eventBus.emit("show_offers", "true");
		},
		handleShowCoupons() {
			this.coupons = true;
			this.showOffers = false;
			this.payment = false;
			this.eventBus.emit("show_coupons", "true");
		},

		selectItemGroup(group) {
			this.item_group = group;
			this.showItemGroupDialog = false;
			this.eventBus.emit("update:item_group", group);
		},

		show_offers() {
			this.showOffers = !this.showOffers;
			this.coupons = false;
			this.payment = false;
			this.eventBus.emit("show_offers", this.showOffers ? "true" : "false");
		},

		show_coupons() {
			this.coupons = !this.coupons;
			this.showOffers = false;
			this.payment = false;
			this.eventBus.emit("show_coupons", this.coupons ? "true" : "false");
		},

		create_opening_voucher() {
			this.dialog = true;
		},

		get_pos_setting() {
			frappe.db.get_doc("POS Settings", undefined).then((doc) => {
				this.eventBus.emit("set_pos_settings", doc);
			});
		},

		checkLoadingComplete() {
			if (this.itemsLoaded && this.customersLoaded) {
				console.info("Loading completed");
			}
		},

		// Dedicated method for switching to list view
		switchToListView() {
			console.log("[POS] Switching to list view");
			this.handleItemsViewUpdate("list");
		},

		// Dedicated method for switching to card view
		switchToCardView() {
			console.log("[POS] Switching to card view");
			this.handleItemsViewUpdate("card");
		},

		handleItemGroupUpdate(newGroup) {
			console.log("[POS] Item group updated:", newGroup);
			this.item_group = newGroup;
		},

		handleItemsViewUpdate(newView) {
			console.log("[POS] Items view update requested:", newView);

			// Prevent unnecessary updates
			if (this.items_view === newView) {
				console.log("[POS] Already in this view, skipping");
				return;
			}

			// Update local state
			this.items_view = newView;

			// Wait for DOM update, then force ItemsSelector to update
			this.$nextTick(() => {
				if (this.$refs.itemsSelectorComponent) {
					console.log("[POS] Updating ItemsSelector view to:", newView);
					this.$refs.itemsSelectorComponent.updateViewMode(newView);
				}

				// Broadcast to other components
				this.eventBus.emit("update:items_view", newView);
				this.eventBus.emit("items_view_changed", newView);

				console.log("[POS] Items view is now:", this.items_view);
			});
		},
		async refreshDrafts() {
			try {
				this.loadDraftsLoading = true;

				if (!this.pos_profile || !this.pos_profile.name) {
					if (this.pos_profile === null) return;
					this.eventBus.emit("show_message", {
						title: __("POS Profile not loaded. Please refresh the page."),
						color: "error",
					});
					this.loadDraftsLoading = false;
					return;
				}

				const r = await frappe.call({
					method: "frappe.client.get_list",
					args: {
						doctype: "Sales Invoice",
						filters: {
							docstatus: 0,
							company: this.pos_profile.company,
							pos_profile: this.pos_profile.name,
						},
						fields: [
							"name",
							"customer",
							"posting_date",
							"posting_time",
							"grand_total",
							"currency",
							// Request these so frontend can show employee
							"custom_service_employee",
						],
						limit_page_length: 500,
						order_by: "modified desc",
					},
				});

				if (r.message) {
					this.eventBus.emit("open_drafts", r.message);
				} else {
					this.eventBus.emit("open_drafts", []);
				}
			} catch (error) {
				console.error("Error fetching draft invoices:", error);
				this.eventBus.emit("show_message", {
					title: __("Error loading draft invoices"),
					color: "error",
				});
			} finally {
				this.loadDraftsLoading = false;
			}
		},


		get_items_groups() {
			if (!this.pos_profile) {
				console.log("No POS Profile");
				return;
			}

			this.items_group = ["ALL"];
			const groups = [];

			if (this.pos_profile.item_groups && this.pos_profile.item_groups.length > 0) {
				console.log("[POS] Loading item groups from POS Profile");

				this.pos_profile.item_groups.forEach((element) => {
					const groupName = element.item_group || element.name;

					if (groupName && groupName !== "All Item Groups" && groupName !== "ALL") {
						this.items_group.push(groupName);
						groups.push(groupName);
					}
				});
			}
		},

		async load_selected_draft(draft_name) {
			try {
				const r = await frappe.call({
					method: "frappe.client.get",
					args: {
						doctype: "Sales Invoice",
						name: draft_name,
					},
				});

				if (r.message) {
					this.eventBus.emit("load_invoice", r.message);

					// If the loaded invoice has a service employee, tell other components.
					if (r.message.custom_service_employee) {
						// If server included a helper name (custom_service_employee_name) prefer that
						this.eventBus.emit("employee_selected", {
							employee_id: r.message.custom_service_employee,
							employee_name: r.message.custom_service_employee_name || null,
						});
					}

					this.eventBus.emit("show_message", {
						title: __("Draft invoice {0} loaded successfully", [draft_name]),
						color: "success",
					});
				}
			} catch (error) {
				console.error("Error loading draft invoice:", error);
				this.eventBus.emit("show_message", {
					title: __("Error loading draft invoice: {0}", [error.message]),
					color: "error",
				});
			}
		},
	},

	mounted: function () {
		this.$nextTick(function () {
			this.check_opening_entry();
			this.get_pos_setting();

			this.eventBus.on("close_opening_dialog", () => {
				this.dialog = false;
			});

			this.eventBus.on("update:items_view", (newView) => {
				this.items_view = newView;
			});

			this.eventBus.on("register_pos_data", (data) => {
				this.pos_profile = data.pos_profile;
				this.pos_opening_shift = data.pos_opening_shift;
				this.get_offers(this.pos_profile.name, this.pos_profile);
				this.eventBus.emit("register_pos_profile", data);
				this.active_price_list = this.pos_profile.selling_price_list;
			});

			this.eventBus.on("register_pos_profile", async (data) => {
				this.pos_profile = data.pos_profile;
				this.get_items_groups();
				this.refreshDrafts();
				await this.initializeItems();
				this.items_view = this.pos_profile.posa_default_card_view ? "card" : "list";
				this.active_price_list = this.pos_profile.selling_price_list;
			});

			this.eventBus.on("show_payment", (data) => {
				this.payment = data === "true";
				this.showOffers = false;
				this.coupons = false;
			});

			this.eventBus.on("show_offers", (data) => {
				this.showOffers = data === "true";
				this.payment = false;
				this.coupons = false;
			});

			this.eventBus.on("show_coupons", (data) => {
				this.coupons = data === "true";
				this.showOffers = false;
				this.payment = false;
			});

			this.eventBus.on("items_loaded", () => {
				this.itemsLoaded = true;
				this.checkLoadingComplete();
			});

			this.eventBus.on("customers_loaded", () => {
				this.customersLoaded = true;
				this.checkLoadingComplete();
			});

			this.eventBus.on("draft_selected", (draft_name) => {
				console.log("[POS] Draft selected from drafts component:", draft_name);
				this.load_selected_draft(draft_name);
			});

			this.eventBus.on("update_offers_counters", (data) => {
				this.offersCount = data.offersCount || 0;
			});

			this.eventBus.on("update_coupons_counters", (data) => {
				this.couponsCount = data.couponsCount || 0;
			});
		});
	},

	beforeUnmount() {
		this.eventBus.off("close_opening_dialog");
		this.eventBus.off("register_pos_data");
		this.eventBus.off("register_pos_profile");
		this.eventBus.off("show_payment");
		this.eventBus.off("show_offers");
		this.eventBus.off("show_coupons");
		this.eventBus.off("items_loaded");
		this.eventBus.off("customers_loaded");
		this.eventBus.off("draft_selected");
		this.eventBus.off("update_offers_counters");
		this.eventBus.off("update_coupons_counters");

		if (this.isFullscreen) {
			document.body.style.overflow = "";
			document.body.style.paddingTop = "";
		}
	},

	created() {
		clearExpiredCustomerBalances();
	},
};
</script>

<style scoped>
/* Root App Container */
.pos-app-container {
	display: flex;
	flex-direction: column;
	width: 100%;
	height: 100vh;
	overflow: hidden;
	background: #fff;
	padding: 0;
	margin: 0;
}

/* Main POS Container */
.pos-main-container {
	position: relative;
	flex: 1;
	width: 100%;
	height: 100%;
	overflow: hidden;
	padding: 0 !important;
	margin: 0 !important;
	transition: all 0.3s ease;
}

/* Fullscreen Mode */
.pos-main-container.fullscreen-mode {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	z-index: 9999;
	background: white;
}

/* Flexbox layout */
.pos-layout {
	display: flex;
	width: 100%;
	height: 100%;
	gap: 0;
	padding: 0;
	margin: 0;
	overflow: hidden;
}

/* Columns */
.pos-column {
	display: flex;
	flex-direction: column;
	height: 100%;
	padding: 6px 3px;
	overflow: hidden;
	min-width: 0;
}

.drafts-column {
	flex: 0 0 25%;
	padding-left: 1px;
	padding-right: 2px;
	flex-shrink: 0;
}

.invoice-column {
	flex: 0 0 50%;
	padding-left: 3px;
	padding-right: 3px;
	flex-shrink: 0;
}

.items-column {
	flex: 0 0 25%;
	padding-left: 2px;
	padding-right: 1px;
	flex-shrink: 0;
}

/* Column Card */
.column-card {
	display: flex;
	flex-direction: column;
	height: 100%;
	border: 2px solid #e0e0e0;
	border-radius: 8px;
	overflow: hidden;
	background: white;
	transition: border-color 0.2s ease;
	position: relative;
}

/* Drafts Card */
.drafts-card {
	overflow: hidden;
	display: flex;
	flex-direction: column;
}

/* Drafts Wrapper Container */
.drafts-wrapper-container {
	flex: 1;
	overflow: hidden;
	display: flex;
	flex-direction: column;
	width: 100%;
	min-height: 0;
}

.drafts-wrapper-container :deep(.drafts-wrapper) {
	display: flex;
	flex-direction: column;
	height: 100%;
	width: 100%;
}

.drafts-wrapper-container :deep(.drafts-content) {
	flex: 1;
	overflow-y: auto;
	overflow-x: hidden;
	padding: 10px;
	background-color: #fafafa;
	min-height: 0;
}

.drafts-wrapper-container :deep(.drafts-footer) {
	flex-shrink: 0;
	padding: 12px;
	background: white;
	border-top: 2px solid #e0e0e0;
	z-index: 100;
}

/* ===== Offers & Coupons - balanced / centered styles ===== */

.offer-style-btn,
.coupon-style-btn {
	display: inline-flex !important;
	align-items: center !important;
	justify-content: center !important;
	gap: 12px;
	box-sizing: border-box;

	/* fixed/consistent sizing */
	min-width: 170px;
	max-width: 210px;
	height: 48px !important;
	padding: 8px 14px !important;

	border-radius: 10px !important;
	text-transform: none !important;
	font-weight: 800 !important;
	color: #fff !important;
	box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12) !important;
	transition:
		transform 0.12s ease,
		box-shadow 0.12s ease;
	overflow: visible !important;
}

/* Hover / active micro-interaction */
.offer-style-btn:hover,
.coupon-style-btn:hover {
	transform: translateY(-2px);
	box-shadow: 0 10px 24px rgba(0, 0, 0, 0.14) !important;
}

/* icon alignment (left) */
.offer-icon,
.coupon-icon {
	flex: 0 0 auto;
	margin-right: 6px;
	margin-left: 0;
}

/* text container: center-aligned, allow short wrap */
.btn-text {
	display: flex;
	flex-direction: column;
	align-items: flex-start; /* left align next to icon */
	justify-content: center;
	line-height: 1;
}

/* Title: number + word */
.btn-title {
	font-size: 15px;
	font-weight: 900;
	line-height: 1;
	display: inline-block;
	white-space: nowrap; /* keep number + word on same line if space; otherwise truncate gracefully */
	overflow: hidden;
	text-overflow: ellipsis;
}

/* make the descriptive word slightly lighter */
.btn-word {
	font-weight: 700;
	margin-left: 6px;
}
/* Add clean spacing between Offers and Coupons buttons */
.offer-btn-wrapper,
.coupon-btn-wrapper {
	display: flex;
	justify-content: center;
}

.offer-style-btn,
.coupon-style-btn {
	margin-right: 12px; /* spacing */
}

.coupon-style-btn {
	margin-left: 12px; /* spacing */
}

/* optional subtitle (if used) */
.btn-sub {
	font-size: 11px;
	opacity: 0.9;
	margin-top: 2px;
}

/* gradients */
.offer-style-btn {
	background: linear-gradient(90deg, #ff9a1c 0%, #ff7a00 60%, #ff6f00 100%) !important;
}

.coupon-style-btn {
	background: linear-gradient(90deg, #43b6ff 0%, #2196f3 60%, #1976d2 100%) !important;
}

/* Responsive: stack & full width on small screens */
@media (max-width: 600px) {
	.offer-style-btn,
	.coupon-style-btn {
		min-width: 100% !important;
		max-width: 100% !important;
		justify-content: flex-start !important;
		padding-left: 16px !important;
		height: 52px !important;
	}

	.btn-text {
		align-items: flex-start;
	}

	.btn-title {
		white-space: nowrap;
		font-size: 15px;
	}
}

/* Offers = Orange gradient */
.offer-style-btn {
	background: linear-gradient(90deg, #ff9800, #ff6f00) !important;
}

/* Coupons = Blue gradient */
.coupon-style-btn {
	background: linear-gradient(90deg, #2196f3, #1976d2) !important;
}

/* text block */
.btn-text {
	display: flex;
	flex-direction: column;
	line-height: 1.1;
	margin-left: 8px;
}

.btn-title {
	font-size: 15px;
	font-weight: 700;
}

.btn-sub {
	font-size: 12px;
	opacity: 0.9;
}

/* Invoice Card */
.invoice-card {
	overflow: hidden;
}

/* Items Card with Footer */
.items-card {
	position: relative;
}

/* Column Header */
.column-header {
	background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%);
	padding: 10px 14px;
	font-weight: 600;
	font-size: 0.95rem;
	display: flex;
	align-items: center;
	gap: 8px;
	min-height: 50px;
	flex-shrink: 0;
	border-bottom: 1px solid #e0e0e0;
}

.column-header .v-icon {
	font-size: 20px;
}

/* Scrollable Content */
.column-scroll-content {
	flex: 1;
	overflow-y: auto;
	overflow-x: hidden;
	padding: 10px;
	background-color: #fafafa;
	min-height: 0;
}
.pos-main-container > .v-row:nth-child(1),
.pos-main-container > .v-row:nth-child(2),
.pos-main-container > .v-row:nth-child(3),
.pos-main-container > .v-row:nth-child(4),
.pos-main-container > .v-row:nth-child(5),
.pos-main-container > .v-row:nth-child(6) {
	display: none !important;
}
.items-scroll {
	padding: 6px;
	margin-bottom: 120px; /* Space for footer filters */
}

/* Invoice Wrapper */
.invoice-wrapper {
	flex: 1;
	overflow: hidden;
	display: flex;
	flex-direction: column;
	width: 100%;
	min-height: 0;
}

.invoice-wrapper :deep(.invoice-container) {
	display: flex;
	flex-direction: column;
	height: 100%;
	width: 100%;
}

.invoice-wrapper :deep(.invoice-content) {
	flex: 1;
	overflow-y: auto;
	overflow-x: hidden;
	padding: 10px;
	background-color: #fafafa;
	min-height: 0;
}

/* Items Footer Filters */
.items-footer-filters {
	position: absolute;
	width: 100%;
	bottom: 0;
	left: 0;
	right: 0;
	background: white;
	border-top: 2px solid #e0e0e0;
	padding: 12px;
	z-index: 100;
}

.filter-row {
	margin-bottom: 0 !important;
}

.filter-btn {
	height: 36px !important;
	font-size: 0.85rem !important;
	text-transform: none !important;
	justify-content: flex-start !important;
}

.filter-text {
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
	max-width: 100%;
}

/* Scrollbars */
.drafts-wrapper-container :deep(.drafts-content::-webkit-scrollbar),
.invoice-wrapper :deep(.invoice-content::-webkit-scrollbar),
.column-scroll-content::-webkit-scrollbar {
	width: 6px;
}

.drafts-wrapper-container :deep(.drafts-content::-webkit-scrollbar-track),
.invoice-wrapper :deep(.invoice-content::-webkit-scrollbar-track),
.column-scroll-content::-webkit-scrollbar-track {
	background: #f1f1f1;
	border-radius: 3px;
}

.drafts-wrapper-container :deep(.drafts-content::-webkit-scrollbar-thumb),
.invoice-wrapper :deep(.invoice-content::-webkit-scrollbar-thumb),
.column-scroll-content::-webkit-scrollbar-thumb {
	background: #999;
	border-radius: 3px;
}

.drafts-wrapper-container :deep(.drafts-content::-webkit-scrollbar-thumb:hover),
invoice-wrapper :deep(.invoice-content::-webkit-scrollbar-thumb:hover),
.column-scroll-content::-webkit-scrollbar-thumb:hover {
	background: #666;
}

/* Responsive - Tablet */
@media (max-width: 1024px) {
	.pos-layout {
		flex-direction: column;
	}

	.pos-column {
		width: 100% !important;
		min-height: 0;
	}

	.column-card {
		height: 450px;
		margin-bottom: 10px;
	}

	.items-scroll {
		margin-bottom: 130px;
	}
}

/* Mobile */
@media (max-width: 768px) {
	.pos-app-container {
		height: 100vh;
	}

	.pos-layout {
		flex-direction: column;
		height: auto;
	}

	.pos-column {
		width: 100% !important;
	}

	.column-header {
		font-size: 1.5rem;
		padding: 8px 10px;
		min-height: 44px;
	}

	.column-card {
		height: 380px;
		margin-bottom: 10px;
	}

	.items-scroll {
		margin-bottom: 140px;
	}

	.filter-btn {
		height: 32px !important;
		font-size: 0.75rem !important;
	}
}

/* Print */
@media print {
	.pos-app-container {
		display: none;
	}
}
</style>
