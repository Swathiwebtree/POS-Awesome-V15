<template>
	<ModuleShell title="Exit">
		<div class="pa-4">
			<h3>Exit</h3>
			<v-btn color="error" @click="confirmExit">Confirm Exit</v-btn>
		</div>
	</ModuleShell>
</template>

<script>
import ModuleShell from "./ModuleShell.vue";
export default {
	name: "ExitModule",
	components: { ModuleShell },
	methods: {
		confirmExit() {
			// replace with actual logout or navigation
			window.location.href = "/app";
		},
	},
};
</script>

<style scoped></style>
