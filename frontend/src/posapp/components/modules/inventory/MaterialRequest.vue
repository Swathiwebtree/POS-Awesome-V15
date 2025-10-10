<template>
	<div class="material-request">
		<h2>Material Requests</h2>

		<!-- Filters -->
		<div class="filters">
			<input type="date" v-model="startDate" placeholder="From Date" />
			<input type="date" v-model="endDate" placeholder="To Date" />
			<input v-model="supplier" placeholder="Supplier" />
			<input v-model="division" placeholder="Division" />
			<button @click="fetchMaterialRequests">Search</button>
		</div>

		<!-- Material Request List -->
		<table>
			<thead>
				<tr>
					<th>MR #</th>
					<th>Date</th>
					<th>Requested By</th>
					<th>Division</th>
					<th>Sales Rep</th>
					<th>Supplier</th>
					<th>Station ID</th>
					<th>Location</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="mr in materialRequests" :key="mr.mr_no" @click="selectMR(mr)">
					<td>{{ mr.mr_no }}</td>
					<td>{{ mr.date }}</td>
					<td>{{ mr.requested_by }}</td>
					<td>{{ mr.division }}</td>
					<td>{{ mr.sales_rep }}</td>
					<td>{{ mr.supplier }}</td>
					<td>{{ mr.station_id }}</td>
					<td>{{ mr.location }}</td>
				</tr>
			</tbody>
		</table>

		<!-- Selected Material Request Details -->
		<div v-if="selectedMR" class="mr-details">
			<h3>MR Details: {{ selectedMR.mr_no }}</h3>

			<table>
				<thead>
					<tr>
						<th>Barcode</th>
						<th>Item Code</th>
						<th>Item Name</th>
						<th>Description</th>
						<th>Qty</th>
						<th>Unit</th>
						<th>Factor</th>
						<th>Qty Total</th>
						<th>Price</th>
						<th>Amount</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="(item, index) in selectedMR.items" :key="index">
						<td>{{ item.barcode }}</td>
						<td>{{ item.item_code }}</td>
						<td>{{ item.item_name }}</td>
						<td>{{ item.description }}</td>
						<td>{{ item.qty }}</td>
						<td>{{ item.unit }}</td>
						<td>{{ item.factor }}</td>
						<td>{{ item.qty * item.factor }}</td>
						<td>{{ item.price }}</td>
						<td>{{ item.amount }}</td>
					</tr>
				</tbody>
			</table>

			<div class="additional-fields">
				<p><strong>Remarks:</strong> {{ selectedMR.remarks || "-" }}</p>
				<p>
					<strong>Created By:</strong> {{ selectedMR.created_by || "-" }} on
					{{ selectedMR.created_on || "-" }}
				</p>
				<p>
					<strong>Modified By:</strong> {{ selectedMR.modified_by || "-" }} on
					{{ selectedMR.modified_on || "-" }}
				</p>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref } from "vue";
import axios from "axios";

const startDate = ref("");
const endDate = ref("");
const supplier = ref("");
const division = ref("");

const materialRequests = ref([]);
const selectedMR = ref(null);

const fetchMaterialRequests = async () => {
	try {
		const res = await axios.get(
			"/api/method/posawesome.posawesome.api.lazer_pos.get_material_request_list",
			{
				params: {
					start_date: startDate.value,
					end_date: endDate.value,
					supplier: supplier.value,
					division: division.value,
				},
			},
		);
		materialRequests.value = res.data.message || [];
		selectedMR.value = null;
	} catch (err) {
		console.error(err);
	}
};

const selectMR = (mr) => {
	selectedMR.value = mr;
};
</script>

<style scoped>
.material-request {
	padding: 10px;
}
.filters {
	display: flex;
	gap: 10px;
	margin-bottom: 10px;
}
table {
	width: 100%;
	border-collapse: collapse;
	margin-bottom: 20px;
}
th,
td {
	border: 1px solid #ccc;
	padding: 5px;
	text-align: left;
}
tr:hover {
	background-color: #f5f5f5;
	cursor: pointer;
}
.mr-details {
	margin-top: 20px;
	padding: 10px;
	border: 1px solid #ddd;
	background: #fafafa;
}
.additional-fields p {
	margin: 2px 0;
}
</style>
