<template>
  <div class="p-6">
    <h2 class="text-2xl font-semibold mb-4 text-gray-800">Issue Note (ISN)</h2>

    <!-- Filter Section -->
    <div class="grid grid-cols-5 gap-3 mb-6">
      <input v-model="filters.startDate" type="date" class="input" />
      <input v-model="filters.endDate" type="date" class="input" />
      <input v-model="filters.location" class="input" placeholder="Location" />
      <select v-model="filters.status" class="input">
        <option value="">All Status</option>
        <option value="Pending">Pending</option>
        <option value="Approved">Approved</option>
        <option value="Completed">Completed</option>
      </select>
      <button @click="fetchIssueNotes" class="btn">Fetch</button>
    </div>

    <!-- Issue Note Table -->
    <div v-if="issueNotes.length" class="overflow-x-auto mb-8 border rounded-lg shadow-sm">
      <table class="min-w-full text-sm">
        <thead class="bg-gray-100">
          <tr>
            <th>ISN #</th>
            <th>Date</th>
            <th>Type</th>
            <th>Division</th>
            <th>Location</th>
            <th>LPO</th>
            <th>Station ID</th>
            <th>Debit</th>
            <th>Customer</th>
            <th>Sales Rep</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="note in issueNotes"
            :key="note.name"
            @click="selectNote(note)"
            class="hover:bg-gray-50 cursor-pointer"
          >
            <td>{{ note.isn_no }}</td>
            <td>{{ formatDate(note.date) }}</td>
            <td>{{ note.issue_type }}</td>
            <td>{{ note.division }}</td>
            <td>{{ note.location }}</td>
            <td>{{ note.lpo }}</td>
            <td>{{ note.station_id }}</td>
            <td>{{ note.debit_account }}</td>
            <td>{{ note.customer }}</td>
            <td>{{ note.sales_rep }}</td>
            <td>{{ note.status }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <p v-else class="text-gray-500 text-sm italic">No Issue Notes found.</p>

    <!-- Selected Note Details -->
    <div v-if="selectedNote" class="mt-8">
      <h3 class="text-lg font-semibold mb-3 text-gray-700">
        Issue Note Details — {{ selectedNote.isn_no }}
      </h3>
      <div class="grid grid-cols-3 gap-2 mb-4 text-sm text-gray-700">
        <p><b>Division:</b> {{ selectedNote.division }}</p>
        <p><b>Location:</b> {{ selectedNote.location }}</p>
        <p><b>Date:</b> {{ formatDate(selectedNote.date) }}</p>
        <p><b>Customer:</b> {{ selectedNote.customer }}</p>
        <p><b>Sales Rep:</b> {{ selectedNote.sales_rep }}</p>
        <p><b>Status:</b> {{ selectedNote.status }}</p>
        <p><b>Remarks:</b> {{ selectedNote.remarks || "-" }}</p>
      </div>

      <h4 class="text-md font-semibold mb-2">Item Details</h4>
      <div class="overflow-x-auto border rounded-lg">
        <table class="min-w-full text-sm">
          <thead class="bg-gray-100">
            <tr>
              <th>Barcode</th>
              <th>Item Code</th>
              <th>Item Name</th>
              <th>Description</th>
              <th>Qty</th>
              <th>Unit</th>
              <th>Factor</th>
              <th>Net Qty</th>
              <th>Loc.</th>
              <th>Job</th>
              <th>Div.</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, idx) in selectedNote.items" :key="idx">
              <td>{{ item.barcode }}</td>
              <td>{{ item.item_code }}</td>
              <td>{{ item.item_name }}</td>
              <td>{{ item.description }}</td>
              <td>{{ item.qty }}</td>
              <td>{{ item.unit }}</td>
              <td>{{ item.factor }}</td>
              <td>{{ item.net_qty }}</td>
              <td>{{ item.location }}</td>
              <td>{{ item.job }}</td>
              <td>{{ item.division }}</td>
            </tr>
            <tr v-if="!selectedNote.items.length">
              <td colspan="11" class="text-center text-gray-500">No items found.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import axios from "axios";

const filters = ref({
  startDate: "",
  endDate: "",
  location: "",
  status: "",
});

const issueNotes = ref([]);
const selectedNote = ref(null);

// Automatically include cookies
axios.defaults.withCredentials = true;

// Include CSRF token for POST requests (if needed)
axios.interceptors.request.use((config) => {
  const csrfToken = frappe.csrf_token;
  if (csrfToken) {
    config.headers["X-Frappe-CSRF-Token"] = csrfToken;
  }
  return config;
});

// Format date helper
const formatDate = (date) => {
  if (!date) return "";
  return new Date(date).toLocaleDateString();
};

// Fetch main Issue Notes
const fetchIssueNotes = async () => {
  try {
    const filtersObj = {};
    if (filters.value.status) filtersObj.status = filters.value.status;
    if (filters.value.location) filtersObj.location = ["like", `%${filters.value.location}%`];
    if (filters.value.startDate && filters.value.endDate) {
      filtersObj.date = ["between", [filters.value.startDate, filters.value.endDate]];
    }

    const res = await axios.get("/api/resource/Issue Note", {
      params: {
        fields: JSON.stringify([
          "name","isn_no","issue_type","division","location",
          "date","lpo","station_id","debit_account",
          "customer","sales_rep","status"
        ]),
        filters: JSON.stringify(filtersObj),
        limit_page_length: 50,
        order_by: "modified desc"
      }
    });

    issueNotes.value = res.data.data || [];
    selectedNote.value = null;
  } catch (err) {
    console.error("Error fetching Issue Notes:", err);
  }
};

// Fetch selected note + child table items
const selectNote = async (note) => {
  try {
    const res = await axios.get(`/api/resource/Issue Note/${note.name}`);
    const data = res.data.data;

    // Fetch child table items
    const itemsRes = await axios.get("/api/resource/Issue Note Item", {
      params: {
        filters: JSON.stringify([["parent", "=", note.name]])
      }
    });

    selectedNote.value = {
      ...data,
      items: itemsRes.data.data || []
    };
  } catch (err) {
    console.error("Error fetching Issue Note details:", err);
  }
};
</script>

<style scoped>
.input {
  border: 1px solid #ccc;
  padding: 6px 8px;
  width: 100%;
  border-radius: 4px;
}
.btn {
  background-color: #007bff;
  color: #fff;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}
.btn:hover {
  background-color: #0056b3;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th,
td {
  border: 1px solid #ccc;
  padding: 6px 8px;
  text-align: left;
}
th {
  font-weight: 600;
}
</style>
