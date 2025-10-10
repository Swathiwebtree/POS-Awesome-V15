<template>
	<div class="receipt-voucher">
		<h4>Receipt Voucher</h4>
		<div class="info-row">
			<label>Voucher #:</label> <input v-model="voucherNo" /> <label>Date:</label>
			<input type="date" v-model="date" /> <label>Customer:</label> <input v-model="customer" />
		</div>

		<table>
			<thead>
				<tr>
					<th>Item/Account</th>
					<th>Amount</th>
					<th>Remarks</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="(entry, index) in entries" :key="index">
					<td>{{ entry.item }}</td>
					<td>{{ entry.amount }}</td>
					<td>{{ entry.remarks }}</td>
				</tr>
			</tbody>
		</table>

		<button @click="finalizeVoucher">Finalize Voucher</button>
	</div>
</template>

<script setup>
import { ref } from "vue";
const voucherNo = ref("");
const date = ref("");
const customer = ref("");
const entries = ref([]);

function finalizeVoucher() {
	alert("Voucher Finalized");
}
</script>

<style scoped>
.receipt-voucher {
	padding: 10px;
}
.info-row {
	display: flex;
	gap: 10px;
	margin-bottom: 10px;
}
table {
	width: 100%;
	border-collapse: collapse;
	margin-bottom: 10px;
}
th,
td {
	border: 1px solid #ccc;
	padding: 4px;
}
</style>
