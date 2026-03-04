<template>
	<v-dialog
		:model-value="modelValue"
		max-width="420"
		width="92vw"
		class="cancel-sale-dialog"
		@update:model-value="$emit('update:modelValue', $event)"
	>
		<v-card>
			<v-card-title class="text-h5">
				<span class="text-h5 text-primary">{{ __("Cancel Sale ?") }}</span>
			</v-card-title>
			<v-card-text>
				This would cancel and delete the current sale. To save it as Draft, click the "Save and Clear"
				instead.
			</v-card-text>
			<v-card-actions>
				<v-spacer></v-spacer>
				<v-btn color="error" @click="onConfirm">{{ __("Yes, Cancel sale") }}</v-btn>
				<v-btn color="warning" @click="$emit('update:modelValue', false)">{{ __("Back") }}</v-btn>
			</v-card-actions>
		</v-card>
	</v-dialog>
</template>

<script>
export default {
	props: {
		modelValue: Boolean,
	},
	emits: ["update:modelValue", "confirm"],
	methods: {
		onConfirm() {
			// Emit confirm event to parent
			this.$emit("confirm");

			// Emit event bus for InvoiceSummary and Payments to clear
			this.eventBus.emit("confirm_cancel_sale");

			// Close the dialog
			this.$emit("update:modelValue", false);
		},
	},
};
</script>

<style scoped>
.cancel-sale-dialog :deep(.v-card) {
	width: 100%;
}

.cancel-sale-dialog :deep(.v-card-title) {
	padding-bottom: 6px;
}

.cancel-sale-dialog :deep(.v-card-actions) {
	flex-wrap: wrap;
	gap: 8px;
}

@media (max-width: 600px) {
	.cancel-sale-dialog :deep(.v-card-actions .v-btn) {
		width: 100%;
	}
}
</style>
