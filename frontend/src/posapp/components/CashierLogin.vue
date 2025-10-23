<template>
  <div class="modal-overlay">
    <div class="login-modal">
      <h2>Cashier Login</h2>
      <input type="password" v-model="cashierCode" placeholder="Enter Cashier PIN" />
      <button @click="login">Login</button>
      <p v-if="error" class="error">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";

const cashierCode = ref("");
const error = ref("");

const emit = defineEmits(["loginSuccess"]);

// Fetch all cashier PINs from ERPNext
const getCashiers = async () => {
  try {
    const res = await frappe.call({
      method: "frappe.client.get_list",
      args: {
        doctype: "Cashier",
        fields: ["cashier_code"],  // Only fetch PINs
      },
    });
    return res.message.map(c => c.cashier_code); // Array of PINs
  } catch (err) {
    console.error(err);
    error.value = "Failed to fetch cashiers";
    return [];
  }
};

const login = async () => {
  error.value = "";
  const pins = await getCashiers();

  if (pins.includes(cashierCode.value)) {
    emit("loginSuccess", cashierCode.value);
    cashierCode.value = "";
  } else {
    error.value = "Invalid Cashier PIN";
  }
};
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.login-modal {
  background: #fff;
  padding: 40px 50px;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
  width: 400px;
  max-width: 90%;
  text-align: center;
}

.login-modal h2 {
  margin-bottom: 25px;
  font-size: 1.8rem;
  font-weight: bold;
  color: #333;
}

.login-modal input {
  display: block;
  width: 100%;
  padding: 12px 10px;
  margin: 12px 0;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 1rem;
  text-align: center;
}

.login-modal button {
  width: 100%;
  padding: 12px;
  margin-top: 20px;
  background-color: #1e7f2e;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 1.1rem;
  cursor: pointer;
  transition: background 0.3s;
}

.login-modal button:hover {
  background-color: #166622;
}

.error {
  color: red;
  font-size: 0.95rem;
  margin-top: 10px;
}
</style>
