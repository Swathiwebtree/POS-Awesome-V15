<template>
	<div class="stock-sales">
		<h2>Stock Sales</h2>
		<div class="filters">
			<input type="date" v-model="fromDate" />
			<input type="date" v-model="toDate" />
			<select v-model="groupBy">
				<option>Salesman</option>
				<option>Stock Item</option>
				<option>Department</option>
				<option>Main Category</option>
				<option>Sub Category</option>
			</select>
			<button @click="fetchSales">Fetch</button>
		</div>

		<table v-if="sales.length">
			<thead>
				<tr>
					<th>Date</th>
					<th>Stock Item</th>
					<th>Sales Type</th>
					<th>Quantity</th>
					<th>Amount</th>
					<th>Discount</th>
					<th>Net Sales</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="item in sales" :key="item.name">
					<td>{{ item.posting_date }}</td>
					<td>{{ item.items[0].stock_item }}</td>
					<td>{{ item.items[0].sales_type }}</td>
					<td>{{ item.items[0].quantity }}</td>
					<td>{{ item.items[0].amount }}</td>
					<td>{{ item.items[0].discount }}</td>
					<td>{{ item.items[0].net_sales }}</td>
				</tr>
				<tr>
					<td colspan="3"><b>Grand Total</b></td>
					<td>{{ totalQuantity }}</td>
					<td>{{ totalAmount }}</td>
					<td>{{ totalDiscount }}</td>
					<td>{{ totalNetSales }}</td>
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
			fromDate: "",
			toDate: "",
			groupBy: "Stock Item",
			sales: [],
		};
	},
	computed: {
		totalQuantity() {
			return this.sales.reduce((sum, s) => sum + s.items[0].quantity, 0);
		},
		totalAmount() {
			return this.sales.reduce((sum, s) => sum + s.items[0].amount, 0);
		},
		totalDiscount() {
			return this.sales.reduce((sum, s) => sum + s.items[0].discount, 0);
		},
		totalNetSales() {
			return this.sales.reduce((sum, s) => sum + s.items[0].net_sales, 0);
		},
	},
	methods: {
		async fetchSales() {
			const res = await axios.get("/api/resource/Stock Sales", {
				params: {
					filters: JSON.stringify([
						["posting_date", ">=", this.fromDate],
						["posting_date", "<=", this.toDate],
					]),
				},
			});
			this.sales = res.data.data;
		},
	},
};
</script>
