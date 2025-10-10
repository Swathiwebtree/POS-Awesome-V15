<template>
	<div>
		<h2>Exit POS</h2>
		<button @click="exitPOS">Exit</button>
	</div>
</template>

<script>
export default {
	methods: {
		exitPOS() {
			window.location.href = "/app";
		},
	},
};
</script>
