export function escapeHtml(text) {
    if (!text) {
        return "";
    }

    const div = document.createElement("div");

    div.textContent = text;

    return div.innerHTML;
}

export function addTargetBlankToLinks(html) {
    const parser = new DOMParser();

    const doc = parser.parseFromString(html, "text/html");

    doc.querySelectorAll("a[href]").forEach((link) => {
        if (!link.target) {
            link.target = "_blank";
        }

        link.rel = "noopener noreferrer";
    });

    return doc.body.innerHTML;
}
