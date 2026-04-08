export const GCC_PHONE_RULES = {
	BH: { dial: "973", len: 8 },
	KW: { dial: "965", len: 8 },
	OM: { dial: "968", len: 8 },
	QA: { dial: "974", len: 8 },
	SA: { dial: "966", len: 9 },
	AE: { dial: "971", len: 9 },
};

export const GCC_COUNTRY_ALIASES = {
	BH: "BH",
	BAHRAIN: "BH",
	KW: "KW",
	KUWAIT: "KW",
	OM: "OM",
	OMAN: "OM",
	QA: "QA",
	QATAR: "QA",
	SA: "SA",
	"SAUDI ARABIA": "SA",
	SAUDI: "SA",
	AE: "AE",
	UAE: "AE",
	"UNITED ARAB EMIRATES": "AE",
};

export function resolveGccIso(countryValue, fallbackIso = "BH") {
	const key = String(countryValue || "")
		.trim()
		.toUpperCase();
	if (GCC_COUNTRY_ALIASES[key]) return GCC_COUNTRY_ALIASES[key];
	return GCC_PHONE_RULES[fallbackIso] ? fallbackIso : "BH";
}

export function resolveCountryIso(countryValue, fallbackIso = "BH") {
	const fallback = String(fallbackIso || "")
		.trim()
		.toUpperCase();
	const key = String(countryValue || "")
		.trim()
		.toUpperCase();
	if (GCC_COUNTRY_ALIASES[key]) return GCC_COUNTRY_ALIASES[key];
	if (!fallback) return "";
	return GCC_PHONE_RULES[fallback] ? fallback : "";
}

function toDigits(value) {
	return String(value || "").replace(/\D/g, "");
}

export function getGccRule(isoOrCountry, fallbackIso = "BH") {
	const iso = resolveGccIso(isoOrCountry, fallbackIso);
	return { iso, rule: GCC_PHONE_RULES[iso] || GCC_PHONE_RULES.BH };
}

export function toGccNationalDigits(value, isoOrCountry, fallbackIso = "BH") {
	const { rule } = getGccRule(isoOrCountry, fallbackIso);
	let digits = toDigits(value);
	if (!digits) return "";

	if (digits.startsWith("00")) {
		digits = digits.slice(2);
	}
	if (digits.startsWith(rule.dial) && digits.length > rule.dial.length) {
		digits = digits.slice(rule.dial.length);
	}
	if (digits.startsWith("0") && digits.length === rule.len + 1) {
		digits = digits.slice(1);
	}

	return digits.slice(0, rule.len);
}

export function toGccE164(value, isoOrCountry, fallbackIso = "BH") {
	const { rule } = getGccRule(isoOrCountry, fallbackIso);
	const national = toGccNationalDigits(value, isoOrCountry, fallbackIso);
	return national ? `+${rule.dial}${national}` : "";
}

export function validateGccNational(value, isoOrCountry, fallbackIso = "BH") {
	const { iso, rule } = getGccRule(isoOrCountry, fallbackIso);
	const national = toGccNationalDigits(value, iso, fallbackIso);
	const len = national.length;
	return {
		iso,
		national,
		expectedLength: rule.len,
		isEmpty: len === 0,
		isTooShort: len > 0 && len < rule.len,
		isComplete: len === rule.len,
		isTooLong: len > rule.len,
		e164: len === rule.len ? `+${rule.dial}${national}` : "",
	};
}

export function formatPhoneForDisplay(value, isoOrCountry = "BH") {
	const raw = String(value || "").trim();
	if (!raw) return "";
	const { rule } = getGccRule(isoOrCountry, "BH");
	const digits = raw.replace(/\D/g, "");
	if (!digits) return "";

	if (digits.startsWith(rule.dial) && digits.length > rule.dial.length) {
		return digits.slice(rule.dial.length);
	}
	if (raw.startsWith("+")) {
		return `+${digits}`;
	}
	return digits;
}
