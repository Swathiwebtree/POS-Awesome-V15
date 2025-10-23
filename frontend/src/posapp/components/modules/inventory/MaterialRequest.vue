<template>
	<div class="material-request">
		<h2>Material Requests</h2>

		<!-- Filters -->
		<div class="filters">
			<input
				type="text"
				v-model="filters.keyword"
				placeholder="Search by MR # or Title"
			/>
			<button @click="fetchMaterialRequests">Search</button>
			<button class="btn-new" @click="createMaterialRequest">+ New</button>
		</div>

		<!-- Material Request List -->
		<table>
			<thead>
				<tr>
					<th>MR #</th>
					<th>Material Request Type</th>
					<th>Schedule Date</th>
					<th>Status</th>
					<th>Title</th>
					<th>Per Ordered</th>
					<th>Per Received</th>
				</tr>
			</thead>
			<tbody>
				<tr
					v-for="(mr, index) in materialRequests"
					:key="index"
					@click="fetchMRDetails(mr[0])"
				>
					<td>{{ mr[0] }}</td>
					<td>{{ mr[11] }}</td>
					<td>{{ mr[12] }}</td>
					<td>{{ mr[14] }}</td>
					<td>{{ mr[15] }}</td>
					<td>{{ mr[16] }}%</td>
					<td>{{ mr[17] }}%</td>
				</tr>
				<tr v-if="materialRequests.length === 0">
					<td colspan="7" class="no-data">No Material Requests Found</td>
				</tr>
			</tbody>
		</table>

		<!-- Selected Material Request Details -->
		<div v-if="selectedMR" class="mr-details">
			<h3>Material Request Details: {{ selectedMR.name }}</h3>
			<p><strong>Title:</strong> {{ selectedMR.title }}</p>
			<p><strong>Status:</strong> {{ selectedMR.status }}</p>
			<p><strong>Request Type:</strong> {{ selectedMR.material_request_type }}</p>
			<p><strong>Schedule Date:</strong> {{ selectedMR.schedule_date }}</p>
			<p><strong>Warehouse:</strong> {{ selectedMR.set_warehouse || "-" }}</p>

			<h4>Item Details</h4>
			<table>
				<thead>
					<tr>
						<th>Item Code</th>
						<th>Item Name</th>
						<th>Description</th>
						<th>Qty</th>
						<th>UOM</th>
						<th>Rate</th>
						<th>Amount</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="(item, i) in selectedMR.items" :key="i">
						<td>{{ item.item_code }}</td>
						<td>{{ item.item_name }}</td>
						<td>{{ item.description }}</td>
						<td>{{ item.qty }}</td>
						<td>{{ item.uom }}</td>
						<td>{{ item.rate }}</td>
						<td>{{ item.amount }}</td>
					</tr>
					<tr v-if="!selectedMR.items || selectedMR.items.length === 0">
						<td colspan="7" class="no-data">No items found</td>
					</tr>
				</tbody>
			</table>

			<div class="additional-fields">
				<p><strong>Remarks:</strong> {{ selectedMR.remarks || "-" }}</p>
				<p>
					<strong>Created By:</strong> {{ selectedMR.owner }} on
					{{ formatDate(selectedMR.creation) }}
				</p>
				<p>
					<strong>Modified By:</strong> {{ selectedMR.modified_by }} on
					{{ formatDate(selectedMR.modified) }}
				</p>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import axios from "axios";

const materialRequests = ref([]);
const selectedMR = ref(null);
const filters = ref({
	keyword: "",
});

// Fetch Material Requests list
async function fetchMaterialRequests() {
	try {
		const res = await axios.get("/api/method/frappe.desk.reportview.get", {
			params: {
				doctype: "Material Request",
				limit_start: 0,
				limit_page_length: 20,
			},
		});
		materialRequests.value = res.data.message?.values || [];
		selectedMR.value = null;
	} catch (error) {
		console.error("Error fetching material requests:", error);
	}
}

// Fetch individual MR details
async function fetchMRDetails(name) {
	try {
		const res = await axios.get("/api/method/frappe.desk.form.load.getdoc", {
			params: { doctype: "Material Request", name },
		});
		selectedMR.value = res.data.docs ? res.data.docs[0] : null;
	} catch (error) {
		console.error("Error fetching MR details:", error);
	}
}

// Date formatter
function formatDate(dateStr) {
	if (!dateStr) return "-";
	const date = new Date(dateStr);
	return date.toLocaleString();
}

// Create new MR (ERP navigation)
function createMaterialRequest() {
	window.open("/app/material-request/new-material-request", "_blank");
}

onMounted(fetchMaterialRequests);
</script>

<style scoped>
.material-request {
	padding: 20px;
	font-family: Arial, sans-serif;
}

.filters {
	display: flex;
	gap: 10px;
	margin-bottom: 15px;
}

.filters input {
	padding: 6px;
	border: 1px solid #ccc;
	border-radius: 4px;
}

.filters button {
	padding: 6px 12px;
	border: none;
	background-color: #1976d2;
	color: white;
	cursor: pointer;
	border-radius: 4px;
}

.filters .btn-new {
	background-color: #43a047;
}

.filters button:hover {
	opacity: 0.9;
}

table {
	width: 100%;
	border-collapse: collapse;
	margin-bottom: 20px;
}

th,
td {
	border: 1px solid #ddd;
	padding: 8px;
	text-align: left;
}

th {
	background-color: #f7f7f7;
}

tr:hover {
	background-color: #f5f5f5;
	cursor: pointer;
}

.no-data {
	text-align: center;
	color: #888;
	font-style: italic;
}

.mr-details {
	background-color: #fafafa;
	padding: 15px;
	border: 1px solid #ddd;
	border-radius: 6px;
}

.mr-details h4 {
	margin-top: 20px;
}

.additional-fields p {
	margin: 4px 0;
}
</style>
