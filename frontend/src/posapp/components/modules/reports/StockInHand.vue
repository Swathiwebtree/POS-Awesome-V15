<template>
	<div>
		<h2 class="text-xl font-semibold mb-4">Stock In Hand</h2>

		<!-- Filters -->
		<div class="grid grid-cols-2 gap-2 mb-4">
			<input type="date" v-model="postingDate" class="input" placeholder="Posting Date" />
			<input v-model="warehouse" class="input" placeholder="Warehouse" />
			<button class="btn" @click="getStockInHand">Get Stock</button>
		</div>

		<!-- Report Table -->
		<table class="table-auto border w-full" v-if="stockData.length">
			<thead>
				<tr>
					<th>Item Code</th>
					<th>Item Name</th>
					<th>Unit</th>
					<th>Warehouse</th>
					<th>Quantity</th>
					<th>Valuation Rate</th>
					<th>Amount</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="(row, index) in stockData" :key="index">
					<td>{{ row.item_code }}</td>
					<td>{{ row.item_name }}</td>
					<td>{{ row.unit }}</td>
					<td>{{ row.warehouse }}</td>
					<td>{{ row.quantity }}</td>
					<td>{{ row.valuation_rate }}</td>
					<td>{{ row.amount }}</td>
				</tr>
			</tbody>
			<tfoot>
				<tr>
					<td colspan="4" class="text-right font-semibold">Totals</td>
					<td>{{ totalQuantity }}</td>
					<td></td>
					<td>{{ totalAmount }}</td>
				</tr>
			</tfoot>
		</table>

		<div v-else class="text-center mt-4 text-gray-600">No stock records found.</div>
	</div>
</template>

<script setup>
import { ref, computed } from "vue";

const postingDate = ref("");
const warehouse = ref("");
const stockData = ref([]);

// Compute totals
const totalQuantity = computed(() => stockData.value.reduce((sum, row) => sum + (row.quantity || 0), 0));
const totalAmount = computed(() => stockData.value.reduce((sum, row) => sum + (row.amount || 0), 0));

// Fetch Stock In Hand via Frappe API
const getStockInHand = () => {
	const filters = {
		posting_date: postingDate.value || null,
		warehouse: warehouse.value || null,
	};

	frappe.call({
		method: "posawesome.posawesome.api.lazer_pos.get_stock_in_hand",
		args: { filters },
		callback: (r) => {
			if (r.message) {
				stockData.value = r.message;
			} else {
				stockData.value = [];
				frappe.msgprint("No stock records found.");
			}
		},
	});
};
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
	padding: 4px 8px;
	cursor: pointer;
	margin-top: 4px;
	font-size: 0.875rem;
}
.btn:hover {
	background: #0056b3;
}
table {
	border-collapse: collapse;
}
th,
td {
	border: 1px solid #ccc;
	padding: 6px;
	text-align: center;
}
tfoot td {
	font-weight: bold;
}
</style>
