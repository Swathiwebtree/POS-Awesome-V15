<template>
	<div class="grn-dashboard">
		<h2 class="title">Goods Receipt Notes (GRN)</h2>

		<!-- Filters -->
		<div class="filters mb-4">
			<input type="date" v-model="startDate" class="input" placeholder="From Date" />
			<input type="date" v-model="endDate" class="input" placeholder="To Date" />
			<input v-model="supplier" class="input" placeholder="Supplier" />
			<input v-model="searchText" class="input" placeholder="Search GRN #" />
			<button class="btn" @click="fetchGRNs">Search</button>
		</div>

		<!-- GRN Table -->
		<table class="table">
			<thead>
				<tr>
					<th>GRN #</th>
					<th>Owner</th>
					<th>Created On</th>
					<th>Modified On</th>
					<th>Modified By</th>
					<th>Status</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="(grn, index) in grnList" :key="index" @click="selectGRN(grn)" class="row">
					<td>{{ grn.name }}</td>
					<td>{{ grn.owner }}</td>
					<td>{{ formatDate(grn.creation) }}</td>
					<td>{{ formatDate(grn.modified) }}</td>
					<td>{{ grn.modified_by }}</td>
					<td>{{ grn.docstatus === 0 ? "Draft" : "Submitted" }}</td>
				</tr>
				<tr v-if="!grnList.length">
					<td colspan="6" class="text-center">No GRNs found.</td>
				</tr>
			</tbody>
		</table>

		<!-- Selected GRN Details -->
		<div v-if="selectedGRN" class="grn-details">
			<h3>GRN Details: {{ selectedGRN.name }}</h3>
			<ul>
				<li><strong>Owner:</strong> {{ selectedGRN.owner }}</li>
				<li><strong>Created On:</strong> {{ formatDate(selectedGRN.creation) }}</li>
				<li><strong>Modified By:</strong> {{ selectedGRN.modified_by }}</li>
				<li><strong>Status:</strong> {{ selectedGRN.docstatus === 0 ? "Draft" : "Submitted" }}</li>
				<li><strong>Supplier:</strong> {{ selectedGRN.supplier || "-" }}</li>
				<li><strong>Location:</strong> {{ selectedGRN.location || "-" }}</li>
				<li><strong>Date:</strong> {{ selectedGRN.date || "-" }}</li>
				<li><strong>GRN #:</strong> {{ selectedGRN.grn_no || "-" }}</li>
			</ul>
		</div>
	</div>
</template>

<script setup>
import { ref } from "vue";
import axios from "axios";

// State variables
const startDate = ref("");
const endDate = ref("");
const supplier = ref("");
const searchText = ref("");
const grnList = ref([]);
const selectedGRN = ref(null);

// Fetch GRNs from ERPNext
const fetchGRNs = async () => {
	try {
		// Build filters array
		const filters = [];
		if (startDate.value) filters.push(["creation", ">=", startDate.value]);
		if (endDate.value) filters.push(["creation", "<=", endDate.value]);
		if (supplier.value) filters.push(["supplier", "like", `%${supplier.value}%`]);
		if (searchText.value) filters.push(["name", "like", `%${searchText.value}%`]);

		const res = await axios.get("/api/method/frappe.desk.reportview.get", {
			params: {
				doctype: "Goods Receipt Note",
				fields: JSON.stringify([
					"name",
					"owner",
					"creation",
					"modified",
					"modified_by",
					"docstatus",
					"supplier",
					"location",
					"date",
					"grn_no",
				]),
				filters: JSON.stringify(filters),
				order_by: "creation desc",
				limit_start: 0,
				limit_page_length: 50,
			},
		});

		const { keys, values } = res.data.message || { keys: [], values: [] };

		grnList.value = values.map((row) => {
			const obj = {};
			keys.forEach((key, i) => (obj[key] = row[i]));
			return obj;
		});

		selectedGRN.value = null;
	} catch (err) {
		console.error("Error fetching GRNs:", err);
	}
};

// Select GRN for details view
const selectGRN = (grn) => {
	selectedGRN.value = grn;
};

// Format date nicely
const formatDate = (dateStr) => {
	if (!dateStr) return "-";
	return new Date(dateStr).toLocaleString();
};

// Fetch initial list on mount
fetchGRNs();
</script>

<style scoped>
.grn-dashboard {
	padding: 20px;
	font-family: Arial, sans-serif;
}

.title {
	margin-bottom: 15px;
}

.filters {
	display: flex;
	flex-wrap: wrap;
	gap: 10px;
	margin-bottom: 15px;
}

.input {
	padding: 6px 10px;
	border: 1px solid #ccc;
	border-radius: 4px;
}

.btn {
	background-color: #007bff;
	color: white;
	border: none;
	padding: 6px 14px;
	border-radius: 4px;
	cursor: pointer;
}

.btn:hover {
	background-color: #0056b3;
}

.table {
	width: 100%;
	border-collapse: collapse;
}

th,
td {
	border: 1px solid #ddd;
	padding: 8px;
	text-align: left;
}

th {
	background-color: #f2f2f2;
}

.row:hover {
	background-color: #eef6ff;
	cursor: pointer;
}

.grn-details {
	margin-top: 20px;
	padding: 10px;
	border: 1px solid #ccc;
	background: #fafafa;
	border-radius: 6px;
}

.text-center {
	text-align: center;
}
</style>
