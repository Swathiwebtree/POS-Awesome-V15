<template>
  <div class="service-issue-note">
    <div class="header">
      <h4>Service Issue Note</h4>
      <button class="btn-new" @click="newIssueNote">New Issue Note</button>
    </div>

    <table>
      <thead>
        <tr>
          <th>ISN #</th>
          <th>Description</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(issue, index) in serviceIssues" :key="index">
          <td>{{ issue.issue_code }}</td>
          <td>{{ issue.description }}</td>
          <td>{{ issue.status }}</td>
        </tr>
        <tr v-if="serviceIssues.length === 0">
          <td colspan="3" class="no-data">No service issues found</td>
        </tr>
      </tbody>
    </table>

    <div class="issue-form" v-if="showForm">
      <h5>New Service Issue</h5>
      <div class="info-row">
        <label>ISN #:</label> <input v-model="isn" />
        <label>Date:</label> <input type="date" v-model="date" />
        <label>Loc:</label> <input v-model="loc" />
        <label>Station ID:</label> <input v-model="stationId" />
        <label>Veh Reg #:</label> <input v-model="vehicleReg" />
        <label>Mobile #:</label> <input v-model="mobile" />
        <label>Work Order #:</label> <input v-model="workOrder" />
        <label>Sales Rep:</label> <input v-model="salesRep" />
        <label>Lift Employee:</label> <input v-model="liftEmployee" />
        <label>Model:</label> <input v-model="model" />
      </div>

      <h5>Item Details</h5>
      <table>
        <thead>
          <tr>
            <th>Barcode</th>
            <th>Item Code</th>
            <th>Item Name</th>
            <th>Qty</th>
            <th>Unit</th>
            <th>Factor</th>
            <th>Qty 2</th>
            <th>Price</th>
            <th>Amount</th>
            <th>Loc</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in items" :key="index">
            <td>{{ item.barcode }}</td>
            <td>{{ item.item_code }}</td>
            <td>{{ item.item_name }}</td>
            <td>{{ item.qty }}</td>
            <td>{{ item.unit }}</td>
            <td>{{ item.factor }}</td>
            <td>{{ item.qty2 }}</td>
            <td>{{ item.price }}</td>
            <td>{{ item.amount }}</td>
            <td>{{ item.loc }}</td>
          </tr>
        </tbody>
      </table>

      <textarea v-model="remarks" placeholder="Remarks"></textarea>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const serviceIssues = ref([])
const showForm = ref(false)

const isn = ref('')
const date = ref('')
const loc = ref('')
const stationId = ref('')
const vehicleReg = ref('')
const mobile = ref('')
const workOrder = ref('')
const salesRep = ref('')
const liftEmployee = ref('')
const model = ref('')
const remarks = ref('')
const items = ref([])

// Fetch list of service issues
async function fetchServiceIssues() {
  try {
    const response = await axios.get('/api/method/posawesome.posawesome.api.lazer_pos.get_service_issue_list')
    serviceIssues.value = response.data.message || []
  } catch (error) {
    console.error('Error fetching service issues:', error)
    serviceIssues.value = []
  }
}

function newIssueNote() {
  showForm.value = !showForm.value
}

// Load on mount
onMounted(() => {
  fetchServiceIssues()
})
</script>

<style scoped>
.service-issue-note {
  padding: 20px;
  font-family: Arial, sans-serif;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.btn-new {
  padding: 6px 12px;
  background-color: #1976d2;
  color: #fff;
  border: none;
  cursor: pointer;
}

.btn-new:hover {
  background-color: #1565c0;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 10px;
}

th,
td {
  border: 1px solid #ccc;
  padding: 6px 8px;
  text-align: left;
}

th {
  background-color: #f5f5f5;
}

.no-data {
  text-align: center;
  color: #888;
  font-style: italic;
}

.issue-form {
  border-top: 1px solid #ccc;
  padding-top: 15px;
}

.info-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 15px;
}

.info-row label {
  width: 120px;
  font-weight: bold;
}

.info-row input {
  flex: 1;
  padding: 4px;
  border: 1px solid #ccc;
}

textarea {
  width: 100%;
  height: 80px;
  margin-top: 10px;
  border: 1px solid #ccc;
  padding: 6px;
}
</style>
