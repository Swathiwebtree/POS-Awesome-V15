<template>
	<ModuleShell title="System">
		<div class="pa-4">
			<h3>System Settings</h3>
			<v-btn class="ma-2">POS Settings</v-btn>
			<v-btn class="ma-2">Printer Setup</v-btn>
			<v-btn class="ma-2">Shifts & Users</v-btn>
		</div>
	</ModuleShell>
</template>

<script>
import ModuleShell from "./ModuleShell.vue";
export default { name: "SystemModule", components: { ModuleShell } };
</script>

<style scoped></style>
