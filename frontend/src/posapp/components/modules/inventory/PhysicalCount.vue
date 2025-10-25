<template>
	<div class="physical-count-container p-4">
		<h2 class="text-xl font-semibold mb-4">Physical Count</h2>

		<!-- Header Fields -->
		<div class="grid grid-cols-3 gap-4 mb-4">
			<input v-model="physicalCount.phy_no" placeholder="Phy #" class="input" />
			<input v-model="physicalCount.date" type="date" class="input" />
			<input v-model="physicalCount.station_id" placeholder="Station ID" class="input" />
			<input v-model="physicalCount.location" placeholder="Location" class="input" />
			<input v-model="physicalCount.shift_closing_id" placeholder="Shift Closing ID" class="input" />
			<input v-model="physicalCount.user_id" placeholder="User ID" class="input" />
		</div>

		<!-- Items Table -->
		<table class="w-full table-auto border">
			<thead>
				<tr class="bg-gray-200">
					<th class="border px-2 py-1">Barcode</th>
					<th class="border px-2 py-1">Item Code</th>
					<th class="border px-2 py-1">Item Name</th>
					<th class="border px-2 py-1">Unit</th>
					<th class="border px-2 py-1">Factor</th>
					<th class="border px-2 py-1">Quantity</th>
					<th class="border px-2 py-1">Net Quantity</th>
					<th class="border px-2 py-1">Actions</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="(item, index) in physicalCount.items" :key="index">
					<td class="border px-2 py-1"><input v-model="item.barcode" class="input" /></td>
					<td class="border px-2 py-1"><input v-model="item.item_code" class="input" /></td>
					<td class="border px-2 py-1"><input v-model="item.item_name" class="input" /></td>
					<td class="border px-2 py-1"><input v-model="item.unit" class="input" /></td>
					<td class="border px-2 py-1">
						<input v-model.number="item.factor" type="number" class="input" />
					</td>
					<td class="border px-2 py-1">
						<input v-model.number="item.quantity" type="number" class="input" />
					</td>
					<td class="border px-2 py-1">
						<input v-model.number="item.net_quantity" type="number" class="input" />
					</td>
					<td class="border px-2 py-1">
						<button @click="removeItem(index)" class="btn btn-red">Delete</button>
					</td>
				</tr>
			</tbody>
		</table>

		<div class="mt-2">
			<button @click="addItem" class="btn btn-blue mr-2">Add Item</button>
			<button @click="savePhysicalCount" class="btn btn-green">Save Physical Count</button>
		</div>
	</div>
</template>

<script setup>
import { ref } from "vue";

// Reactive object for Physical Count
const physicalCount = ref({
	phy_no: "",
	date: "",
	station_id: "",
	location: "",
	shift_closing_id: "",
	user_id: "",
	items: [],
});

// Add new empty row
function addItem() {
	physicalCount.value.items.push({
		barcode: "",
		item_code: "",
		item_name: "",
		unit: "",
		factor: 1,
		quantity: 0,
		net_quantity: 0,
	});
}

// Remove row
function removeItem(index) {
	physicalCount.value.items.splice(index, 1);
}

// Save to Frappe backend using frappe.call
function savePhysicalCount() {
	frappe.call({
		method: "frappe.client.insert",
		args: {
			doc: {
				doctype: "Physical Count",
				...physicalCount.value,
			},
		},
		callback: (r) => {
			if (r.message) {
				alert("Physical Count saved successfully!");
				// Reset form
				physicalCount.value = {
					phy_no: "",
					date: "",
					station_id: "",
					location: "",
					shift_closing_id: "",
					user_id: "",
					items: [],
				};
			}
		},
		error: (err) => {
			console.error(err);
			alert("Error saving Physical Count");
		},
	});
}
</script>

<style scoped>
.input {
	border: 1px solid #ccc;
	padding: 4px 6px;
	width: 100%;
	box-sizing: border-box;
}
.btn {
	padding: 6px 12px;
	border-radius: 4px;
	cursor: pointer;
}
.btn-blue {
	background: #3b82f6;
	color: white;
}
.btn-green {
	background: #10b981;
	color: white;
}
.btn-red {
	background: #ef4444;
	color: white;
}
</style>
