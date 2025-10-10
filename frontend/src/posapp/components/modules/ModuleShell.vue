<template>
	<v-card>
		<v-card-title>
			<div>{{ title }}</div>
			<v-spacer />
			<div v-if="!authenticated">
				<v-text-field
					placeholder="Cashier code"
					v-model="code"
					dense
					hide-details
					class="mr-2"
					style="width: 140px"
				/>
				<v-btn small @click="loginCashier">Enter</v-btn>
			</div>
			<div v-else>
				<v-chip small color="green" text-color="white">Authenticated</v-chip>
			</div>
		</v-card-title>

		<v-divider />

		<v-card-text>
			<div v-if="authenticated">
				<slot />
			</div>
			<div v-else class="text-center">
				<p>Enter cashier login code to access this module.</p>
			</div>
		</v-card-text>
	</v-card>
</template>

<script>
export default {
	name: "ModuleShell",
	props: { title: { type: String, required: true } },
	data() {
		return { code: "", authenticated: false };
	},
	methods: {
		loginCashier() {
			// placeholder authentication - replace with your logic
			if (this.code && this.code.length >= 3) {
				this.authenticated = true;
			} else {
				this.$emit("show-message", { title: "Invalid code", color: "error" });
			}
		},
	},
};
</script>

<style scoped></style>
