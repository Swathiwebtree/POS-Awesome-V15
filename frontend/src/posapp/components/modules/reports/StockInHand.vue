<template>
	<div>
		<h2 class="text-xl font-semibold mb-4">Stock in Hand</h2>

		<!-- Filters -->
		<div class="grid grid-cols-3 gap-2 mb-4">
			<input v-model="filters.itemCode" placeholder="Item Code" class="input" />
			<input v-model="filters.location" placeholder="Location" class="input" />
			<button class="btn col-span-3" @click="fetchStock">Fetch Stock</button>
		</div>

		<!-- Stock Table -->
		<table class="table-auto border w-full">
			<thead>
				<tr>
					<th>Item Code</th>
					<th>Item Name</th>
					<th>Unit</th>
					<th>Quantity Available</th>
					<th>Location</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="(item, index) in stockData" :key="index">
					<td>{{ item.item_code }}</td>
					<td>{{ item.item_name }}</td>
					<td>{{ item.stock_uom }}</td>
					<td>{{ item.stock_in_hand }}</td>
					<td>{{ item.location }}</td>
				</tr>
				<tr v-if="stockData.length === 0">
					<td colspan="5" class="text-center">No stock found.</td>
				</tr>
			</tbody>
		</table>
	</div>
</template>

<script setup>
import { ref } from "vue";
import axios from "axios";

const stockData = ref([]);
const filters = ref({
	itemCode: "",
	location: "",
});

const fetchStock = async () => {
	try {
		const response = await axios.get(
			"/api/method/posawesome.posawesome.api.lazer_pos.get_stock_in_hand_list",
			{
				params: {
					filters: JSON.stringify({
						item_code: filters.value.itemCode,
						location: filters.value.location,
					}),
				},
			},
		);
		stockData.value = response.data.message || [];
	} catch (error) {
		console.error("Error fetching stock:", error);
		alert("Failed to fetch stock data.");
	}
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
