<template>
	<div class="vehicle-history">
		<h4>Vehicle History</h4>

		<!-- Vehicle & Customer Info -->
		<div class="info-row">
			<label>Vehicle #:</label>
			<input v-model="vehicleNo" placeholder="Enter vehicle number" />
			<button @click="fetchVehicleDetails">Search</button>
		</div>

		<div v-if="vehicleData">
			<div class="vehicle-info">
				<p><strong>Tel (Mob):</strong> {{ customerData.mobile_no || "-" }}</p>
				<p><strong>Make:</strong> {{ vehicleData.make || "-" }}</p>
				<p><strong>Model #:</strong> {{ vehicleData.model || "-" }}</p>
				<p><strong>Mileage Kms:</strong> {{ vehicleData.odometer || "-" }}</p>
				<p><strong>Customer:</strong> {{ customerData.customer_name || "-" }}</p>
				<p><strong>Cash Customer:</strong> {{ customerData.cash_customer ? "Yes" : "No" }}</p>
				<p><strong>Name:</strong> {{ customerData.name || "-" }}</p>
			</div>

			<!-- Vehicle History Table -->
			<h5>Transaction History</h5>
			<table>
				<thead>
					<tr>
						<th>Bill No</th>
						<th>Date</th>
						<th>Item Code</th>
						<th>Item Name</th>
						<th>Amount</th>
						<th>Points</th>
						<th>Lift Code</th>
						<th>Staff Name</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="(entry, index) in history" :key="index">
						<td>{{ entry.bill_no }}</td>
						<td>{{ entry.date }}</td>
						<td>{{ entry.item_code }}</td>
						<td>{{ entry.item_name }}</td>
						<td>{{ entry.amount }}</td>
						<td>{{ entry.points }}</td>
						<td>{{ entry.lift_code }}</td>
						<td>{{ entry.staff_name }}</td>
					</tr>
					<tr v-if="history.length === 0">
						<td colspan="8" class="no-data">No history found</td>
					</tr>
				</tbody>
			</table>
		</div>

		<div v-else>
			<p>Please enter a vehicle number and click search.</p>
		</div>
	</div>
</template>

<script setup>
import { ref } from "vue";
import axios from "axios";

const vehicleNo = ref("");
const vehicleData = ref(null);
const customerData = ref({});
const history = ref([]);

async function fetchVehicleDetails() {
	if (!vehicleNo.value) return alert("Please enter vehicle number.");

	try {
		const res = await axios.get("/api/method/posawesome.posawesome.api.lazer_pos.get_vehicle_details", {
			params: { vehicle_no: vehicleNo.value },
		});

		if (res.data.message) {
			vehicleData.value = res.data.message.vehicle || null;
			customerData.value = res.data.message.customer || {};
			history.value = res.data.message.history || [];
		} else {
			vehicleData.value = null;
			customerData.value = {};
			history.value = [];
			alert("Vehicle not found");
		}
	} catch (err) {
		console.error(err);
		alert("Error fetching vehicle details");
	}
}
</script>

<style scoped>
.vehicle-history {
	padding: 10px;
}
.info-row {
	display: flex;
	gap: 10px;
	margin-bottom: 15px;
	align-items: center;
}
.vehicle-info p {
	margin: 3px 0;
}
table {
	width: 100%;
	border-collapse: collapse;
	margin-top: 10px;
}
th,
td {
	border: 1px solid #ccc;
	padding: 5px;
	text-align: left;
}
.no-data {
	text-align: center;
	font-style: italic;
	color: #888;
}
button {
	padding: 4px 8px;
	cursor: pointer;
}
</style>
