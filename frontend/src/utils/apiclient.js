// ~/frappe-bench/apps/posawesome/frontend/src/utils/apiclient.js
import axios from "axios";

const apiClient = axios.create({
  baseURL: "http://localhost:8000/api/method", // change this to your backend API URL if different
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

export default apiClient;
