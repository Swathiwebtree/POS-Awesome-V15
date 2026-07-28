// Include onscan.js
const posaVersion = (() => {
	if (window.__POSAWESOME_BUILD_VERSION__) {
		return window.__POSAWESOME_BUILD_VERSION__;
	}
	if (window.__POSAWESOME_VERSION__) {
		return window.__POSAWESOME_VERSION__;
	}
	const script = Array.from(document.querySelectorAll("script")).find((el) =>
		(el.src || "").includes("/assets/posawesome/dist/js/posawesome.umd.js"),
	);
	if (!script || !script.src) return "";
	try {
		return new URL(script.src, window.location.origin).searchParams.get("v") || "";
	} catch {
		return "";
	}
})();
const withPosAwesomeVersion = (url) => {
	if (!posaVersion) return url;
	const separator = url.includes("?") ? "&" : "?";
	return `${url}${separator}v=${encodeURIComponent(posaVersion)}`;
};

frappe.pages["posapp"].on_page_load = async function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "POS Awesome",
		single_column: true,
	});

	// Ensure frappe.PosApp is available before using it
	if (!frappe.PosApp || !frappe.PosApp.posapp) {
		console.error("frappe.PosApp.posapp is not defined. Check if posawesome.umd.js is loaded properly.");
		return;
	}

	// Attach instance to the page
	page.$PosApp = new frappe.PosApp.posapp(page);

	// Adjust layout
	$("div.navbar-fixed-top").find(".container").css("padding", "0");

	// Load CSS dynamically
	$("head").append(
		"<link href='/assets/posawesome/node_modules/vuetify/dist/vuetify.min.css' rel='stylesheet'>",
	);
	$("head").append(
		"<link rel='stylesheet' href='https://cdn.jsdelivr.net/npm/@mdi/font@6.x/css/materialdesignicons.min.css'>",
	);
	$("head").append("<link rel='preconnect' href='https://fonts.googleapis.com'>");
	$("head").append("<link rel='preconnect' href='https://fonts.gstatic.com' crossorigin>");
	$("head").append(
		"<link rel='preload' href='https://fonts.googleapis.com/css?family=Roboto:100,300,400,500,700,900' as='style'>",
	);
	$("head").append(
		"<link rel='stylesheet' href='https://fonts.googleapis.com/css?family=Roboto:100,300,400,500,700,900'>",
	);

	// ---- SAFE HANDLER (no logic changed) ----
	const update_totals_based_on_tax_inclusive = async () => {
		console.log("Updating totals based on tax inclusive settings");

		//  Wait until Vue sets pos_profile
		let retries = 0;
		while ((!page.$PosApp || !page.$PosApp.posProfile) && retries < 20) {
			await new Promise((r) => setTimeout(r, 300));
			retries++;
		}

		const posProfile = page.$PosApp?.posProfile?.name;

		if (!posProfile) {
			console.warn("POS Profile not yet available. Skipping tax update.");
			return;
		}

		const cacheKey = "posa_tax_inclusive";
		const cachedValue = localStorage.getItem(cacheKey);

		const applySetting = (taxInclusive) => {
			const totalAmountField = document.getElementById("input-v-25");
			const grandTotalField = document.getElementById("input-v-29");

			if (!totalAmountField || !grandTotalField) {
				console.warn("Total / Grand Total fields not found yet");
				return;
			}

			if (taxInclusive) {
				totalAmountField.value = grandTotalField.value;
				console.log("Total copied from grand total:", grandTotalField.value);
			} else {
				totalAmountField.value = "";
				console.log("Total cleared (tax exclusive)");
			}
		};

		const fetchAndCache = () => {
			frappe.call({
				method: "posawesome.posawesome.api.utilities.get_pos_profile_tax_inclusive",
				args: { pos_profile: posProfile },
				callback: (response) => {
					if (response?.message !== undefined) {
						const posa_tax_inclusive = response.message;

						try {
							localStorage.setItem(cacheKey, JSON.stringify(posa_tax_inclusive));
						} catch (err) {
							console.warn("Failed to cache tax inclusive setting", err);
						}

						applySetting(posa_tax_inclusive);

						import(withPosAwesomeVersion("/assets/posawesome/dist/js/offline/index.js"))
							.then((m) => m?.setTaxInclusiveSetting?.(posa_tax_inclusive))
							.catch(() => {});
					}
				},
			});
		};

		if (!navigator.onLine && cachedValue) {
			try {
				const val = JSON.parse(cachedValue);
				applySetting(val);
				import(withPosAwesomeVersion("/assets/posawesome/dist/js/offline/index.js"))
					.then((m) => m?.setTaxInclusiveSetting?.(val))
					.catch(() => {});
				return;
			} catch {}
		}

		fetchAndCache();
	};

	// Listen for realtime profile registration
	frappe.realtime.on("pos_profile_registered", update_totals_based_on_tax_inclusive);
};
