<template>
	<div class="petty-cash">
		<h4>Petty Cash</h4>

		<!-- Add Petty Cash Form -->
		<div class="add-form">
			<h5>Add New Petty Cash</h5>
			<input v-model="newEntry.ref" placeholder="Reference" />
			<input v-model="newEntry.station_id" placeholder="Station ID" />
			<input v-model="newEntry.date" type="date" placeholder="Date" />
			<input v-model="newEntry.description" placeholder="Description" />
			<input v-model="newEntry.user_id" placeholder="User ID" />

			<h6>Items</h6>
			<div v-for="(item, idx) in newItems" :key="idx" class="item-row">
				<input v-model="item.ac_code" placeholder="A/C Code" />
				<input v-model="item.account_name" placeholder="Account Name" />
				<input v-model="item.description" placeholder="Description" />
				<input v-model.number="item.amount" type="number" placeholder="Amount" />
				<input v-model="item.division" placeholder="Div" />
				<input v-model="item.account_id" placeholder="Account ID" />
				<input v-model="item.date" type="date" placeholder="Date" />
				<input v-model="item.typ" placeholder="Typ" />
				<input v-model="item.trans_no" placeholder="Trans #" />
				<input v-model="item.ref_no" placeholder="Ref #" />
				<input v-model="item.currency" placeholder="Cur" />
				<input v-model.number="item.paid_foreign" type="number" placeholder="Paid (Foreign)" />
				<input v-model.number="item.paid_local" type="number" placeholder="Paid (Local)" />
				<button @click="removeItem(idx)">Remove</button>
			</div>
			<button @click="addItem">Add Item</button>
			<button @click="addPettyCash">Add Petty Cash</button>
		</div>

		<table>
			<thead>
				<tr>
					<th>PC #</th>
					<th>Ref</th>
					<th>Station ID</th>
					<th>Date</th>
					<th>Description</th>
					<th>User ID</th>
					<th>Total</th>
					<th>Action</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="(entry, idx) in pettyCashList" :key="idx">
					<td @click="toggleItems(idx)" style="cursor: pointer">{{ entry.pc_no }}</td>
					<td>{{ entry.ref }}</td>
					<td>{{ entry.station_id }}</td>
					<td>{{ entry.date }}</td>
					<td>{{ entry.description }}</td>
					<td>{{ entry.user_id }}</td>
					<td>{{ entry.total || calculateTotal(entry.items) }}</td>
					<td>
						<button @click="deletePettyCash(entry.pc_no)">Delete</button>
					</td>
				</tr>
				<tr v-if="expanded[idx]" :key="'items-' + idx">
					<td colspan="8">
						<table class="items-table">
							<thead>
								<tr>
									<th>A/C Code</th>
									<th>Account Name</th>
									<th>Description</th>
									<th>Amount</th>
									<th>Div</th>
									<th>Account ID</th>
									<th>Date</th>
									<th>Typ</th>
									<th>Trans #</th>
									<th>Ref #</th>
									<th>Cur</th>
									<th>Paid (Foreign)</th>
									<th>Paid (Local)</th>
								</tr>
							</thead>
							<tbody>
								<tr v-for="(item, i) in pettyCashList[idx].items" :key="i">
									<td>{{ item.ac_code }}</td>
									<td>{{ item.account_name }}</td>
									<td>{{ item.description }}</td>
									<td>{{ item.amount }}</td>
									<td>{{ item.division }}</td>
									<td>{{ item.account_id }}</td>
									<td>{{ item.date }}</td>
									<td>{{ item.typ }}</td>
									<td>{{ item.trans_no }}</td>
									<td>{{ item.ref_no }}</td>
									<td>{{ item.currency }}</td>
									<td>{{ item.paid_foreign }}</td>
									<td>{{ item.paid_local }}</td>
								</tr>
							</tbody>
						</table>
					</td>
				</tr>
			</tbody>
		</table>
	</div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import axios from "axios";

const pettyCashList = ref([]);
const expanded = ref([]);
const newEntry = ref({
	ref: "",
	station_id: "",
	date: "",
	description: "",
	user_id: "",
});
const newItems = ref([]);

// Fetch Petty Cash
async function fetchPettyCash() {
	try {
		const res = await axios.get(
			"/api/method/posawesome.posawesome.api.lazer_pos.get_petty_cash_transactions",
		);
		pettyCashList.value = res.data.message || [];
		expanded.value = Array(pettyCashList.value.length).fill(false);
	} catch (err) {
		console.error(err);
	}
}

// Add new item row
function addItem() {
	newItems.value.push({
		ac_code: "",
		account_name: "",
		description: "",
		amount: 0,
		division: "",
		account_id: "",
		date: "",
		typ: "",
		trans_no: "",
		ref_no: "",
		currency: "",
		paid_foreign: 0,
		paid_local: 0,
	});
}

// Remove item row
function removeItem(idx) {
	newItems.value.splice(idx, 1);
}

// Add Petty Cash
async function addPettyCash() {
	try {
		await axios.post("/api/method/posawesome.posawesome.api.lazer_pos.add_petty_cash", {
			pc_data: JSON.stringify(newEntry.value),
			items_data: JSON.stringify(newItems.value),
		});
		alert("Petty Cash added!");
		fetchPettyCash();
		Object.keys(newEntry.value).forEach((k) => (newEntry.value[k] = ""));
		newItems.value = [];
	} catch (err) {
		console.error(err);
		alert("Failed to add Petty Cash");
	}
}

// Delete Petty Cash
function deletePettyCash(pc_no) {
	if (confirm("Are you sure you want to delete this entry?")) {
		frappe
			.delete_doc("Petty Cash", pc_no)
			.then(() => {
				alert("Deleted!");
				fetchPettyCash();
			})
			.catch((err) => {
				console.error(err);
				alert("Failed to delete");
			});
	}
}

// Toggle items
function toggleItems(idx) {
	expanded.value[idx] = !expanded.value[idx];
}

// Calculate total
function calculateTotal(items) {
	return items?.reduce((sum, i) => sum + (i.amount || 0), 0) || 0;
}

onMounted(fetchPettyCash);
</script>

<style scoped>
table {
	width: 100%;
	border-collapse: collapse;
	margin-bottom: 20px;
}
th,
td {
	border: 1px solid #ccc;
	padding: 6px;
}
.items-table th,
.items-table td {
	font-size: 12px;
}
.add-form input {
	margin-right: 8px;
	margin-bottom: 8px;
}
.add-form button {
	margin-top: 8px;
	padding: 4px 12px;
}
.item-row {
	display: flex;
	flex-wrap: wrap;
	gap: 6px;
	margin-bottom: 4px;
}
.item-row input {
	width: 120px;
}
</style>
