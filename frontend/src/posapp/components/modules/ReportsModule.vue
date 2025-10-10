<template>
	<ModuleShell title="Reports">
		<v-list>
			<v-list-item
				v-for="(report, index) in reports"
				:key="index"
				@click="openReport(report.name)"
				class="report-item"
			>
				<v-list-item-title>{{ report.label }}</v-list-item-title>
			</v-list-item>
		</v-list>
	</ModuleShell>
</template>

<script>
import ModuleShell from "./ModuleShell.vue";

export default {
	name: "ReportsModule",
	components: { ModuleShell },
	data() {
		return {
			reports: [
				{ name: "BillsListingWorkOrder", label: "Bills Listing - Work Order" },
				{ name: "BillsListingVehicle", label: "Bills Listing - Vehicle" },
				{ name: "PaymentSummary", label: "Payment Summary" },
				{ name: "StockInHand", label: "Stock in Hand" },
				{ name: "StockSales", label: "Stock Sales" },
				{ name: "SalesPoints", label: "Sales Points" },
				{ name: "SalesTransaction", label: "Sales Transaction" }, // If needed
			],
		};
	},
	methods: {
		openReport(reportName) {
			// Emit the selected report so the parent (or router) can load the page
			this.$emit("change-page", reportName);
		},
	},
};
</script>

<style scoped>
.report-item {
	cursor: pointer;
}
</style>
