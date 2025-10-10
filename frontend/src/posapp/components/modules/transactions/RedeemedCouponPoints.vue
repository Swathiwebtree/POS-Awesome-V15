<template>
	<div class="coupon-sales-points">
		<h4>Coupon Sales Point</h4>

		<!-- Filters -->
		<div class="filters">
			<label>Lift Employee:</label>
			<input v-model="liftEmployee" placeholder="Staff Code" />
			<label>From (Date):</label>
			<input type="date" v-model="fromDate" />
			<label>To (Date):</label>
			<input type="date" v-model="toDate" />
			<button @click="fetchCouponPoints">Search</button>
		</div>

		<!-- Table -->
		<table>
			<thead>
				<tr>
					<th>Staff Code</th>
					<th>Staff Name</th>
					<th>Date</th>
					<th>Points</th>
					<th>Terminal</th>
					<th>Vehicle #</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="(entry, index) in redeemed" :key="index">
					<td>{{ entry.staff_code }}</td>
					<td>{{ entry.staff_name }}</td>
					<td>{{ entry.date }}</td>
					<td>{{ entry.points }}</td>
					<td>{{ entry.terminal }}</td>
					<td>{{ entry.vehicle_no }}</td>
				</tr>
				<tr v-if="redeemed.length === 0">
					<td colspan="6" class="no-data">No records found</td>
				</tr>
			</tbody>
		</table>
	</div>
</template>

<script setup>
import { ref } from "vue";
import axios from "axios";

const liftEmployee = ref("");
const fromDate = ref("");
const toDate = ref("");
const redeemed = ref([]);

async function fetchCouponPoints() {
	try {
		const res = await axios.get(
			"/api/method/posawesome.posawesome.api.lazer_pos.get_coupon_sales_point_list",
			{
				params: {
					lift_employee: liftEmployee.value,
					from_date: fromDate.value,
					to_date: toDate.value,
				},
			},
		);
		redeemed.value = res.data.message || [];
	} catch (err) {
		console.error(err);
		alert("Error fetching coupon sales points");
	}
}
</script>

<style scoped>
.coupon-sales-points {
	padding: 10px;
}
.filters {
	display: flex;
	gap: 10px;
	margin-bottom: 10px;
	align-items: center;
	flex-wrap: wrap;
}
input {
	padding: 4px;
}
button {
	padding: 4px 8px;
	cursor: pointer;
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
</style>
