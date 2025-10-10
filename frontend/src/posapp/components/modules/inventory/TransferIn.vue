<template>
	<div>
		<h2 class="text-xl font-semibold mb-4">Transfer In</h2>

		<!-- Filter/Search Fields -->
		<div class="grid grid-cols-4 gap-2 mb-4">
			<input type="date" v-model="fromDate" placeholder="From Date" class="input" />
			<input type="date" v-model="toDate" placeholder="To Date" class="input" />
			<input v-model="transferFrom" placeholder="Transfer From" class="input" />
			<input v-model="transferTo" placeholder="Transfer To" class="input" />
			<input v-model="stationId" placeholder="Station ID" class="input" />
			<button class="btn col-span-1" @click="fetchTransferInList">Search</button>
		</div>

		<!-- Main Fields -->
		<div class="grid grid-cols-4 gap-2 mb-4">
			<input v-model="transNumber" placeholder="Trans #" class="input" />
			<input v-model="tOutNumber" placeholder="T. Out #" class="input" />
			<input v-model="transferFromInput" placeholder="Transfer From" class="input" />
			<input v-model="stationIdInput" placeholder="Station ID" class="input" />
			<input type="date" v-model="date" class="input" />
			<input v-model="division" placeholder="Div" class="input" />
			<input v-model="transferToInput" placeholder="Transfer To" class="input" />
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
					<td><input v-model="item.item_code" class="input" /></td>
					<td><input v-model="item.item_name" class="input" /></td>
					<td><input v-model.number="item.balance" class="input" /></td>
					<td><input v-model.number="item.qty" class="input" /></td>
					<td><input v-model="item.unit" class="input" /></td>
					<td><input v-model="item.source_no" class="input" /></td>
				</tr>
			</tbody>
		</table>

		<button class="btn" @click="saveTransferIn">Save Transfer In</button>
	</div>
</template>

<script setup>
import { ref } from "vue";
import axios from "axios";

const fromDate = ref("");
const toDate = ref("");
const transferFrom = ref("");
const transferTo = ref("");
const stationId = ref("");

const transNumber = ref("");
const tOutNumber = ref("");
const transferFromInput = ref("");
const stationIdInput = ref("");
const date = ref("");
const division = ref("");
const transferToInput = ref("");
const userId = ref("");

const items = ref([]);

// Fetch Transfer In records from API
const fetchTransferInList = async () => {
	try {
		const response = await axios.get(
			"/api/method/posawesome.posawesome.api.lazer_pos.get_transfer_in_list",
			{
				params: {
					from_date: fromDate.value,
					to_date: toDate.value,
					transfer_from: transferFrom.value,
					transfer_to: transferTo.value,
					station_id: stationId.value,
				},
			},
		);

		if (response.data.message) {
			// If API returns list of transfer records
			if (response.data.message.length > 0) {
				const record = response.data.message[0];
				transNumber.value = record.trans_no;
				tOutNumber.value = record.t_out_no;
				transferFromInput.value = record.transfer_from;
				stationIdInput.value = record.station_id;
				date.value = record.date;
				division.value = record.div;
				transferToInput.value = record.transfer_to;
				userId.value = record.user_id;
				items.value = record.items.map((i) => ({
					barcode: i.barcode || "",
					item_code: i.item_code || "",
					item_name: i.item_name || "",
					balance: i.balance || 0,
					qty: i.qty || 0,
					unit: i.unit || "",
					source_no: i.source_no || "",
				}));
			}
		}
	} catch (error) {
		console.error("Error fetching Transfer In list:", error);
		alert("Failed to fetch Transfer In records.");
	}
};

const saveTransferIn = () => {
	alert("Transfer In Saved!");
};
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
	margin-top: 4px;
}
.btn:hover {
	background: #0056b3;
}
table {
	border-collapse: collapse;
	width: 100%;
	margin-bottom: 10px;
}
th,
td {
	border: 1px solid #ccc;
	padding: 4px;
	text-align: left;
}
</style>
