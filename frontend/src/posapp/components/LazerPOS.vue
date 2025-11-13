<template>
	<!-- Cashier Login Modal -->
	<CashierLogin v-if="showLogin" @loginSuccess="handleLoginSuccess" />

	<div class="LazerPOS flex">
		<!-- Sidebar -->
		<aside class="w-64 bg-gray-100 p-4 min-h-screen">
			<h2 class="text-xl font-bold mb-4">LazerPOS</h2>
			<ul>
				<li v-for="mainModule in sidebarModules" :key="mainModule.name" class="mb-2">
					<!-- Main module name -->
					<div
						class="font-semibold cursor-pointer hover:text-blue-600"
						@click="toggleModule(mainModule.name)"
					>
						{{ mainModule.name }}
					</div>

					<!-- Submodules -->
					<ul v-show="currentModule === mainModule.name" class="ml-4 mt-1">
						<li
							v-for="sub in mainModule.submodules"
							:key="sub"
							class="cursor-pointer hover:text-green-600 text-sm"
							:class="{ 'font-bold text-green-800': currentSubmodule === sub }"
							@click="selectSubmodule(mainModule.name, sub)"
						>
							{{ sub }}
						</li>
					</ul>
				</li>
			</ul>
		</aside>

		<!-- Main Content -->
		<div class="flex-1 p-4 module-content">
			<component v-if="activeComponent" :is="activeComponent" v-bind="activeProps" />
			<div v-else class="pa-4">Select a module or submodule</div>
		</div>
	</div>
</template>

<script setup>
import CashierLogin from "./CashierLogin.vue";
import { ref, computed, defineAsyncComponent } from "vue";

const showLogin = ref(true);
const loggedInCashier = ref(null);

function formatModuleKey(name) {
	// Remove spaces and append 'Module'
	return name.replace(/\s+/g, "") + "Module";
}

/* ===========================
   Import Main Modules
=========================== */
import TransactionsModule from "./modules/TransactionsModule.vue";
import InventoryModule from "./modules/InventoryModule.vue";
import ReportsModule from "./modules/ReportsModule.vue";
import SystemModule from "./modules/SystemModule.vue";
import CashCountingModule from "./modules/CashCountingModule.vue";
import CashierOutModule from "./modules/CashierOutModule.vue";
import DayEndClosingModule from "./modules/DayEndClosingModule.vue";
import ExitModule from "./modules/ExitModule.vue";

/* ===========================
   Transactions Submodules
=========================== */
const transactionSubmodulesMap = {
	"Vehicles Master": "VehiclesMaster",
	"Service Issue Note": "ServiceIssueNote",
	"Quotation": "Quotation",
	"Petty Cash": "PettyCash",
	"Receipt Voucher": "ReceiptVoucher",
	"Item Inquiry": "ItemInquiry",
	"Sales by Payment": "SalesByPayment",
	"Vehicle History": "VehicleHistory",
	"Redeemed Coupon Points": "RedeemedCouponPoints",
};
const transactionComponents = {};
Object.values(transactionSubmodulesMap).forEach((name) => {
	transactionComponents[name] = defineAsyncComponent(() => import(`./modules/transactions/${name}.vue`));
});

/* ===========================
   Inventory Submodules
=========================== */
const inventorySubmodulesMap = {
	"Material Request": "MaterialRequest",
	"Goods Receipt Note": "GoodsReceiptNote",
	"Issue Note": "IssueNote",
	"Transfer In": "TransferIn",
	"Transfer Out": "TransferOut",
	"Physical Count": "PhysicalCount",
	"Production Form": "ProductionForm",
	"Damage Memo": "DamageMemo",
};
const inventoryComponents = {};
Object.values(inventorySubmodulesMap).forEach((name) => {
	inventoryComponents[name] = defineAsyncComponent(() => import(`./modules/inventory/${name}.vue`));
});

