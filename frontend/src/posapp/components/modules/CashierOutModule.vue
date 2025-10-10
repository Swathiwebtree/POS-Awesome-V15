<template>
	<div>
		<h2>Cashier Out</h2>
		<button @click="cashierOut">Confirm Cashier Out</button>
		<p v-if="status">{{ status }}</p>
	</div>
</template>

<script>
import axios from "axios";

export default {
	data() {
		return { status: null };
	},
	methods: {
		async cashierOut() {
			try {
				const res = await axios.post("/api/method/posawesome.posawesome.api.lazer_pos.cashier-out");
				this.status = res.data.message;
			} catch (err) {
				console.error(err);
			}
		},
	},
};
</script>
