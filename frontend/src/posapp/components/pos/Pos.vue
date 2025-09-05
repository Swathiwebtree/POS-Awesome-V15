<template>
	<div
		class="pos-main-container dynamic-container"
		:class="rtlClasses"
		:style="[responsiveStyles, rtlStyles]"
	>
		<ClosingDialog></ClosingDialog>
		<Drafts></Drafts>
		<SalesOrders></SalesOrders>
		<Returns></Returns>
		<NewAddress></NewAddress>
		<MpesaPayments></MpesaPayments>
		<Variants></Variants>
		<OpeningDialog v-if="dialog" :dialog="dialog"></OpeningDialog>

		<!-- PIN Dialog -->
		<!-- <PinDialog
			v-model="showPin"
			:expectedPin="pos_settings && pos_settings.custom_cashier_code_"
			@success="onPinSuccess"
		/> -->

		<!-- Main Screen -->
		<div v-if="!dialog && showMainMenu && !currentSubmodule">
			<MainMenu
				@open-transactions="handleOpenTransactions"
				@open-module="handleOpenModule"
			/>
		</div>

		<!-- Transactions Sub-Menu -->
		<div v-else-if="!dialog && showTransactions && !currentSubmodule">
			<TransactionsMenu
				@back="() => { showTransactions = false }"
				@select="handleSelectSubmodule"
			/>
		</div>

		<!-- Submodules Screens -->
		<div v-else-if="currentSubmodule">
			<component
				:is="currentSubmodule"
				@back="closeSubmodule"
			/>
		</div>

		<!-- POS Main Screen for a selected work order -->
		<div v-else-if="!dialog && selectedWorkOrder">
			<PosMain :work-order="selectedWorkOrder" />
		</div>

		<!-- Original POS UI -->
		<v-row
			v-else
			dense
			class="ma-0 dynamic-main-row"
		>
			<v-col
				v-show="!payment && !showOffers && !coupons"
				xl="5"
				lg="5"
				md="5"
				sm="5"
				cols="12"
				class="pos dynamic-col"
			>
				<ItemsSelector></ItemsSelector>
			</v-col>
			<v-col
				v-show="showOffers"
				xl="5"
				lg="5"
				md="5"
				sm="5"
				cols="12"
				class="pos dynamic-col"
			>
				<PosOffers></PosOffers>
			</v-col>
			<v-col
				v-show="coupons"
				xl="5"
				lg="5"
				md="5"
				sm="5"
				cols="12"
				class="pos dynamic-col"
			>
				<PosCoupons></PosCoupons>
			</v-col>
			<v-col
				v-show="payment"
				xl="5"
				lg="5"
				md="5"
				sm="5"
				cols="12"
				class="pos dynamic-col"
			>
				<Payments></Payments>
			</v-col>

			<v-col
				xl="7"
				lg="7"
				md="7"
				sm="7"
				cols="12"
				class="pos dynamic-col"
			>
				<Invoice></Invoice>
			</v-col>
		</v-row>
	</div>
</template>

<script>
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
import MainMenu from "./MainMenu.vue";
import TransactionsMenu from "./TransactionsMenu.vue";
// import PinDialog from "./PinDialog.vue";

// Import your sub-modules 
import VehicleService from "./VehicleService.vue";
import VehiclesMaster from "./VehiclesMaster.vue";

const ServiceIssueNote = { template: '<div class="pa-4"><v-btn variant="text" @click="$emit(`back`)">← Back</v-btn><h2>Service Issue Note</h2></div>' };
const Quotation = { template: '<div class="pa-4"><v-btn variant="text" @click="$emit(`back`)">← Back</v-btn><h2>Quotation</h2></div>' };
const PettyCash = { template: '<div class="pa-4"><v-btn variant="text" @click="$emit(`back`)">← Back</v-btn><h2>Petty Cash</h2></div>' };
const ReceiptVoucher = { template: '<div class="pa-4"><v-btn variant="text" @click="$emit(`back`)">← Back</v-btn><h2>Receipt Voucher</h2></div>' };
const ItemInquiry = { template: '<div class="pa-4"><v-btn variant="text" @click="$emit(`back`)">← Back</v-btn><h2>Item Inquiry</h2></div>' };
const SalesByPayment = { template: '<div class="pa-4"><v-btn variant="text" @click="$emit(`back`)">← Back</v-btn><h2>Sales by Payment</h2></div>' };
const VehicleHistory = { template: '<div class="pa-4"><v-btn variant="text" @click="$emit(`back`)">← Back</v-btn><h2>Vehicle History</h2></div>' };
const RedeemedCouponPoints = { template: '<div class="pa-4"><v-btn variant="text" @click="$emit(`back`)">← Back</v-btn><h2>Redeemed Coupon Points</h2></div>' };

import {
	getOpeningStorage,
	setOpeningStorage,
	clearOpeningStorage,
	initPromise,
	checkDbHealth,
	setTaxTemplate,
} from "../../../offline/index.js";
import { getCurrentInstance } from "vue";
import { usePosShift } from "../../composables/usePosShift.js";
import { useOffers } from "../../composables/useOffers.js";
import { clearExpiredCustomerBalances } from "../../../offline/index.js";
import { useResponsive } from "../../composables/useResponsive.js";
import { useRtl } from "../../composables/useRtl.js";

