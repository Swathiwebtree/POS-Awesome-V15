<template>
	<div>
		<h2 class="text-xl font-semibold mb-4">Transfer Out</h2>

		<div class="grid grid-cols-3 gap-2 mb-4">
			<input v-model="transNumber" placeholder="Trans #" class="input" />
			<input v-model="transferTo" placeholder="Transfer To" class="input" />
			<input v-model="stationId" placeholder="Station ID" class="input" />
			<input type="date" v-model="date" class="input" />
			<input v-model="division" placeholder="Division" class="input" />
			<input v-model="transferFrom" placeholder="Transfer From" class="input" />
			<input v-model="userId" placeholder="User ID" class="input" />
		</div>

		<!-- Stock Items Table -->
		<table class="table-auto border w-full mb-4">
			<thead>
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
				<tr v-for="(item, index) in items" :key="index">
					<td><input v-model="item.barcode" class="input" /></td>
					<td><input v-model="item.code" class="input" /></td>
					<td><input v-model="item.name" class="input" /></td>
					<td><input v-model.number="item.balance" class="input" /></td>
					<td><input v-model.number="item.qty" class="input" /></td>
					<td><input v-model="item.unit" class="input" /></td>
					<td><input v-model="item.source" class="input" /></td>
				</tr>
			</tbody>
		</table>

		<button class="btn" @click="saveTransferOut">Save Transfer Out</button>
	</div>
</template>

<script setup>
import { ref } from "vue";

const transNumber = ref("");
const transferTo = ref("");
const stationId = ref("");
const date = ref("");
const division = ref("");
const transferFrom = ref("");
const userId = ref("");

const items = ref([{ barcode: "", code: "", name: "", balance: 0, qty: 0, unit: "", source: "" }]);

const saveTransferOut = () => alert("Transfer Out Saved!");
</script>

<style scoped>
.input {
	border: 1px solid #ccc;
	padding: 4px;
	width: 100%;
	margin-bottom: 4px;
}
.btn {
	background: #007bff;
	color: white;
	padding: 6px 12px;
	cursor: pointer;
}
.btn:hover {
	background: #0056b3;
}
</style>
