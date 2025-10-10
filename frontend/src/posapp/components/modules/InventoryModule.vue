<template>
	<div class="inventory-module p-4">
		<h1 class="text-2xl font-bold mb-4">Inventory Module</h1>

		<!-- Submodule Tabs -->
		<div class="flex space-x-2 mb-4">
			<button
				v-for="tab in tabs"
				:key="tab.name"
				@click="currentTab = tab.name"
				:class="[
					'px-4 py-2 rounded',
					currentTab === tab.name ? 'bg-blue-500 text-white' : 'bg-gray-200',
				]"
			>
				{{ tab.label }}
			</button>
		</div>

		<!-- Submodule Component -->
		<component v-if="currentComponent" :is="currentComponent" />
	</div>
</template>

<script setup>
import { ref, computed, watch } from "vue";

// Accept default submodule from parent
const props = defineProps({
	defaultSubmodule: {
		type: String,
		default: "MaterialRequest",
	},
});

// Define submodules with dynamic imports for lazy loading
const tabs = [
	{
		name: "MaterialRequest",
		label: "Material Request",
		component: () => import("./inventory/MaterialRequest.vue"),
	},
	{
		name: "GoodsReceiptNote",
		label: "Goods Receipt Note",
		component: () => import("./inventory/GoodsReceiptNote.vue"),
	},
	{ name: "IssueNote", label: "Issue Note", component: () => import("./inventory/IssueNote.vue") },
	{ name: "TransferIn", label: "Transfer In", component: () => import("./inventory/TransferIn.vue") },
	{ name: "TransferOut", label: "Transfer Out", component: () => import("./inventory/TransferOut.vue") },
	{
		name: "PhysicalCount",
		label: "Physical Count",
		component: () => import("./inventory/PhysicalCount.vue"),
	},
	{
		name: "ProductionForm",
		label: "Production Form",
		component: () => import("./inventory/ProductionForm.vue"),
	},
	{ name: "DamageMemo", label: "Damage Memo", component: () => import("./inventory/DamageMemo.vue") },
];

// Reactive current tab
const currentTab = ref(props.defaultSubmodule);

// Watch for changes in the defaultSubmodule from parent
watch(
	() => props.defaultSubmodule,
	(newVal) => {
		if (newVal) currentTab.value = newVal;
	},
);

// Computed to return current component dynamically
const currentComponent = computed(() => {
	const tab = tabs.find((t) => t.name === currentTab.value);
	return tab ? tab.component : null;
});
</script>

<style scoped>
.inventory-module {
	max-width: 1200px;
	margin: 0 auto;
}

.inventory-module button {
	transition: all 0.2s ease;
}

.inventory-module button:hover {
	opacity: 0.8;
}
</style>
