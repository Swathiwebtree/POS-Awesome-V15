<template>
  <div class="service-issue-note">
    <!-- Header -->
    <div class="header">
      <h4>Service Issue Note</h4>
      <button class="btn-new" @click="toggleForm">
        {{ showForm ? 'Close' : 'New Issue Note' }}
      </button>
    </div>

    <!-- Service Issue Notes Table -->
    <table>
      <thead>
        <tr>
          <th>ISN #</th>
          <th>Vehicle Reg #</th>
          <th>Customer</th>
          <th>Status</th>
          <th>Priority</th>
          <th>Date</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(issue, index) in serviceIssues" :key="index">
          <td>{{ issue.issue_id }}</td>
          <td>{{ issue.vehicle }}</td>
          <td>{{ issue.customer }}</td>
          <td>{{ issue.status }}</td>
          <td>{{ issue.priority }}</td>
          <td>{{ issue.service_date }}</td>
        </tr>
        <tr v-if="serviceIssues.length === 0">
          <td colspan="6" class="no-data">No service issues found</td>
        </tr>
      </tbody>
    </table>

    <!-- New Service Issue Form -->
    <div v-if="showForm" class="issue-form">
      <h5>New Service Issue</h5>

      <div class="info-row">
        <label>ISN #:</label>
        <input v-model="form.issue_id" />

        <label>Date:</label>
        <input type="date" v-model="form.service_date" />

        <label>Loc:</label>
        <input v-model="form.loc" />

        <label>Station ID:</label>
        <input v-model="form.station_id" />

        <label>Veh Reg #:</label>
        <input v-model="form.vehicle" />

        <label>Mobile #:</label>
        <input v-model="form.mobile" />

        <label>Work Order #:</label>
        <input v-model="form.work_order" />

        <label>Sales Rep:</label>
        <input v-model="form.sales_rep" />

        <label>Lift Employee:</label>
        <input v-model="form.lift_employee" />

        <label>Model:</label>
        <input v-model="form.model" />

        <label>Priority:</label>
        <select v-model="form.priority">
          <option value="">Select</option>
          <option>Low</option>
          <option>Medium</option>
          <option>High</option>
        </select>

        <label>Status:</label>
        <select v-model="form.status">
          <option>Open</option>
          <option>In Progress</option>
          <option>Resolved</option>
          <option>Closed</option>
        </select>
      </div>

      <!-- Issue Details -->
      <div class="details-section">
        <label>Issue Details:</label>
        <textarea v-model="form.issue_details" placeholder="Describe the issue"></textarea>
      </div>

      <!-- Item Details -->
      <h5>Item Details</h5>
      <table class="items-table">
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
          <tr v-for="(item, index) in form.items" :key="index">
            <td><input v-model="item.barcode" /></td>
            <td><input v-model="item.item_code" /></td>
            <td><input v-model="item.item_name" /></td>
            <td><input type="number" v-model="item.qty" /></td>
            <td><input v-model="item.unit" /></td>
            <td><input v-model="item.factor" /></td>
            <td><input type="number" v-model="item.qty2" /></td>
            <td><input type="number" v-model="item.price" /></td>
            <td><input type="number" v-model="item.amount" /></td>
            <td><input v-model="item.loc" /></td>
          </tr>
        </tbody>
      </table>

      <button class="btn-add-item" @click="addItem">+ Add Item</button>

      <!-- Remarks -->
      <div class="details-section">
        <label>Remarks:</label>
        <textarea v-model="form.remarks" placeholder="Additional notes..."></textarea>
      </div>

      <div class="form-actions">
        <button class="btn-save" @click="saveIssueNote">Save Issue Note</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import axios from "axios";

// State
const serviceIssues = ref([]);
const showForm = ref(false);

// Default form data
const form = ref({
  issue_id: "",
  service_date: "",
  loc: "",
  station_id: "",
  vehicle: "",
  mobile: "",
  work_order: "",
  sales_rep: "",
  lift_employee: "",
  model: "",
  priority: "",
  status: "Open",
  issue_details: "",
  remarks: "",
  items: [],
});

// Fetch list of service issues
async function fetchServiceIssues() {
  try {
    const response = await axios.get(
      "/api/method/posawesome.posawesome.api.lazer_pos.get_service_issue_list"
    );
    serviceIssues.value = response.data.message || [];
  } catch (error) {
    console.error("Error fetching service issues:", error);
  }
}

// Add a new item row
function addItem() {
  form.value.items.push({
    barcode: "",
    item_code: "",
    item_name: "",
    qty: 1,
    unit: "",
    factor: "",
    qty2: "",
    price: "",
    amount: "",
    loc: "",
  });
}

// Save new issue note to ERPNext
async function saveIssueNote() {
  try {
    const response = await axios.post(
      "/api/method/posawesome.posawesome.api.lazer_pos.create_service_issue_note",
      { data: form.value }
    );

    if (response.data.message === "success") {
      alert("Service Issue Note saved successfully!");
      showForm.value = false;
      fetchServiceIssues();
    } else {
      alert("Failed to save issue note.");
    }
  } catch (error) {
    console.error("Error saving issue note:", error);
    alert("Error while saving issue note.");
  }
}

// Toggle form visibility
function toggleForm() {
  showForm.value = !showForm.value;
}

// Load issues on mount
onMounted(() => {
  fetchServiceIssues();
});
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
  margin-bottom: 15px;
}
.btn-new {
  padding: 6px 12px;
  background-color: #1976d2;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.btn-new:hover {
  background-color: #125ca1;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 15px;
}
th, td {
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
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 15px;
}
.info-row label {
  font-weight: bold;
}
.info-row input, select {
  width: 100%;
  padding: 4px;
  border: 1px solid #ccc;
}
.details-section {
  margin: 15px 0;
}
textarea {
  width: 100%;
  height: 80px;
  padding: 6px;
  border: 1px solid #ccc;
}
.items-table input {
  width: 100%;
  padding: 4px;
  border: 1px solid #ccc;
}
.btn-add-item {
  margin-top: 5px;
  padding: 4px 10px;
  background-color: #4caf50;
  color: white;
  border: none;
  border-radius: 3px;
  cursor: pointer;
}
.btn-add-item:hover {
  background-color: #3e8e41;
}
.form-actions {
  text-align: right;
  margin-top: 10px;
}
.btn-save {
  background-color: #1976d2;
  color: white;
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.btn-save:hover {
  background-color: #125ca1;
}
</style>
