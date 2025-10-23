<template>
  <div class="p-4">
    <h2 class="text-xl font-bold mb-4">Day End Closing</h2>

    <div class="mb-4">
      <input v-model="newUser" placeholder="User" class="input" />
      <input v-model="newCash" type="number" placeholder="Total Cash" class="input" />
      <input v-model="newOpenOrders" type="number" placeholder="Open Work Orders" class="input" />
      <input v-model="newClosingTime" type="datetime-local" class="input" />
      <button @click="addDayEnd" class="btn">Add</button>
    </div>

    <table class="table-auto w-full border">
      <thead>
        <tr>
          <th>User</th>
          <th>Total Cash</th>
          <th>Open Work Orders</th>
          <th>Closing Time</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="day in dayEndList" :key="day.name">
          <td>{{ day.user }}</td>
          <td><input v-model="day.total_cash" type="number" /></td>
          <td><input v-model="day.open_work_orders" type="number" /></td>
          <td><input v-model="day.closing_time" type="datetime-local" /></td>
          <td>
            <button @click="updateDayEnd(day)" class="btn">Save</button>
            <button @click="deleteDayEnd(day.name)" class="btn btn-red">Delete</button>
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
      dayEndList: [],
      newUser: '',
      newCash: '',
      newOpenOrders: '',
      newClosingTime: ''
    };
  },
  mounted() {
    this.fetchDayEnd();
  },
  methods: {
    async fetchDayEnd() {
      const res = await axios.get('/api/method/posawesome.posawesome.api.lazer_pos.get_day_end');
      this.dayEndList = res.data.message;
    },
    async addDayEnd() {
      await axios.post('/api/method/posawesome.posawesome.api.lazer_pos.create_day_end', {
        user: this.newUser,
        total_cash: this.newCash,
        open_work_orders: this.newOpenOrders,
        closing_time: this.newClosingTime
      });
      this.newUser = '';
      this.newCash = '';
      this.newOpenOrders = '';
      this.newClosingTime = '';
      this.fetchDayEnd();
    },
    async updateDayEnd(day) {
      await axios.post('/api/method/posawesome.posawesome.api.lazer_pos.update_day_end', {
        name: day.name,
        total_cash: day.total_cash,
        open_work_orders: day.open_work_orders,
        closing_time: day.closing_time
      });
      this.fetchDayEnd();
    },
    async deleteDayEnd(name) {
      await axios.post('/api/method/posawesome.posawesome.api.lazer_pos.delete_day_end', { name });
      this.fetchDayEnd();
    }
  }
};
</script>
