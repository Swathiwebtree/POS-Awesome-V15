const normalizeText = (value) => (value || "").toString().trim().toLowerCase();

const getSearchableFields = (item) => [item?.item_group, item?.item_name, item?.item_code, item?.code]
	.map((value) => normalizeText(value))
	.filter(Boolean);

export function looksLikeEngineOilItem(item) {
	const row = item?.raw || item || {};
	const itemType = normalizeText(row.item_type);
	if (itemType === "engine_oil") {
		return true;
	}

	return getSearchableFields(row).some((text) => {
		return (
			text.includes("engine oil") ||
			text.includes("engine-oil") ||
			text.includes("engineoil")
		);
	});
}

export function looksLikeServiceItem(item) {
	const row = item?.raw || item || {};
	const itemType = normalizeText(row.item_type);
	if (itemType === "service" || Number(row.custom_service_item || 0) === 1) {
		return true;
	}

	const searchable = getSearchableFields(row);
	const keywords = ["carwash", "car wash", "bike wash", "bikewash", "wash", "service"];
	return searchable.some((text) => keywords.some((keyword) => text.includes(keyword)));
}

export function getItemType(item) {
	const row = item?.raw || item || {};
	const itemType = normalizeText(row.item_type);
	if (looksLikeEngineOilItem(row)) {
		return "engine_oil";
	}
	if (itemType && itemType !== "unknown") {
		return itemType;
	}
	if (Number(row.custom_service_item || 0) === 1) {
		return "service";
	}
	if (looksLikeServiceItem(row)) {
		return "service";
	}
	if (Number(row.is_stock_item || 0) === 1) {
		return "stock";
	}
	return "unknown";
}
