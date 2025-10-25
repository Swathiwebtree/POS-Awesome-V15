<template>
	<div class="p-4">
		<h2 class="text-xl font-bold mb-4">System Settings</h2>

		<div class="mb-4">
			<input v-model="newParam" placeholder="Parameter" class="input" />
			<input v-model="newValue" placeholder="Value" class="input" />
			<button @click="addSetting" class="btn">Add</button>
		</div>

		<table class="table-auto w-full border">
			<thead>
				<tr>
					<th>Parameter</th>
					<th>Value</th>
					<th>Actions</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="setting in settings" :key="setting.name">
					<td>{{ setting.parameter }}</td>
					<td>
						<input v-model="setting.value" />
					</td>
					<td>
						<button @click="updateSetting(setting)" class="btn">Save</button>
						<button @click="deleteSetting(setting.name)" class="btn btn-red">Delete</button>
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
			settings: [],
			newParam: "",
			newValue: "",
		};
	},
	mounted() {
		this.fetchSettings();
	},
	methods: {
		async fetchSettings() {
			const res = await axios.get("/api/method/posawesome.posawesome.api.lazer_pos.get_settings");
			this.settings = res.data.message;
		},
		async addSetting() {
			await axios.post("/api/method/posawesome.posawesome.api.lazer_pos.create_setting", {
				parameter: this.newParam,
				value: this.newValue,
			});
			this.newParam = "";
			this.newValue = "";
			this.fetchSettings();
		},
		async updateSetting(setting) {
			await axios.post("/api/method/posawesome.posawesome.api.lazer_pos.update_setting", {
				name: setting.name,
				value: setting.value,
			});
			this.fetchSettings();
		},
		async deleteSetting(name) {
			await axios.post("/api/method/posawesome.posawesome.api.lazer_pos.delete_setting", { name });
			this.fetchSettings();
		},
	},
};
</script>