/* ===========================
   Reports Submodules
=========================== */
const reportsSubmodulesMap = {
	"Bills Listing - Work Order": "BillsListingWorkOrder",
	"Bills Listing - Vehicle": "BillsListingVehicle",
	"Payment Summary": "PaymentSummary",
	"Stock in Hand": "StockInHand",
	"Stock Sales": "StockSales",
	"Sales Points": "SalesPoints",
	"Sales Transaction": "SalesTransaction",
};
const reportsComponents = {};
Object.values(reportsSubmodulesMap).forEach((name) => {
	reportsComponents[name] = defineAsyncComponent(() => import(`./modules/reports/${name}.vue`));
});

/* ===========================
   Sidebar Data
=========================== */
const sidebarModules = [
	{ name: "Transactions", submodules: Object.keys(transactionSubmodulesMap) },
	{ name: "Inventory", submodules: Object.keys(inventorySubmodulesMap) },
	{ name: "Reports", submodules: Object.keys(reportsSubmodulesMap) },
	{ name: "System", submodules: [] },
	{ name: "Cash Counting", submodules: [] },
	{ name: "Cashier Out", submodules: [] },
	{ name: "Day End Closing", submodules: [] },
	{ name: "Exit", submodules: [] },
];

/* ===========================
   Module Map
=========================== */
const modulesMap = {
	TransactionsModule,
	InventoryModule,
	ReportsModule,
	SystemModule,
	CashCountingModule,
	CashierOutModule,
	DayEndClosingModule,
	ExitModule,
};

/* ===========================
   Reactive State
=========================== */
const currentModule = ref("Transactions");
const currentSubmodule = ref("Vehicle Master");
const currentModuleComponent = ref("TransactionsModule");

/* ===========================
   Methods
=========================== */
function toggleModule(moduleName) {
	currentModule.value = moduleName;
	currentModuleComponent.value = formatModuleKey(moduleName);

	const mod = sidebarModules.find((m) => m.name === moduleName);
	currentSubmodule.value = mod?.submodules?.[0] || "";
}

function selectSubmodule(mainModule, submoduleLabel) {
	currentModule.value = mainModule;
	currentSubmodule.value = submoduleLabel;
	currentModuleComponent.value = formatModuleKey(mainModule); //
}

function handleLoginSuccess(username) {
	loggedInCashier.value = username; // store the cashier username
	showLogin.value = false; // hide the login modal
}

/* ===========================
   Computed Properties
=========================== */
const activeComponent = computed(() => {
	if (currentModuleComponent.value === "TransactionsModule") {
		const compName = transactionSubmodulesMap[currentSubmodule.value];
		return transactionComponents[compName] || TransactionsModule;
	}
	if (currentModuleComponent.value === "InventoryModule") {
		const compName = inventorySubmodulesMap[currentSubmodule.value];
		return inventoryComponents[compName] || InventoryModule;
	}
	if (currentModuleComponent.value === "ReportsModule") {
		const compName = reportsSubmodulesMap[currentSubmodule.value];
		return reportsComponents[compName] || ReportsModule;
	}
	return modulesMap[currentModuleComponent.value] || null;
});

const activeProps = computed(() => {
	if (currentModuleComponent.value === "TransactionsModule") {
		const compName = transactionSubmodulesMap[currentSubmodule.value];
		return { defaultSubmodule: compName };
	}
	if (currentModuleComponent.value === "InventoryModule") {
		const compName = inventorySubmodulesMap[currentSubmodule.value];
		return { defaultSubmodule: compName };
	}
	if (currentModuleComponent.value === "ReportsModule") {
		const compName = reportsSubmodulesMap[currentSubmodule.value];
		return { defaultSubmodule: compName };
	}
	return {};
});
</script>

<style scoped>
.LazerPOS {
	display: flex;
	min-height: 100vh;
}
aside ul li ul li {
	padding-left: 0.5rem;
}
.module-content {
	background-color: #fff;
	min-height: 100vh;
}
.font-bold.text-green-800 {
	font-weight: bold;
	color: #2a7f2e;
}
</style>
