<template>
	<div>
		<h2>Exit POS</h2>
		<button @click="exitPOS" class="btn btn-red">Confirm Exit</button>
	</div>
</template>

<script setup>
import axios from "axios";

const exitPOS = async () => {
	try {
		const res = await axios.post("/api/method/posawesome.posawesome.api.lazer_pos.exit_pos", {
			user: frappe.session.user,
		});
		alert(res.data.message);
		window.close(); // Close POS window
	} catch (error) {
		console.error(error);
		alert("Failed to exit POS");
	}
};
</script>
