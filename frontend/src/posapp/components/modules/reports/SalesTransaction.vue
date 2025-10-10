<template>
	<div>
		<h2 class="text-xl font-semibold mb-4">Sales Transaction</h2>

		<!-- Filters -->
		<div class="grid grid-cols-3 gap-2 mb-4">
			<input type="date" v-model="dateFrom" class="input" />
			<input type="date" v-model="dateTo" class="input" />
			<select v-model="salesType" class="input">
				<option value="">Sales Type</option>
				<option>Retail</option>
				<option>Wholesale</option>
			</select>
			<button class="btn col-span-3" @click="generateReport">Generate Report</button>
		</div>

		<!-- Report Table -->
		<table class="table-auto border w-full">
			<thead>
				<tr>
					<th>Date</th>
					<th>Transaction No.</th>
					<th>Sales Type</th>
					<th>Amount</th>
					<th>Discount</th>
					<th>Net Sales</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="(row, index) in reportData" :key="index">
					<td>{{ row.date }}</td>
					<td>{{ row.txnNo }}</td>
					<td>{{ row.salesType }}</td>
					<td>{{ row.amount }}</td>
					<td>{{ row.discount }}</td>
					<td>{{ row.netSales }}</td>
				</tr>
			</tbody>
			<tfoot>
				<tr>
					<td colspan="5" class="text-right font-semibold">Grand Total</td>
					<td>{{ grandTotal }}</td>
				</tr>
			</tfoot>
		</table>
	</div>
</template>

<script setup>
import { ref, computed } from "vue";

const dateFrom = ref("");
const dateTo = ref("");
const salesType = ref("");

const reportData = ref([
	{ date: "2025-10-01", txnNo: "TX001", salesType: "Retail", amount: 1000, discount: 50, netSales: 950 },
	{
		date: "2025-10-02",
		txnNo: "TX002",
		salesType: "Wholesale",
		amount: 2000,
		discount: 100,
		netSales: 1900,
	},
]);

const generateReport = () => alert("Report generated!");

const grandTotal = computed(() => reportData.value.reduce((sum, row) => sum + row.netSales, 0));
</script>

<style scoped>
.input {
	border: 1px solid #ccc;
	padding: 4px;
	width: 100%;
	margin-bottom: 4px;
}
.btn {
	background: #007bff;
	color: white;
	padding: 6px 12px;
	cursor: pointer;
	margin-top: 4px;
}
.btn:hover {
	background: #0056b3;
}
.table-auto {
	border-collapse: collapse;
}
.table-auto th,
.table-auto td {
	border: 1px solid #ccc;
	padding: 6px;
}
</style>
