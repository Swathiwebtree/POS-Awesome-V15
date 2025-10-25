<template>
	<div class="p-4">
		<h2 class="text-xl font-bold mb-4">Cashier Out</h2>

		<div class="mb-4">
			<input v-model="newUser" placeholder="User" class="input" />
			<input v-model="newShift" placeholder="Shift" class="input" />
			<input v-model="newCash" type="number" placeholder="Total Cash" class="input" />
			<input v-model="newStart" type="datetime-local" class="input" />
			<input v-model="newEnd" type="datetime-local" class="input" />
			<button @click="addShift" class="btn">Add Shift</button>
		</div>

		<table class="table-auto w-full border">
			<thead>
				<tr>
					<th>User</th>
					<th>Shift</th>
					<th>Total Cash</th>
					<th>Start Time</th>
					<th>End Time</th>
					<th>Actions</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="shift in shifts" :key="shift.name">
					<td>{{ shift.user }}</td>
					<td>{{ shift.shift }}</td>
					<td><input v-model="shift.total_cash" type="number" /></td>
					<td>{{ shift.start_time }}</td>
					<td><input v-model="shift.end_time" type="datetime-local" /></td>
					<td>
						<button @click="updateShift(shift)" class="btn">Save</button>
						<button @click="deleteShift(shift.name)" class="btn btn-red">Delete</button>
					</td>
				</tr>
			</tbody>
		</table>
	</div>
</template>

<script>
import axios from "axios";
export default {
	data() {
		return {
			shifts: [],
			newUser: "",
			newShift: "",
			newCash: "",
			newStart: "",
			newEnd: "",
		};
	},
	mounted() {
		this.fetchShifts();
	},
	methods: {
		async fetchShifts() {
			const res = await axios.get("/api/method/posawesome.posawesome.api.lazer_pos.get_shifts");
			this.shifts = res.data.message;
		},
		async addShift() {
			await axios.post("/api/method/posawesome.posawesome.api.lazer_pos.create_shift", {
				user: this.newUser,
				shift: this.newShift,
				total_cash: this.newCash,
				start_time: this.newStart,
				end_time: this.newEnd,
			});
			this.newUser = "";
			this.newShift = "";
			this.newCash = "";
			this.newStart = "";
			this.newEnd = "";
			this.fetchShifts();
		},
		async updateShift(shift) {
			await axios.post("/api/method/posawesome.posawesome.api.lazer_pos.update_shift", {
				name: shift.name,
				total_cash: shift.total_cash,
				end_time: shift.end_time,
			});
			this.fetchShifts();
		},
		async deleteShift(name) {
			await axios.post("/api/method/posawesome.posawesome.api.lazer_pos.delete_shift", { name });
			this.fetchShifts();
		},
	},
};
</script>
