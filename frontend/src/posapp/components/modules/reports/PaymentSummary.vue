<template>
	<div>
		<h2 class="text-xl font-semibold mb-4">Payment Summary</h2>

		<!-- Filters -->
		<div class="grid grid-cols-3 gap-2 mb-4">
			<input type="date" v-model="dateFrom" class="input" placeholder="Date From" />
			<input type="date" v-model="dateTo" class="input" placeholder="Date To" />
			<select v-model="paymentType" class="input">
				<option value="">All Payment Types</option>
				<option value="Cash">Cash</option>
				<option value="Card">Credit Card</option>
				<option value="Coupon">Coupon</option>
			</select>
			<button class="btn col-span-3" @click="generateReport">Generate Report</button>
		</div>

		<!-- Report Table -->
		<table class="table-auto border w-full">
			<thead>
				<tr>
					<th>Date</th>
					<th>Transaction Number</th>
					<th>Payment Code</th>
					<th>Amount</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="(row, index) in reportData" :key="index">
					<td>{{ row.date }}</td>
					<td>{{ row.transaction_number }}</td>
					<td>{{ row.payment_code }}</td>
					<td>{{ row.amount }}</td>
				</tr>
				<tr v-if="reportData.length === 0">
					<td colspan="4" class="text-center">No records found.</td>
				</tr>
			</tbody>
			<tfoot>
				<tr>
					<td colspan="3" class="text-right font-semibold">Grand Total</td>
					<td>{{ grandTotal }}</td>
				</tr>
			</tfoot>
		</table>
	</div>
</template>

<script setup>
import { ref, computed } from "vue";
import axios from "axios";

const dateFrom = ref("");
const dateTo = ref("");
const paymentType = ref("");
const reportData = ref([]);

// Fetch data from API
const generateReport = async () => {
	try {
		const response = await axios.get(
			"/api/method/posawesome.posawesome.api.lazer_pos.get_payment_summary_list",
			{
				params: {
					from_date: dateFrom.value,
					to_date: dateTo.value,
					payment_type: paymentType.value || undefined,
				},
			},
		);
		reportData.value = response.data.message || [];
	} catch (error) {
		console.error("Error fetching report:", error);
		alert("Failed to fetch report. See console for details.");
	}
};

// Compute grand total
const grandTotal = computed(() => {
	return reportData.value.reduce((sum, row) => sum + (parseFloat(row.amount) || 0), 0);
});
</script>

<style scoped>
.input {
	border: 1px solid #ccc;
	padding: 4px;
	width: 100%;
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
.table-auto th,
.table-auto td {
	padding: 4px 6px;
	border: 1px solid #ccc;
	text-align: left;
}
</style>
