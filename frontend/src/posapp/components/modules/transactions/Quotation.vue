<template>
	<div class="quotation-module">
		<h2>Quotation Dashboard</h2>

		<!-- Search Section -->
		<div class="filter-row">
			<label>Quotation #:</label>
			<input v-model="filters.name" placeholder="Enter Quotation ID" />
			<button @click="fetchQuotation">Search</button>
			<button class="btn-new" @click="createQuotation">+ New Quotation</button>
		</div>

		<!-- Quotation Details -->
		<div v-if="quotation" class="quotation-details">
			<h3>Quotation Details ({{ quotation.name }})</h3>

			<div class="details-grid">
				<div><b>Date:</b> {{ quotation.transaction_date }}</div>
				<div><b>Ref:</b> {{ quotation.reference }}</div>
				<div><b>Div:</b> {{ quotation.division || "-" }}</div>
				<div><b>Client:</b> {{ quotation.customer_name }}</div>
				<div><b>Tel No:</b> {{ quotation.phone_no }}</div>
				<div><b>Address 1:</b> {{ quotation.address_line1 }}</div>
				<div><b>Address 2:</b> {{ quotation.address_line2 }}</div>
				<div><b>Address 3:</b> {{ quotation.address_line3 }}</div>
				<div><b>Attn:</b> {{ quotation.attention }}</div>
				<div><b>Sales Rep:</b> {{ quotation.sales_rep_name }}</div>
				<div><b>Fax No:</b> {{ quotation.fax_no }}</div>
				<div><b>Subject:</b> {{ quotation.subject }}</div>
				<div><b>Email Addr:</b> {{ quotation.email }}</div>
				<div><b>Type:</b> {{ quotation.quotation_type }}</div>
				<div><b>Station ID:</b> {{ quotation.station_id }}</div>
				<div><b>Price Level:</b> {{ quotation.price_level }}</div>
				<div><b>Location:</b> {{ quotation.location }}</div>
			</div>

			<!-- Items Table -->
			<h4>Item Details</h4>
			<table class="items-table">
				<thead>
					<tr>
						<th>Barcode</th>
						<th>Item Code</th>
						<th>Item Name</th>
						<th>Description</th>
						<th>Qty</th>
						<th>Unit</th>
						<th>Factor</th>
						<th>Qty 2</th>
						<th>Price</th>
						<th>Amount</th>
						<th>Price Src</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="(item, i) in quotation.items" :key="i">
						<td>{{ item.barcode || "-" }}</td>
						<td>{{ item.item_code }}</td>
						<td>{{ item.item_name }}</td>
						<td>{{ item.description }}</td>
						<td>{{ item.qty }}</td>
						<td>{{ item.uom }}</td>
						<td>{{ item.conversion_factor }}</td>
						<td>{{ item.qty }}</td>
						<td>{{ item.rate }}</td>
						<td>{{ item.amount }}</td>
						<td>{{ item.price_list_rate }}</td>
					</tr>
				</tbody>
			</table>

			<!-- Summary -->
			<h4>Summary</h4>
			<div class="summary-grid">
				<div><b>Payment:</b> {{ quotation.payment_terms_template || "-" }}</div>
				<div><b>Validity:</b> {{ quotation.valid_till || "-" }}</div>
				<div><b>Total:</b> {{ quotation.total || 0 }}</div>
				<div><b>Delivery:</b> {{ quotation.delivery_date || "-" }}</div>
				<div><b>Discount:</b> {{ quotation.discount_amount || 0 }}</div>
				<div><b>Net:</b> {{ quotation.grand_total || 0 }}</div>
				<div><b>Remarks:</b> {{ quotation.remarks || "-" }}</div>
				<div><b>Created By:</b> {{ quotation.owner }}</div>
				<div><b>Created On:</b> {{ quotation.creation }}</div>
				<div><b>Last Modified:</b> {{ quotation.modified }}</div>
			</div>
		</div>

		<!-- No Data -->
		<div v-else class="no-data">No quotation data found. Please search using a valid Quotation #.</div>
	</div>
</template>

<script setup>
import { ref } from "vue";
import axios from "axios";

const quotation = ref(null);
const filters = ref({ name: "" });

// Fetch quotation data from ERPNext API
async function fetchQuotation() {
	if (!filters.value.name) {
		alert("Please enter a Quotation number (e.g., SAL-QTN-2025-00001)");
		return;
	}
	try {
		const res = await axios.get("/api/method/frappe.desk.form.load.getdoc", {
			params: {
				doctype: "Quotation",
				name: filters.value.name,
			},
		});
		quotation.value = res.data.docs?.[0] || null;
	} catch (err) {
		console.error("Error fetching quotation:", err);
		alert("Failed to fetch quotation details.");
	}
}

// Open new quotation form in ERP
function createQuotation() {
	window.open("/app/quotation/new-quotation", "_blank");
}
</script>

<style scoped>
.quotation-module {
	padding: 20px;
	font-family: Arial, sans-serif;
}

h2 {
	margin-bottom: 20px;
	color: #2c3e50;
}

.filter-row {
	display: flex;
	align-items: center;
	gap: 10px;
	margin-bottom: 20px;
}

.filter-row input {
	padding: 6px 10px;
	border: 1px solid #ccc;
	border-radius: 4px;
}

.filter-row button {
	padding: 6px 12px;
	background-color: #1976d2;
	color: white;
	border: none;
	border-radius: 4px;
	cursor: pointer;
}

.filter-row button:hover {
	background-color: #125aa5;
}

.btn-new {
	margin-left: auto;
	background-color: #43a047;
}

.btn-new:hover {
	background-color: #388e3c;
}

.quotation-details {
	border: 1px solid #ddd;
	padding: 15px;
	border-radius: 8px;
	background-color: #fafafa;
}

.details-grid,
.summary-grid {
	display: grid;
	grid-template-columns: repeat(2, 1fr);
	gap: 8px;
	margin-bottom: 20px;
	font-size: 14px;
}

.items-table {
	width: 100%;
	border-collapse: collapse;
	margin-top: 10px;
	margin-bottom: 20px;
	font-size: 13px;
}

.items-table th,
.items-table td {
	border: 1px solid #ccc;
	padding: 6px;
	text-align: left;
}

.items-table th {
	background-color: #f5f5f5;
}

.no-data {
	margin-top: 20px;
	color: #777;
	font-style: italic;
	text-align: center;
}
</style>
