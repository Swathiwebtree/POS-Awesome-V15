<template>
	<div class="sales-payment">
		<h4>Sales by Payment</h4>
		<table>
			<thead>
				<tr>
					<th>Type</th>
					<th>Total</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="(row, idx) in salesData" :key="idx">
					<td>{{ row.type }}</td>
					<td>{{ row.total }}</td>
				</tr>
			</tbody>
		</table>

		<div>
			<p>Sales Amount: {{ salesAmount }}</p>
			<p>Others: {{ others }}</p>
			<p>Total: {{ total }}</p>
		</div>
	</div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import axios from "axios";

const salesData = ref([]);
const salesAmount = ref(0);
const others = ref(0);
const total = ref(0);

async function fetchSales() {
	try {
		const res = await axios.get(
			"/api/method/posawesome.posawesome.api.lazer_pos.get_sales_by_payment_list",
		);
		salesData.value = res.data.message || [];
		salesAmount.value = res.data.sales_amount || 0;
		others.value = res.data.others || 0;
		total.value = res.data.total || 0;
	} catch (err) {
		console.error(err);
	}
}

onMounted(fetchSales);
</script>

<style scoped>
table {
	width: 100%;
	border-collapse: collapse;
	margin-bottom: 10px;
}
th,
td {
	border: 1px solid #ccc;
	padding: 5px;
}
</style>
