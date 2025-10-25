<template>
	<div class="p-6">
		<h2 class="text-2xl font-semibold mb-4 text-gray-800">Transfer In</h2>

		<!-- Filters -->
		<div class="grid grid-cols-5 gap-3 mb-6">
			<input v-model="filters.startDate" type="date" class="input" />
			<input v-model="filters.endDate" type="date" class="input" />
			<input v-model="filters.transferFrom" class="input" placeholder="Transfer From" />
			<input v-model="filters.transferTo" class="input" placeholder="Transfer To" />
			<button @click="fetchTransfers" class="btn">Fetch</button>
		</div>

		<!-- Transfer In Table -->
		<div v-if="transfers.length" class="overflow-x-auto mb-8 border rounded-lg shadow-sm">
			<table class="min-w-full text-sm">
				<thead class="bg-gray-100">
					<tr>
						<th>Trans #</th>
						<th>T. Out #</th>
						<th>Transfer From</th>
						<th>Station ID</th>
						<th>Date</th>
						<th>Div</th>
						<th>Transfer To</th>
						<th>User ID</th>
					</tr>
				</thead>
				<tbody>
					<tr
						v-for="transfer in transfers"
						:key="transfer.name"
						@click="selectTransfer(transfer)"
						class="hover:bg-gray-50 cursor-pointer"
					>
						<td>{{ transfer.trans_no }}</td>
						<td>{{ transfer.t_out_no }}</td>
						<td>{{ transfer.transfer_from }}</td>
						<td>{{ transfer.station_id }}</td>
						<td>{{ formatDate(transfer.date) }}</td>
						<td>{{ transfer.div }}</td>
						<td>{{ transfer.transfer_to }}</td>
						<td>{{ transfer.user_id }}</td>
					</tr>
				</tbody>
			</table>
		</div>

		<p v-else class="text-gray-500 text-sm italic">No Transfer In records found.</p>

		<!-- Selected Transfer Details -->
		<div v-if="selectedTransfer" class="mt-8">
			<h3 class="text-lg font-semibold mb-3 text-gray-700">
				Transfer Details — {{ selectedTransfer.trans_no }}
			</h3>
			<div class="grid grid-cols-3 gap-2 mb-4 text-sm text-gray-700">
				<p><b>Transfer From:</b> {{ selectedTransfer.transfer_from }}</p>
				<p><b>Transfer To:</b> {{ selectedTransfer.transfer_to }}</p>
				<p><b>Date:</b> {{ formatDate(selectedTransfer.date) }}</p>
				<p><b>Div:</b> {{ selectedTransfer.div }}</p>
				<p><b>Station ID:</b> {{ selectedTransfer.station_id }}</p>
				<p><b>User ID:</b> {{ selectedTransfer.user_id }}</p>
				<p><b>T. Out #:</b> {{ selectedTransfer.t_out_no }}</p>
			</div>

			<h4 class="text-md font-semibold mb-2">Item Details</h4>
			<div class="overflow-x-auto border rounded-lg">
				<table class="min-w-full text-sm">
					<thead class="bg-gray-100">
						<tr>
							<th>Barcode</th>
							<th>Item Code</th>
							<th>Item Name</th>
							<th>Balance</th>
							<th>Qty</th>
							<th>Unit</th>
							<th>Source #</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="(item, idx) in selectedTransfer.items" :key="idx">
							<td>{{ item.barcode }}</td>
							<td>{{ item.item_code }}</td>
							<td>{{ item.item_name }}</td>
							<td>{{ item.balance }}</td>
							<td>{{ item.qty }}</td>
							<td>{{ item.unit }}</td>
							<td>{{ item.source_no }}</td>
						</tr>
					</tbody>
				</table>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref } from "vue";
import axios from "axios";

const filters = ref({
	startDate: "",
	endDate: "",
	transferFrom: "",
	transferTo: "",
});

const transfers = ref([]);
const selectedTransfer = ref(null);

// Include cookies automatically
axios.defaults.withCredentials = true;

// Add CSRF token if embedded in Frappe page
axios.interceptors.request.use((config) => {
	const csrfToken = frappe.csrf_token;
	if (csrfToken) config.headers["X-Frappe-CSRF-Token"] = csrfToken;
	return config;
});

// Fetch Transfer In records
const fetchTransfers = async () => {
	try {
		const filtersObj = {};
		if (filters.value.transferFrom) filtersObj.transfer_from = filters.value.transferFrom;
		if (filters.value.transferTo) filtersObj.transfer_to = filters.value.transferTo;
		if (filters.value.startDate && filters.value.endDate)
			filtersObj.date = ["between", [filters.value.startDate, filters.value.endDate]];

		const res = await axios.get("/api/resource/Transfer In", {
			params: {
				fields: JSON.stringify([
					"name",
					"trans_no",
					"t_out_no",
					"transfer_from",
					"station_id",
					"date",
					"div",
					"transfer_to",
					"user_id",
				]),
				filters: JSON.stringify(filtersObj),
				limit_page_length: 50,
				order_by: "modified desc",
			},
		});

		transfers.value = res.data.data || [];
		selectedTransfer.value = null;
	} catch (err) {
		console.error("Error fetching Transfer In records:", err);
	}
};

// Fetch single Transfer with child items
const selectTransfer = async (transfer) => {
	try {
		const res = await axios.get(`/api/resource/Transfer In/${transfer.name}`);
		selectedTransfer.value = res.data.data;
	} catch (err) {
		console.error("Error fetching Transfer In details:", err);
	}
};

// Format date for display
const formatDate = (date) => {
	if (!date) return "";
	return new Date(date).toLocaleDateString();
};
</script>

<style scoped>
.input {
	border: 1px solid #ccc;
	padding: 6px 8px;
	width: 100%;
	border-radius: 4px;
}
.btn {
	background-color: #007bff;
	color: #fff;
	padding: 6px 12px;
	border-radius: 4px;
	cursor: pointer;
	font-weight: 500;
}
.btn:hover {
	background-color: #0056b3;
}
table {
	width: 100%;
	border-collapse: collapse;
}
th,
td {
	border: 1px solid #ccc;
	padding: 6px 8px;
	text-align: left;
}
th {
	font-weight: 600;
}
</style>
