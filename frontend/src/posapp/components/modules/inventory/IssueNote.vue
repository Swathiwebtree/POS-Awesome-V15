<template>
  <div>
    <h2 class="text-xl font-semibold mb-4">Issue Note (ISN)</h2>

    <!-- Filter Section -->
    <div class="grid grid-cols-4 gap-2 mb-4">
      <input v-model="filters.startDate" type="date" placeholder="Start Date" class="input"/>
      <input v-model="filters.endDate" type="date" placeholder="End Date" class="input"/>
      <input v-model="filters.location" placeholder="Location" class="input"/>
      <input v-model="filters.status" placeholder="Status" class="input"/>
      <button @click="fetchIssueNotes" class="btn col-span-1">Fetch Issue Notes</button>
    </div>

    <!-- Issue Note List Table -->
    <table class="table-auto border w-full mb-4">
      <thead>
        <tr>
          <th>ISN #</th><th>Date</th><th>Type</th><th>Division</th><th>Location</th>
          <th>LPO</th><th>Station ID</th><th>Debit</th><th>Customer</th>
          <th>Sales Rep</th><th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(note, index) in issueNotes" :key="index" @click="selectNote(note)" class="cursor-pointer hover:bg-gray-100">
          <td>{{ note.name }}</td>
          <td>{{ note.posting_date }}</td>
          <td>{{ note.type }}</td>
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

    <!-- Selected Issue Note Items -->
    <div v-if="selectedNote">
      <h3 class="text-lg font-semibold mb-2">Item Details for ISN #: {{ selectedNote.name }}</h3>
      <table class="table-auto border w-full mb-4">
        <thead>
          <tr>
            <th>Barcode</th><th>Item Code</th><th>Item Name</th><th>Description</th>
            <th>Qty</th><th>Unit</th><th>Factor</th><th>Net Qty</th>
            <th>Loc.</th><th>Job</th><th>Div.</th>
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
            <td>{{ item.qty * item.factor }}</td>
            <td>{{ item.location }}</td>
            <td>{{ item.job }}</td>
            <td>{{ item.division }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const filters = ref({
  startDate: '',
  endDate: '',
  location: '',
  status: ''
})

const issueNotes = ref([])
const selectedNote = ref(null)

const fetchIssueNotes = async () => {
  try {
    const response = await frappe.call({
      method: 'posawesome.posawesome.api.lazer_pos.get_issue_note_list',
      args: {
        start_date: filters.value.startDate,
        end_date: filters.value.endDate,
        location: filters.value.location,
        status: filters.value.status
      }
    })
    issueNotes.value = response?.message || []
    selectedNote.value = null
  } catch (err) {
    console.error('Error fetching issue notes:', err)
  }
}

const selectNote = (note) => {
  selectedNote.value = note
}
</script>

<style scoped>
.input { border:1px solid #ccc; padding:4px; width:100%; margin-bottom:4px; }
.btn { background:#007bff; color:white; padding:6px 12px; cursor:pointer; }
.btn:hover { background:#0056b3; }
table { width: 100%; border-collapse: collapse; }
th, td { border:1px solid #ccc; padding:4px; }
.cursor-pointer { cursor:pointer; }
</style>
