<template>
  <div class="p-4">
    <h2 class="text-xl font-bold mb-4">Cash Counting</h2>
    
    <div class="mb-4">
      <input v-model="newUser" placeholder="User" class="input" />
      <input v-model="newAmount" placeholder="Amount" type="number" class="input" />
      <input v-model="newDate" type="datetime-local" class="input" />
      <button @click="addCashCount" class="btn">Add</button>
    </div>

    <table class="table-auto w-full border">
      <thead>
        <tr>
          <th>User</th>
          <th>Amount</th>
          <th>Date</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="count in cashCounts" :key="count.name">
          <td>{{ count.user }}</td>
          <td><input v-model="count.amount" type="number" /></td>
          <td>{{ count.date }}</td>
          <td>
            <button @click="updateCashCount(count)" class="btn">Save</button>
            <button @click="deleteCashCount(count.name)" class="btn btn-red">Delete</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import axios from 'axios';
export default {
  data() {
    return {
      cashCounts: [],
      newUser: '',
      newAmount: '',
      newDate: ''
    };
  },
  mounted() {
    this.fetchCashCounts();
  },
  methods: {
    async fetchCashCounts() {
      const res = await axios.get('/api/method/posawesome.posawesome.api.lazer_pos.get_cash_counts');
      this.cashCounts = res.data.message;
    },
    async addCashCount() {
      await axios.post('/api/method/posawesome.posawesome.api.lazer_pos.create_cash_count', {
        user: this.newUser,
        amount: this.newAmount,
        date: this.newDate
      });
      this.newUser = '';
      this.newAmount = '';
      this.newDate = '';
      this.fetchCashCounts();
    },
    async updateCashCount(count) {
      await axios.post('/api/method/posawesome.posawesome.api.lazer_pos.update_cash_count', {
        name: count.name,
        amount: count.amount
      });
      this.fetchCashCounts();
    },
    async deleteCashCount(name) {
      await axios.post('/api/method/posawesome.posawesome.api.lazer_pos.delete_cash_count', { name });
      this.fetchCashCounts();
    }
  }
};
</script>
