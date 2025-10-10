<template>
	<div>
		<h2 class="text-xl font-semibold mb-4">Stock Sales</h2>

		<!-- Filters -->
		<div class="grid grid-cols-3 gap-2 mb-4">
			<input type="date" v-model="dateFrom" class="input" placeholder="From Date" />
			<input type="date" v-model="dateTo" class="input" placeholder="To Date" />
			<select v-model="department" class="input">
				<option value="">Select Department</option>
				<option>Sales</option>
				<option>Service</option>
			</select>
			<select v-model="mainCategory" class="input">
				<option value="">Main Category</option>
				<option>Category A</option>
				<option>Category B</option>
			</select>
			<select v-model="subCategory" class="input">
				<option value="">Sub Category</option>
				<option>Sub 1</option>
				<option>Sub 2</option>
			</select>
			<input v-model="stockItem" placeholder="Stock Item" class="input" />
			<select v-model="stockType" class="input">
				<option value="">Stock Type</option>
				<option>Consumable</option>
				<option>Fixed Asset</option>
			</select>
			<button class="btn col-span-3" @click="generateReport">Generate Report</button>
		</div>

		<!-- Grouping Options -->
		<div class="mb-4">
			<label class="mr-2">Group By:</label>
			<select v-model="groupBy" class="input w-1/4">
				<option value="">None</option>
				<option value="salesman">Salesman</option>
				<option value="stockItem">Stock Item</option>
				<option value="department">Department</option>
				<option value="mainCategory">Main Category</option>
				<option value="subCategory">Sub Category</option>
			</select>
		</div>

		<!-- Report Table -->
		<table class="table-auto border w-full">
			<thead>
				<tr>
					<th>Date</th>
					<th>Sales Type</th>
					<th>Quantity</th>
					<th>Amount</th>
					<th>Discount</th>
					<th>Net Sales</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="(row, index) in reportData" :key="index">
					<td>{{ row.date }}</td>
					<td>{{ row.salesType }}</td>
					<td>{{ row.qty }}</td>
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
import axios from "axios";

const dateFrom = ref("");
const dateTo = ref("");
const department = ref("");
const mainCategory = ref("");
const subCategory = ref("");
const stockItem = ref("");
const stockType = ref("");
const groupBy = ref("");

const reportData = ref([]);

// Compute grand total
const grandTotal = computed(() => {
	return reportData.value.reduce((sum, row) => sum + (row.netSales || 0), 0);
});

// Fetch report from API
const generateReport = async () => {
	try {
		const params = {
			start_date: dateFrom.value,
			end_date: dateTo.value,
			department: department.value,
			main_category: mainCategory.value,
			sub_category: subCategory.value,
			stock_item_from: stockItem.value,
			stock_item_to: stockItem.value,
			group_by: groupBy.value,
		};
		const response = await axios.get(
			"/api/method/posawesome.posawesome.api.lazer_pos.get_stock_sales_list",
			{ params },
		);
		let data = response.data.message;

		// If grouped, flatten object for table display
		if (groupBy.value && typeof data === "object" && !Array.isArray(data)) {
			const flattened = [];
			Object.keys(data).forEach((key) => {
				data[key].forEach((row) => flattened.push(row));
			});
			reportData.value = flattened;
		} else {
			reportData.value = data;
		}
	} catch (error) {
		console.error("Error fetching stock sales:", error);
		alert("Failed to generate report");
	}
};
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
