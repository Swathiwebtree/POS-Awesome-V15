<template>
	<div>
		<h2 class="text-xl font-semibold mb-4">Damage Memo</h2>

		<div class="grid grid-cols-3 gap-2 mb-4">
			<input v-model="dmNumber" placeholder="DM #" class="input" />
			<input v-model="division" placeholder="Division" class="input" />
			<input v-model="location" placeholder="Location" class="input" />
			<input type="date" v-model="date" class="input" />
			<input v-model="stationId" placeholder="Station ID" class="input" />
			<input v-model="userId" placeholder="User ID" class="input" />
		</div>

		<table class="table-auto border w-full mb-4">
			<thead>
				<tr>
					<th>Barcode</th>
					<th>Item Code</th>
					<th>Item Name</th>
					<th>Qty</th>
					<th>Unit</th>
					<th>Reason</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="(item, index) in items" :key="index">
					<td><input v-model="item.barcode" class="input" /></td>
					<td><input v-model="item.code" class="input" /></td>
					<td><input v-model="item.name" class="input" /></td>
					<td><input v-model.number="item.qty" class="input" /></td>
					<td><input v-model="item.unit" class="input" /></td>
					<td><input v-model="item.reason" class="input" /></td>
				</tr>
			</tbody>
		</table>

		<button class="btn" @click="saveDamageMemo">Save Damage Memo</button>
	</div>
</template>

<script setup>
import { ref } from "vue";

const dmNumber = ref("");
const division = ref("");
const location = ref("");
const date = ref("");
const stationId = ref("");
const userId = ref("");

const items = ref([{ barcode: "", code: "", name: "", qty: 0, unit: "", reason: "" }]);

const saveDamageMemo = () => alert("Damage Memo Saved!");
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
