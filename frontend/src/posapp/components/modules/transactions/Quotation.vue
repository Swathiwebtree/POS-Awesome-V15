<template>
	<div class="quotation-module">
		<h3>Quotation Dashboard</h3>

		<!-- Filters -->
		<div class="filter-row">
			<label>Customer:</label>
			<input v-model="filters.customer" placeholder="Enter customer name" />
			<label>Status:</label>
			<select v-model="filters.status">
				<option value="">All</option>
				<option value="Draft">Draft</option>
				<option value="Submitted">Submitted</option>
				<option value="Cancelled">Cancelled</option>
			</select>
			<button @click="fetchQuotations">Search</button>
		</div>

		<!-- Quotation Table -->
		<table class="quotation-table">
			<thead>
				<tr>
					<th>Quotation #</th>
					<th>Customer</th>
					<th>Date</th>
					<th>Status</th>
					<th>Total</th>
					<th>Currency</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="(quot, index) in quotations" :key="index">
					<td>{{ quot.name }}</td>
					<td>{{ quot.customer }}</td>
					<td>{{ formatDate(quot.transaction_date) }}</td>
					<td>{{ quot.status }}</td>
					<td>{{ quot.grand_total }}</td>
					<td>{{ quot.currency }}</td>
				</tr>
				<tr v-if="quotations.length === 0">
					<td colspan="6" class="no-data">No quotations found</td>
				</tr>
			</tbody>
		</table>

		<!-- New Quotation Button -->
		<button class="btn-new" @click="createQuotation">+ New Quotation</button>
	</div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import axios from "axios";

const quotations = ref([]);
const filters = ref({
	customer: "",
	status: "",
});

// Fetch quotations from API
async function fetchQuotations() {
	try {
		const params = {};
		if (filters.value.customer) params.customer = filters.value.customer;
		if (filters.value.status) params.status = filters.value.status;

		const response = await axios.get(
			"/api/method/posawesome.posawesome.api.lazer_pos.get_quotation_list",
			{ params },
		);
		quotations.value = response.data.message || [];
	} catch (error) {
		console.error("Error fetching quotations:", error);
	}
}

// Format date
function formatDate(dateStr) {
	if (!dateStr) return "-";
	const date = new Date(dateStr);
	return date.toLocaleDateString();
}

// Add new quotation (redirect or open form)
function createQuotation() {
	alert("Open new quotation form");
}

onMounted(() => {
	fetchQuotations();
});
</script>

<style scoped>
.quotation-module {
	padding: 20px;
	font-family: Arial, sans-serif;
}

h3 {
	margin-bottom: 15px;
	color: #2c3e50;
}

.filter-row {
	display: flex;
	align-items: center;
	gap: 10px;
	margin-bottom: 15px;
}

.filter-row input,
.filter-row select {
	padding: 5px 8px;
	border: 1px solid #ccc;
	border-radius: 4px;
}

.filter-row button {
	padding: 6px 12px;
	background-color: #1976d2;
	color: white;
	border: none;
	cursor: pointer;
}

.filter-row button:hover {
	background-color: #1565c0;
}

.quotation-table {
	width: 100%;
	border-collapse: collapse;
	margin-bottom: 15px;
}

th,
td {
	border: 1px solid #ccc;
	padding: 6px 8px;
	text-align: left;
}

th {
	background-color: #f5f5f5;
}

.no-data {
	text-align: center;
	color: #888;
	font-style: italic;
}

.btn-new {
	padding: 8px 14px;
	background-color: #43a047;
	color: #fff;
	border: none;
	cursor: pointer;
	border-radius: 4px;
}

.btn-new:hover {
	background-color: #388e3c;
}
</style>
