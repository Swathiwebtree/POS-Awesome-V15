export function jinjaPrint(doctype, name, print_format, no_letterhead, silent) {
	frappe.call({
		method: "posawesome.posawesome.api.invoices.get_print_html",
		args: {
			doctype: doctype,
			name: name,
			print_format: print_format,
			no_letterhead: no_letterhead || 0,
		},
		callback: function (r) {
			if (!r.message) return;
			const html = r.message;
			if (silent) {
				silentPrintHTML(html);
			} else {
				const win = window.open("", "_blank");
				if (win) {
					win.document.write(html);
					win.document.close();
					win.focus();
					win.print();
				}
			}
		},
	});
}

function silentPrintHTML(html) {
	try {
		const iframe = document.createElement("iframe");
		iframe.style.position = "fixed";
		iframe.style.right = "0";
		iframe.style.bottom = "0";
		iframe.style.width = "0";
		iframe.style.height = "0";
		iframe.style.border = "0";
		document.body.appendChild(iframe);
		iframe.contentDocument.write(html);
		iframe.contentDocument.close();
		iframe.contentWindow.focus();
		iframe.contentWindow.print();
		setTimeout(() => iframe.remove(), 1000);
	} catch (err) {
		console.error("Silent print failed, falling back to new window", err);
		const win = window.open("", "_blank");
		if (win) {
			win.document.write(html);
			win.document.close();
			win.focus();
			win.print();
		}
	}
}

export function silentPrint(url) {
	if (!url) return;
	try {
		const iframe = document.createElement("iframe");
		iframe.style.position = "fixed";
		iframe.style.right = "0";
		iframe.style.bottom = "0";
		iframe.style.width = "0";
		iframe.style.height = "0";
		iframe.style.border = "0";
		iframe.onload = () => {
			try {
				iframe.contentWindow.focus();
				iframe.contentWindow.print();
			} finally {
				setTimeout(() => iframe.remove(), 1000);
			}
		};
		iframe.src = url;
		document.body.appendChild(iframe);
	} catch (err) {
		console.error("Silent print failed, falling back to new window", err);
		const win = window.open(url, "_blank");
		if (win) {
			win.addEventListener("load", () => win.print(), { once: true });
		}
	}
}
