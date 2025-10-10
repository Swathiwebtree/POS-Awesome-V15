<template>
	<div>
		<h2>System Module</h2>
		<button @click="getSystemStatus">Check System Status</button>
		<pre>{{ systemStatus }}</pre>
	</div>
</template>

<script>
import axios from "axios";

export default {
	name: "SystemModule",
	data() {
		return { systemStatus: null };
	},
	methods: {
		async getSystemStatus() {
			try {
				const res = await axios.get(
					"/api/method/posawesome.posawesome.api.lazer_pos.get_system_status",
				);
				this.systemStatus = res.data;
			} catch (err) {
				console.error(err);
			}
		},
	},
};
</script>
