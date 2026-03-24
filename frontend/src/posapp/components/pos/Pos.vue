<template>
	<div class="pos-app-container" :class="{ 'fullscreen-mode': isFullscreen }">
		<div class="pos-scale-wrapper" :class="{ 'fullscreen-mode': isFullscreen }">
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
						<div v-show="!showOffers && !showCoupons" class="column-card drafts-card">
							<div class="column-header">
								<v-icon left color="primary">mdi-file-document</v-icon>
								<span>{{ __("Job orders") }}</span>
								<v-spacer></v-spacer>
								<v-btn
									icon
									size="small"
									:color="autoRefreshDrafts ? 'primary' : 'grey'"
									:aria-label="
										autoRefreshDrafts ? __('Auto Refresh On') : __('Auto Refresh Off')
									"
									:title="
										autoRefreshDrafts ? __('Auto Refresh On') : __('Auto Refresh Off')
									"
									@click="toggleDraftsAutoRefresh"
								>
									<v-icon>{{
										autoRefreshDrafts ? "mdi-refresh-auto" : "mdi-refresh-off"
									}}</v-icon>
								</v-btn>
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
						<div v-show="showCoupons" class="column-card offers-coupons-card">
							<PosCoupons></PosCoupons>
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
									:item_group="item_group"
									:external-search="first_search"
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
									<v-row
										no-gutters
										align="center"
										justify="center"
										class="dynamic-spacing-sm"
									>
										<!-- SEARCH BAR - ADD THIS FIRST -->
										<v-col cols="12" class="mb-2">
											<v-text-field
												density="compact"
												clearable
												autofocus
												variant="solo"
												color="#4169E1"
												placeholder="Search Items"
												hint="Search by item code, serial number, batch no or barcode"
												hide-details
												v-model="debounce_search"
												@keydown.esc="esc_event"
												@keydown.enter="search_onchange"
												@click:clear="handleSearchClear"
												prepend-inner-icon="mdi-magnify"
												ref="search_input"
											>
												<template
													v-slot:append-inner
													v-if="pos_profile?.posa_enable_camera_scanning"
												>
													<v-btn
														icon="mdi-camera"
														size="small"
														color="primary"
														variant="text"
														@click="startCameraScanning"
														:title="__('Scan with Camera')"
													>
													</v-btn>
												</template>
											</v-text-field>
										</v-col>
										<!-- Item Group and Price List -->
										<v-col cols="12" class="mb-2">
											<v-row dense>
												<v-col cols="12" class="px-0">
													<v-select
														:items="items_group"
														:label="__('Items Group')"
														density="compact"
														variant="solo"
														hide-details
														class="items-group-full"
														:model-value="item_group"
														@update:model-value="handleItemGroupUpdate"
													/>
												</v-col>
											</v-row>
										</v-col>

										<!-- <v-col
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
									</v-col>  -->

										<!-- Offers & Coupons -->
										<v-col cols="12" class="mt-2 mb-2">
											<v-row dense align="center">
												<v-col cols="6" class="py-1">
													<v-btn class="offer-style-btn" @click="handleShowOffers">
														<v-icon left size="18">mdi-tag-multiple</v-icon>
														<div class="btn-text">
															<div class="btn-title">
																{{ offersCount }} {{ __("Offers") }}
															</div>
														</div>
													</v-btn>
												</v-col>

												<v-col cols="6" class="py-1">
													<v-btn
														class="coupon-style-btn"
														@click="handleShowCoupons"
													>
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

			<Payments></Payments>
			<!-- dialogs omitted -->
		</div>
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
			autoRefreshDrafts: true,
			draftsRefreshIntervalId: null,
			draftsRefreshIntervalMs: 60000,
			pos_profile: null,
			pos_opening_shift: null,
			payment: false,
			showOffers: false,
			showCoupons: false,
			itemsLoaded: false,
			customersLoaded: false,
			isFullscreen: false,
			showItemGroupDialog: false,
			showPriceListDialog: false,
			offersCount: 0,
			couponsCount: 0,
			active_price_list: "",
			first_search: "",
			search: "",
			search_backup: "",
			search_from_scanner: false,
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

		debounce_search: {
			get() {
				return this.first_search;
			},
			set(newValue) {
				this.first_search = (newValue || "").trim();
			},
		},
	},

	watch: {
		offers: {
			deep: true,
			handler(val) {
				this.offersCount = Array.isArray(val) ? val.length : 0;

				this.eventBus.emit("set_offers", val || []);
				this.eventBus.emit("update_offers_counters", {
					offersCount: this.offersCount,
				});

				console.log("[POS] Offers synced:", val);
			},
		},

		coupons: {
			deep: true,
			handler(val) {
				this.couponsCount = Array.isArray(val) ? val.length : 0;

				this.eventBus.emit("set_coupons", val || []);
				this.eventBus.emit("update_coupons_counters", {
					couponsCount: this.couponsCount,
				});

				console.log("[POS] Coupons synced:", val);
			},
		},
	},

	methods: {
		async handleSearchClear() {
			console.log("[POS] Search clear clicked");
			this.first_search = "";
			this.search = "";

			if (this.$refs.itemsSelectorComponent) {
				await this.$refs.itemsSelectorComponent.clearSearch();
			} else {
				this.eventBus.emit("update:item_group", this.item_group || "ALL");
			}
		},

		onBarcodeScanned(scannedCode) {
			this.search_from_scanner = true;
			this.first_search = scannedCode;
			this.search = scannedCode;

			this.$nextTick(() => {
				this.search_onchange();
			});
		},

		search_onchange() {
			this.first_search = (this.first_search || "").trim();
		},

		async clearSearch() {
			this.search_backup = this.first_search;
			this.first_search = "";
			this.search = "";

			// Also clear in ItemsSelector
			if (this.$refs.itemsSelectorComponent) {
				await this.$refs.itemsSelectorComponent.clearSearch();
			} else {
				this.eventBus.emit("update:item_group", this.item_group || "ALL");
			}
		},

		esc_event() {
			this.search = null;
			this.first_search = null;
			this.search_backup = null;

			this.$nextTick(() => {
				if (this.$refs.search_input) {
					this.$refs.search_input.focus();
				}
			});
		},

		startCameraScanning() {
			if (this.$refs.itemsSelectorComponent?.startCameraScanning) {
				this.$refs.itemsSelectorComponent.startCameraScanning();
			}
		},
		toggleFullscreen() {
			this.isFullscreen = !this.isFullscreen;
			this.$emit("toggle-fullscreen", this.isFullscreen);
			if (this.isFullscreen) {
				document.body.style.overflow = "hidden";
				document.body.style.paddingTop = "0";
				document.documentElement.style.overflow = "hidden";
			} else {
				document.body.style.overflow = "";
				document.body.style.paddingTop = "";
				document.documentElement.style.overflow = "";
			}
		},

		// Footer buttons -> open panels like before
		handleShowOffers() {
			this.showOffers = true;
			this.showCoupons = false;

			this.eventBus.emit("show_offers", "true");
			this.eventBus.emit("set_offers", this.offers || []);
			this.eventBus.emit("update_pos_offers", this.offers || []);
		},

		handleShowCoupons() {
			this.showCoupons = true;
			this.showOffers = false;

			this.eventBus.emit("show_coupons", "true");
			this.eventBus.emit("set_coupons", this.coupons || []);
			this.eventBus.emit("set_pos_coupons", this.coupons || []);
		},

		selectItemGroup(group) {
			this.item_group = group;
			this.showItemGroupDialog = false;
			this.eventBus.emit("update:item_group", group);
		},

		show_offers() {
			this.showOffers = !this.showOffers;
			this.showCoupons = false;
			this.eventBus.emit("show_offers", this.showOffers ? "true" : "false");
		},

		show_coupons() {
			this.showCoupons = !this.showCoupons;
			this.showOffers = false;
			this.eventBus.emit("show_coupons", this.showCoupons ? "true" : "false");
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
			if (this.item_group === newGroup) return;

			this.item_group = newGroup;
			this.first_search = "";
			this.search = "";
		},
		handleItemsViewUpdate(newView) {
			if (this.items_view === newView) return;
			this.items_view = newView;
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
							"customer_name",
							"custom_display_name",
							"title",
							"display_name",
							"posting_date",
							"posting_time",
							"grand_total",
							"currency",
							"custom_service_employee",
							"custom_has_oil_item",
							"custom_odometer_reading",
							"custom_vehicle_no",
							"contact_mobile",
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
		shouldAutoRefreshDrafts() {
			if (typeof document !== "undefined" && document.hidden) return false;
			if (!this.autoRefreshDrafts) return false;
			if (this.showOffers || this.showCoupons) return false;
			if (this.loadDraftsLoading) return false;
			return true;
		},
		startDraftsAutoRefresh() {
			if (this.draftsRefreshIntervalId) return;
			this.draftsRefreshIntervalId = setInterval(() => {
				if (this.shouldAutoRefreshDrafts()) {
					this.refreshDrafts();
				}
			}, this.draftsRefreshIntervalMs);
		},
		stopDraftsAutoRefresh() {
			if (!this.draftsRefreshIntervalId) return;
			clearInterval(this.draftsRefreshIntervalId);
			this.draftsRefreshIntervalId = null;
		},
		toggleDraftsAutoRefresh() {
			this.autoRefreshDrafts = !this.autoRefreshDrafts;
			if (this.autoRefreshDrafts) {
				this.startDraftsAutoRefresh();
				if (this.shouldAutoRefreshDrafts()) {
					this.refreshDrafts();
				}
			} else {
				this.stopDraftsAutoRefresh();
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
						let employeeName = r.message.custom_service_employee_name || null;

						// Older/mobile-created drafts may only store the employee code on the invoice.
						if (!employeeName) {
							try {
								const employeeResp = await frappe.call({
									method: "frappe.client.get_value",
									args: {
										doctype: "Employee",
										fieldname: ["employee_name"],
										filters: {
											name: r.message.custom_service_employee,
										},
									},
								});
								employeeName = employeeResp?.message?.employee_name || null;
							} catch (employeeError) {
								console.warn(
									"[POS] Failed to resolve employee name for loaded draft:",
									r.message.custom_service_employee,
									employeeError,
								);
							}
						}

						this.eventBus.emit("employee_selected", {
							employee_id: r.message.custom_service_employee,
							employee_name: employeeName,
						});
					}

					// --- NEW: emit explicit custom field events so children can populate reliably ---
					this.eventBus.emit("set_contact_mobile", r.message.contact_mobile || "");
					this.eventBus.emit("set_custom_vehicle_no", r.message.custom_vehicle_no || "");
					// keep odometer as string if present
					this.eventBus.emit(
						"set_custom_odometer_reading",
						r.message.custom_odometer_reading || "",
					);
					// coerce has_oil_item to boolean (1/"1" => true)
					this.eventBus.emit(
						"set_custom_has_oil_item",
						Boolean(Number(r.message.custom_has_oil_item)) || false,
					);

					// Emit customer type for corporate detection
					this.eventBus.emit("customer_selected", {
						customer: r.message.customer,
						customer_type: r.message.customer_type || "Individual",
					});

					this.eventBus.emit("show_message", {
						title: __("Draft invoice {0} loaded successfully", [draft_name]),
						color: "success",
					});

					// Auto-reload job orders after a draft is loaded
					this.refreshDrafts();
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

			this.eventBus.on("register_pos_data", (data) => {
				this.pos_profile = data.pos_profile;
				this.pos_opening_shift = data.pos_opening_shift;
				this.get_offers(this.pos_profile.name, this.pos_profile);
				this.eventBus.emit("register_pos_profile", data);
				this.active_price_list = this.pos_profile.selling_price_list;
			});

			this.eventBus.on("register_pos_profile", async (data) => {
				this.pos_profile = data.pos_profile;
				this.get_offers(this.pos_profile.name, this.pos_profile);
				this.get_items_groups();
				this.refreshDrafts();
				this.startDraftsAutoRefresh();
				await this.initializeItems();
				this.items_view = this.pos_profile.posa_default_card_view ? "card" : "list";
				this.active_price_list = this.pos_profile.selling_price_list;
			});

			this.eventBus.on("show_offers", (data) => {
				this.showOffers = data === "true";
				this.showCoupons = false;
			});

			this.eventBus.on("show_coupons", (data) => {
				this.showCoupons = data === "true";
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

			this.eventBus.on("refresh_drafts", () => {
				this.refreshDrafts();
			});

			this.eventBus.on("update_offers_counters", (data) => {
				this.offersCount = data.offersCount || 0;
			});

			this.eventBus.on("update_coupons_counters", (data) => {
				this.couponsCount = data.couponsCount || 0;
			});

			this.eventBus.on("barcode_scanned", (code) => {
				this.onBarcodeScanned(code);
			});
		});

		this._handleDraftsVisibility = () => {
			if (!document.hidden && this.shouldAutoRefreshDrafts()) {
				this.refreshDrafts();
			}
		};
		document.addEventListener("visibilitychange", this._handleDraftsVisibility);
	},

	beforeUnmount() {
		this.stopDraftsAutoRefresh();
		if (this._handleDraftsVisibility) {
			document.removeEventListener("visibilitychange", this._handleDraftsVisibility);
		}
		this.eventBus.off("close_opening_dialog");
		this.eventBus.off("register_pos_data");
		this.eventBus.off("register_pos_profile");
		this.eventBus.off("show_offers");
		this.eventBus.off("show_coupons");
		this.eventBus.off("items_loaded");
		this.eventBus.off("customers_loaded");
		this.eventBus.off("draft_selected");
		this.eventBus.off("refresh_drafts");
		this.eventBus.off("update_offers_counters");
		this.eventBus.off("update_coupons_counters");
		this.eventBus.off("barcode_scanned");

		if (this.isFullscreen) {
			document.body.style.overflow = "";
			document.body.style.paddingTop = "";
			document.documentElement.style.overflow = "";
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
	height: 100%;
	flex: 1 1 auto;
	min-height: 0;
	overflow: hidden;
	background: #fff;
	padding: 0;
	margin: 0;
}

.pos-app-container.fullscreen-mode {
	position: fixed !important;
	top: 0 !important;
	left: 0 !important;
	right: 0 !important;
	bottom: 0 !important;
	width: 100% !important;
	height: 100% !important;
	z-index: 1100 !important;
	overflow: hidden !important;
}

@media (min-width: 1280px) {
	.pos-scale-wrapper {
		--pos-scale: 0.85;

		position: fixed;
		top: 60px;
		left: 0;

		transform: scale(var(--pos-scale));
		transform-origin: top left;

		width: calc(100% / var(--pos-scale));
		height: calc((100vh - 60px) / var(--pos-scale));

		overflow: hidden;
		z-index: 1;
	}

	/* ===== FULLSCREEN: SAME SCALE, REMOVE NAVBAR OFFSET ===== */
	.pos-scale-wrapper.fullscreen-mode {
		--pos-scale: 0.85;

		position: fixed !important;
		top: 0 !important;
		left: 0 !important;

		transform: scale(var(--pos-scale)) !important;
		transform-origin: top left !important;

		width: calc(100% / var(--pos-scale)) !important;
		height: calc(100vh / var(--pos-scale)) !important;

		overflow: hidden !important;
		z-index: 1100 !important;
	}
}

/* Main POS Container */
.pos-main-container {
	position: relative;
	flex: 1;
	width: 100%;
	height: 100%;
	min-height: 0;
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
	z-index: 1100;
	background: white;
	overflow: auto;
	transform: none !important;
	width: 100%;
	height: 100%;
}

/* Ensure all interactive elements work in fullscreen */
.pos-main-container.fullscreen-mode * {
	pointer-events: auto !important;
}

/* Ensure dropdowns and dialogs appear above fullscreen */
.pos-main-container.fullscreen-mode .v-overlay,
.pos-main-container.fullscreen-mode .v-menu,
.pos-main-container.fullscreen-mode .v-dialog,
.pos-main-container.fullscreen-mode .v-autocomplete__content,
.pos-main-container.fullscreen-mode .v-select__content {
	z-index: 9999 !important;
	position: fixed !important;
}

/* Ensure invoice content is interactive */
.pos-main-container.fullscreen-mode .invoice-wrapper,
.pos-main-container.fullscreen-mode .invoice-card,
.pos-main-container.fullscreen-mode .invoice-content {
	pointer-events: auto !important;
	position: relative;
	z-index: auto;
}

/* Ensure input fields are clickable */
.pos-main-container.fullscreen-mode input,
.pos-main-container.fullscreen-mode textarea,
.pos-main-container.fullscreen-mode button,
.pos-main-container.fullscreen-mode .v-field,
.pos-main-container.fullscreen-mode .v-input,
.pos-main-container.fullscreen-mode .v-btn {
	pointer-events: auto !important;
	position: relative;
	z-index: 1;
}

/* Ensure customer dropdown works */
.pos-main-container.fullscreen-mode .v-autocomplete,
.pos-main-container.fullscreen-mode .v-select {
	pointer-events: auto !important;
	z-index: 10 !important;
}

.pos-layout {
	display: flex;
	width: 100%;
	height: 100%;
	min-height: 0;
	gap: 6px; /* Consistent gap */
	padding: 6px; /* Consistent padding */
	margin: 0;
	overflow: hidden;
	flex-wrap: nowrap; /* CRITICAL: No wrapping! */
}

/* BASE COLUMN STYLES */
.pos-column {
	display: flex;
	flex-direction: column;
	height: 100%;
	overflow: hidden;
	min-width: 0; /* CRITICAL: Allows flex shrinking */
	pointer-events: auto;
	position: relative;
}

@media (min-width: 1920px) {
	.pos-column {
		padding: 8px 6px;
	}

	.drafts-column {
		flex: 0 0 20%;
		min-width: 250px;
	}

	.invoice-column {
		flex: 0 0 55%;
		min-width: 500px;
	}

	.items-column {
		flex: 0 0 25%;
		min-width: 300px;
	}
}

/* ============================================
   LAPTOP (1400px - 1919px) - Flex scaling
   ============================================ */
@media (min-width: 1400px) and (max-width: 1919px) {
	.pos-column {
		padding: 6px 4px; /* Reduce padding */
	}

	.drafts-column {
		flex: 0 0 20%; /* Keep percentage for scaling */
		min-width: 180px; /* Lower minimum */
	}

	.invoice-column {
		flex: 0 0 55%; /* Scales with screen */
		min-width: 350px; /* Lower minimum */
	}

	.items-column {
		flex: 0 0 25%; /* Scales with screen */
		min-width: 150px; /* Lower minimum */
	}
}

/* ============================================
   TIGHT LAPTOP (1280px - 1399px) - Compact
   ============================================ */
@media (min-width: 1280px) and (max-width: 1399px) {
	.pos-column {
		padding: 4px 2px; /* Minimal padding */
	}

	.drafts-column {
		flex: 0 0 auto;
		width: 22%; /* Fixed percentage */
		min-width: 140px; /* Very low minimum */
	}

	.invoice-column {
		flex: 1 1 auto; /* Take remaining space */
		min-width: 300px; /* Can go lower */
	}

	.items-column {
		flex: 0 0 auto;
		width: 22%; /* Fixed percentage */
		min-width: 120px; /* Very low minimum */
	}
}

/* Columns */
.pos-column {
	display: flex;
	flex-direction: column;
	height: 100%;
	padding: 8px 6px;
	overflow: hidden;
	min-width: 0;
	position: relative;
	/* Add this */
	pointer-events: auto;
	/* Add this */
}

/* Ensure columns work in fullscreen */
.fullscreen-mode .pos-column {
	pointer-events: auto !important;
	overflow: visible;
	/* Allow dropdowns to overflow */
}

/* ============================================
   DESKTOP & LAPTOP MAIN LAYOUT (1280px+)
   ============================================ */

@media (min-width: 1280px) {
	.drafts-column,
	.items-column {
		flex: 0 0 22%;
		min-width: 220px;
		max-width: 26%;
	}

	.invoice-column {
		flex: 1 1 auto; /* take remaining space */
		min-width: 420px;
	}
}

/* .drafts-column {
	flex: 0 0 20%;
	padding-left: 1px;
	padding-right: 2px;
	flex-shrink: 0;
	pointer-events: auto;
	min-width: 260px;
} */

/* .invoice-column {
	flex: 2 1 520px;
	padding-left: 3px;
	padding-right: 3px;
	pointer-events: auto;
	z-index: 2;
	min-width: 320px;
} */

.invoice-column .column-card {
	border-radius: 14px;
}

/* .items-column {
	flex: 1 1 300px;
	padding-left: 2px;
	padding-right: 1px;
	pointer-events: auto;
	min-width: 240px;
} */

/* Column Card */
.column-card {
	display: flex;
	flex-direction: column;
	height: 100%;
	border: 1px solid #ececec;
	border-radius: 12px;
	overflow: hidden;
	background: #ffffff;
	transition: border-color 0.2s ease;
	position: relative;
	flex: 1 1 auto;
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
	padding: 8px;
	background-color: white;
	min-height: 0;
}

.drafts-wrapper-container :deep(.drafts-footer) {
	position: relative;
	bottom: 0;
	padding: 12px;
	background: white;
	border-top: 2px solid #e0e0e0;
}

/* === BUTTON STYLING  */

/* BUTTONS - Responsive sizing */
.offer-style-btn,
.coupon-style-btn {
	width: 100% !important;
	height: 40px !important; /* Reduce from 44px */
	padding: 0 10px !important; /* Reduce from 12px */
	margin: 0 !important;
	border-radius: 6px !important; /* Reduce from 8px */
	display: flex !important;
	align-items: center !important;
	justify-content: center !important;
	gap: 6px !important; /* Reduce from 8px */
	font-weight: 600 !important;
	font-size: 12px !important; /* Reduce from 13px */
	color: white !important;
	transition: all 0.2s ease !important;
}

@media (min-width: 1920px) {
	.offer-style-btn,
	.coupon-style-btn {
		height: 44px !important;
		font-size: 13px !important;
	}
}

.offer-style-btn {
	background: linear-gradient(90deg, #ff9800, #f57c00) !important;
}

.coupon-style-btn {
	background: linear-gradient(90deg, #2196f3, #1976d2) !important;
}

.offer-style-btn:hover,
.coupon-style-btn:hover {
	transform: translateY(-2px);
}

.offer-style-btn:active,
.coupon-style-btn:active {
	transform: translateY(0);
}

/* Button text styling */
.btn-text {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	line-height: 1;
}

.btn-title {
	font-size: 13px;
	font-weight: 600;
	white-space: nowrap;
}

/* Reset Vuetify Grid */
.items-footer-filters :deep(.v-col) {
	padding: 3px !important; /* Reduce from 4px */
}

.items-footer-filters :deep(.v-row) {
	margin: 0 !important;
}
/* Invoice Card */
.invoice-card {
	overflow: hidden;
}

/* SCROLLBARS */
.column-scroll-content::-webkit-scrollbar,
.drafts-wrapper-container :deep(.drafts-content::-webkit-scrollbar),
.invoice-wrapper :deep(.invoice-content::-webkit-scrollbar) {
	width: 6px;
}

.column-scroll-content::-webkit-scrollbar-thumb,
.drafts-wrapper-container :deep(.drafts-content::-webkit-scrollbar-thumb),
.invoice-wrapper :deep(.invoice-content::-webkit-scrollbar-thumb) {
	background: rgba(0, 0, 0, 0.25);
	border-radius: 3px;
}

.column-scroll-content::-webkit-scrollbar-thumb:hover,
.drafts-wrapper-container :deep(.drafts-content::-webkit-scrollbar-thumb:hover),
.invoice-wrapper :deep(.invoice-content::-webkit-scrollbar-thumb:hover) {
	background: rgba(0, 0, 0, 0.4);
}

/* Items Card with Footer */
.items-card {
	position: relative;
}

/* Column Header */
.column-header {
	background: white;
	padding: 10px 12px;
	font-weight: 600;
	font-size: 18px;
	display: flex;
	align-items: center;
	gap: 8px;
	min-height: 48px;
	flex-shrink: 0;
	color: #333;
	border-bottom: 1px solid #e5e7eb;
	flex-wrap: wrap;
}
@media (max-width: 1400px) {
	.column-header {
		font-size: 16px;
		padding: 8px 10px;
		min-height: 44px;
	}
}
.column-header .v-icon {
	font-size: 20px;
}

/* Scrollable Content */
.column-scroll-content {
	flex: 1;
	overflow-y: auto;
	overflow-x: hidden;
	padding: 8px;
	background-color: white;
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
	padding: 0;
}
/* Invoice Wrapper */
.invoice-wrapper {
	flex: 1;
	overflow: hidden;
	display: flex;
	flex-direction: column;
	width: 100%;
	min-height: 0;
	position: relative;
}

/* Ensure invoice content is scrollable and interactive in fullscreen */
.fullscreen-mode .invoice-wrapper {
	overflow: visible;
	/* Change from hidden */
	pointer-events: auto !important;
}

.invoice-wrapper :deep(.invoice-container) {
	display: flex;
	flex-direction: column;
	height: 100%;
	width: 100%;
	pointer-events: auto;
	/* Add this */
}

.invoice-wrapper :deep(.invoice-content) {
	flex: 1;
	overflow-y: auto;
	overflow-x: hidden;
	padding: 10px 12px;
	background-color: #ffffff;
	min-height: 0;
	pointer-events: auto;
}

.items-card {
	display: flex;
	flex-direction: column;
	height: 100%;
}

.column-scroll-content {
	flex: 1;
	overflow-y: auto;
}

.items-footer-filters {
	position: sticky;
	bottom: 0;
	background: #fff;
	z-index: 10;
	flex-shrink: 0;
	padding: 8px;
	border-top: 1px solid #e0e0e0;
	overflow: visible; /* key */
	max-height: none; /* key */
}

@media (max-width: 1400px) {
	.items-footer-filters {
		padding: 6px;
	}
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
	background: white;
	border-radius: 3px;
}

.drafts-wrapper-container :deep(.drafts-content::-webkit-scrollbar-thumb),
.invoice-wrapper :deep(.invoice-content::-webkit-scrollbar-thumb),
.column-scroll-content::-webkit-scrollbar-thumb {
	background: rgba(0, 0, 0, 0.25);
	border-radius: 3px;
}

.drafts-wrapper-container :deep(.drafts-content::-webkit-scrollbar-thumb:hover),
.invoice-wrapper :deep(.invoice-content::-webkit-scrollbar-thumb:hover),
.column-scroll-content::-webkit-scrollbar-thumb:hover {
	background: rgba(0, 0, 0, 0.4);
}

/* Responsive - Tablet */
@media (max-width: 1024px) {
	.pos-layout {
		flex-wrap: wrap;
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

@media (max-width: 1200px) {
	.invoice-column {
		order: 1;
		flex: 1 1 100%;
	}

	.drafts-column {
		order: 2;
		flex: 1 1 50%;
	}

	.items-column {
		order: 3;
		flex: 1 1 50%;
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

/* FIX: Add New Customer / Add New Vehicle buttons not clickable in fullscreen */
.fullscreen-mode .invoice-wrapper :deep(.v-input__prepend),
.fullscreen-mode .invoice-wrapper :deep(.v-input__prepend-inner),
.fullscreen-mode .invoice-wrapper :deep(.v-field__prepend-inner),
.fullscreen-mode .invoice-wrapper :deep(.v-input__append),
.fullscreen-mode .invoice-wrapper :deep(.v-input__append-inner),
.fullscreen-mode .invoice-wrapper :deep(.v-field__append-inner) {
	position: relative !important;
	z-index: 999999 !important;
	pointer-events: auto !important;
}

/* Fix for autocomplete menu overlapping */
.fullscreen-mode :deep(.v-overlay__content) {
	z-index: 999999 !important;
	position: fixed !important;
}

/* Ensure append icons remain clickable */
.fullscreen-mode :deep(.v-icon) {
	pointer-events: auto !important;
}

.items-footer-filters .v-text-field {
	margin-bottom: 12px;
}

.items-footer-filters .v-text-field:deep(.v-field) {
	border-radius: 8px;
	background-color: white;
	border: 1.5px solid #b8c1cc !important;
}

.items-footer-filters :deep(.v-select .v-field),
.items-footer-filters :deep(.items-group-full .v-field) {
	border-radius: 8px;
	background-color: white;
	border: 1.5px solid #b8c1cc !important;
}

.items-footer-filters :deep(.v-field__overlay) {
	opacity: 0.02 !important;
}

.items-footer-filters .v-text-field:deep(input) {
	padding: 8px !important;
}

/* Ensure search input is focused when clicked */
.items-footer-filters .v-text-field:deep(.v-field__input) {
	cursor: text;
}

.offer-style-btn,
.coupon-style-btn {
	width: 100% !important;
}

.drafts-column {
	overflow: hidden;
}

@media (min-width: 1280px) {
	.drafts-footer {
		position: relative;
	}
}
/* Compact Invoice Footer Area */
.cards {
	padding-top: 8px !important;
	padding-bottom: 8px !important;
}

/* Final override: always-visible borders for right panel search/item group fields */
:deep(.items-footer-filters .v-text-field .v-field),
:deep(.items-footer-filters .v-select .v-field),
:deep(.items-footer-filters .items-group-full .v-field) {
	border: 1px solid #0f0f0f !important;
	background-color: #fff !important;
}

:deep(.items-footer-filters .v-field__overlay) {
	opacity: 0 !important;
}

/* Final desktop/laptop layout override: remove outer and inter-column gaps */
@media (min-width: 1280px) {
	.pos-layout {
		gap: 0 !important;
		padding: 0 !important;
	}

	.pos-column {
		padding: 0 !important;
	}

	.column-card {
		margin: 0 !important;
	}

	.pos-main-container.fullscreen-mode .pos-layout {
		gap: 0 !important;
		padding: 0 !important;
	}
}
</style>
