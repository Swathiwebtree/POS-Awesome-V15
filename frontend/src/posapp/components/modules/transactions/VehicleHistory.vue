<template>
	<div class="vehicle-history">
		<h4>Vehicle History</h4>

		<!-- Vehicle Search -->
		<div class="info-row">
			<label>Vehicle #:</label>
			<input v-model="vehicleNo" placeholder="Enter vehicle number" />
			<button @click="fetchVehicleHistory">Search</button>
		</div>

		<!-- Vehicle Info -->
		<div v-if="vehicleHistory">
			<div class="vehicle-info">
				<p><strong>Vehicle #:</strong> {{ vehicleHistory.vehicle_no || "-" }}</p>
				<p><strong>Make:</strong> {{ vehicleHistory.make || "-" }}</p>
				<p><strong>Model #:</strong> {{ vehicleHistory.model_no || "-" }}</p>
				<p><strong>Mileage Kms:</strong> {{ vehicleHistory.mileage_kms || "-" }}</p>
				<p><strong>Customer Name:</strong> {{ vehicleHistory.customer_name || "-" }}</p>
				<p><strong>Cash Customer:</strong> {{ vehicleHistory.cash_customer ? "Yes" : "No" }}</p>
			</div>

			<!-- Vehicle Transactions Table -->
			<h5>Transactions</h5>
			<table class="transactions-table">
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
					<tr v-for="(tx, index) in vehicleHistory.vehicle_transactions" :key="index">
						<td>{{ tx.bill_no }}</td>
						<td>{{ tx.date }}</td>
						<td>{{ tx.item_code }}</td>
						<td>{{ tx.item_name }}</td>
						<td>{{ tx.amount }}</td>
						<td>{{ tx.points }}</td>
						<td>{{ tx.lift_code }}</td>
						<td>{{ tx.staff_name }}</td>
					</tr>
				</tbody>
			</table>
		</div>

		<div v-else-if="searched">No vehicle history found.</div>
	</div>
</template>

<script>
import axios from "axios";

export default {
	data() {
		return {
			vehicleNo: "",
			vehicleHistory: null,
			searched: false,
		};
	},
	methods: {
		async fetchVehicleHistory() {
			if (!this.vehicleNo) return alert("Please enter a vehicle number");

			try {
				const response = await axios.get(`/api/method/frappe.client.get_list`, {
					params: {
						doctype: "Vehicle History",
						filters: { vehicle_no: this.vehicleNo },
						fields: [
							"vehicle_no",
							"make",
							"model_no",
							"mileage_kms",
							"customer_name",
							"cash_customer",
							"vehicle_transactions",
						],
						limit_page_length: 1,
					},
				});

				if (response.data.message && response.data.message.length) {
					this.vehicleHistory = response.data.message[0];
				} else {
					this.vehicleHistory = null;
				}
				this.searched = true;
			} catch (error) {
				console.error("Error fetching vehicle history:", error);
			}
		},
	},
};
</script>

<style>
.vehicle-history {
	padding: 1rem;
}
.info-row {
	display: flex;
	align-items: center;
	gap: 0.5rem;
	margin-bottom: 1rem;
}
.vehicle-info p {
	margin: 0.25rem 0;
}
.transactions-table {
	width: 100%;
	border-collapse: collapse;
	margin-top: 1rem;
}
.transactions-table th,
.transactions-table td {
	border: 1px solid #ccc;
	padding: 0.5rem;
	text-align: left;
}
</style>