export default {
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
		SalesOrders,
		MainMenu,
		TransactionsMenu,
		// PinDialog,

		// submodules
		VehicleService,
		VehiclesMaster,
		ServiceIssueNote,
		Quotation,
		PettyCash,
		ReceiptVoucher,
		ItemInquiry,
		SalesByPayment,
		VehicleHistory,
		RedeemedCouponPoints,
	},

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
	data() {
		return {
			dialog: false,
			payment: false,
			showOffers: false,
			coupons: false,
			itemsLoaded: false,
			customersLoaded: false,

			showMainMenu: true,
			showTransactions: false,
			isAuthed: false,
			// showPin: false,
			pendingAction: null,
			// pos_settings: null,

			selectedWorkOrder: null,
			currentSubmodule: null, // Track which submodule is open
		};
	},
	methods: {
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
		requireAuth(cb) {
			// Always allow — skip PIN and cashier code
			if (cb) cb();
		},

		onPinSuccess() {
			// No PIN needed, just mark as authenticated
			this.isAuthed = true;
		},

		// requireAuth(cb) {
		// 	if (this.isAuthed) {
		// 		cb && cb();
		// 	} else {
		// 		this.pendingAction = cb;
		// 		this.showPin = true;
		// 	}
		// },
		// onPinSuccess() {
		// 	this.isAuthed = true;
		// 	if (typeof this.pendingAction === "function") {
		// 		const fn = this.pendingAction;
		// 		this.pendingAction = null;
		// 		fn();
		// 	}
		// },

		handleOpenTransactions() {
			this.requireAuth(() => {
				this.showTransactions = true;
			});
		},
		handleOpenModule(key) {
			this.requireAuth(() => {
				if (key === "exit") {
					window.location.href = "/app"; // exits POS
					return;
				}
				frappe.msgprint(`Module "${key}" is not wired yet.`);
			});
		},
		handleSelectSubmodule(key) {
			this.requireAuth(() => {
				this.currentSubmodule = this.mapKeyToComponent(key);
				this.showTransactions = false;
				this.showMainMenu = false;
			});
		},
		mapKeyToComponent(key) {
			const map = {
				vehicle_service: "VehicleService",
				vehicles_master: "VehiclesMaster",
				service_issue_note: "ServiceIssueNote",
				quotation: "Quotation",
				petty_cash: "PettyCash",
				receipt_voucher: "ReceiptVoucher",
				item_inquiry: "ItemInquiry",
				sales_by_payment: "SalesByPayment",
				vehicle_history: "VehicleHistory",
				redeemed_coupon_points: "RedeemedCouponPoints",
			};
			return map[key] || null;
		},
		closeSubmodule() {
			this.currentSubmodule = null;
			this.showTransactions = true; // go back to transaction menu
		},
	},
	mounted() {
		this.$nextTick(function () {
			this.check_opening_entry?.();
			this.get_pos_setting();
			this.eventBus.on("close_opening_dialog", () => {
				this.dialog = false;
			});
			this.eventBus.on("register_pos_data", (data) => {
				this.pos_profile = data.pos_profile;
				this.get_offers(this.pos_profile.name, this.pos_profile);
				this.pos_opening_shift = data.pos_opening_shift;
				this.eventBus.emit("register_pos_profile", data);
				console.info("LoadPosProfile");
			});
			this.eventBus.on("register_pos_profile", (data) => {
				if (data && data.pos_profile) {
					this.get_offers(data.pos_profile.name, data.pos_profile);
				}
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
			this.eventBus.on("open_closing_dialog", () => {
				this.get_closing_data?.();
			});
			this.eventBus.on("submit_closing_pos", (data) => {
				this.submit_closing_pos?.(data);
			});

			this.eventBus.on("items_loaded", () => {
				this.itemsLoaded = true;
				this.checkLoadingComplete();
			});
			this.eventBus.on("customers_loaded", () => {
				this.customersLoaded = true;
				this.checkLoadingComplete();
			});
			this.eventBus.on("set_pos_settings", (doc) => {
				this.pos_settings = doc;
			});
		});
	},
	beforeUnmount() {
		this.eventBus.off("close_opening_dialog");
		this.eventBus.off("register_pos_data");
		this.eventBus.off("register_pos_profile");
		this.eventBus.off("LoadPosProfile");
		this.eventBus.off("show_offers");
		this.eventBus.off("show_coupons");
		this.eventBus.off("open_closing_dialog");
		this.eventBus.off("submit_closing_pos");
		this.eventBus.off("items_loaded");
		this.eventBus.off("customers_loaded");
	},
	created() {
		clearExpiredCustomerBalances();
		if (this.$route?.params?.workOrder) {
			this.selectedWorkOrder = this.$route.params.workOrder;
			this.showMainMenu = false;
		}
	},
};
</script>
