import axios from "axios";

// export async function loginCashier(code) {
//   const res = await axios.post(
//     "/api/method/posawesome.posawesome.api.posapp.validate_cashier",
//     { code }
//   );

//   // Directly return response since backend is already simplified
//   return res.data; 
// }
export async function loginCashier(code) {
  return {
    status: "success",
    cashier: {
      name: "Test Cashier",
      employee_name: "Test Employee",
      user: frappe.session.user || "Administrator",
      terminal: "Default Terminal",
      role: "Cashier"
    }
  };
}
