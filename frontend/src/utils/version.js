const buildVersion =
	typeof __POSAWESOME_BUILD_VERSION__ !== "undefined"
		? __POSAWESOME_BUILD_VERSION__
		: typeof __POSAWESOME_VERSION__ !== "undefined"
			? __POSAWESOME_VERSION__
			: typeof window !== "undefined" && window.__POSAWESOME_BUILD_VERSION__
				? window.__POSAWESOME_BUILD_VERSION__
				: typeof window !== "undefined" && window.__POSAWESOME_VERSION__
					? window.__POSAWESOME_VERSION__
					: "";

export const POSAWESOME_VERSION = buildVersion;

export function withPosAwesomeVersion(url) {
	if (!buildVersion) return url;
	const separator = url.includes("?") ? "&" : "?";
	return `${url}${separator}v=${encodeURIComponent(buildVersion)}`;
}
