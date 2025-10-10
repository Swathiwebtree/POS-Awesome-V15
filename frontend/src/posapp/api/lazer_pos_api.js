import axios from "axios";

const api = axios.create({
  baseURL: "/api/method/posawesome.api.lazer_pos", // Frappe backend API path
});

// Get vehicle details by license plate
export const getVehicleDetails = (vehicle_no) =>
  api.get("/get_vehicle_details", { params: { vehicle_no } });

// Get all service records for a vehicle
export const getServiceRecords = (vehicle_no) =>
  api.get("/get_service_records", { params: { vehicle_no } });

// Add a service to a vehicle
export const addService = (vehicle_no, service_type, cost = 0) =>
  api.post("/add_service", { vehicle_no, service_type, cost });

// Update status of a service/work order
export const updateServiceStatus = (work_order_name, status, service_item = null) =>
  api.post("/update_service_status", { work_order_name, status, service_item });
