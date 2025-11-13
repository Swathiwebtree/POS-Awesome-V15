/* global localStorage */

// --- Generic Storage Functions (Re-included from previous step) ---

// Define which storage mechanism to use.
const storage = localStorage;
const CUSTOMER_STORAGE_KEY = "posawesome_customers"; // Unique key for customer data

/**
 * Safely retrieves an item from storage, automatically parsing JSON.
 */
export function getItem(key) {
	try {
		const value = storage.getItem(key);
		if (value === null) {
			return null;
		}
		// Attempt to parse as JSON for objects/arrays
		return JSON.parse(value);
	} catch (e) {
		// If parsing fails (it's not JSON), return the raw string value
		if (e instanceof SyntaxError) {
			return storage.getItem(key);
		}
		console.error(`Error retrieving key '${key}' from storage:`, e);
		return null;
	}
}

/**
 * Safely sets an item in storage, automatically stringifying objects/arrays.
 */
export function setItem(key, value) {
	try {
		const serializedValue = typeof value === "string" ? value : JSON.stringify(value);
		storage.setItem(key, serializedValue);
	} catch (e) {
		// This often catches QuotaExceededError (storage full)
		console.error(`Error setting key '${key}' in storage. Error:`, e);
	}
}

// You can keep the other generic exports if needed:
export function removeItem(key) {
	try {
		storage.removeItem(key);
	} catch (e) {
		console.error(`Error removing key '${key}' from storage:`, e);
	}
}
export function clearStorage() {
	try {
		storage.clear();
	} catch (e) {
		console.error("Error clearing storage:", e);
	}
}

// --------------------------------------------------------------------
// --- Specific Exported Functions for Customer.vue (THE FIX) ---
// --------------------------------------------------------------------

/**
 * Saves customer data to local storage.
 * This is the function Customer.vue expects as 'setCustomerStorage'.
 * @param {Array<Object>} customers - The list of customer records.
 */
export function setCustomerStorage(customers) {
	console.log("Saving customers to storage...");
	setItem(CUSTOMER_STORAGE_KEY, customers);
}

/**
 * Retrieves customer data from local storage.
 * This is the function Customer.vue expects as 'getCustomersStorage'.
 * @returns {Array<Object>} The list of customer records, or an empty array if none found.
 */
export function getCustomersStorage() {
	const customers = getItem(CUSTOMER_STORAGE_KEY);
	console.log("Retrieving customers from storage.");
	return customers || [];
}
