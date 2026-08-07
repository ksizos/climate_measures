export function initSidebar() {
    const sidebar = document.getElementById("sidebar");

    const toggle = document.getElementById("sidebarToggle");

    if (!sidebar || !toggle) {
        return;
    }

    toggle.addEventListener("click", () => {
        sidebar.classList.toggle("sidebar-hidden");

        const hidden = sidebar.classList.contains("sidebar-hidden");

        toggle.style.transform = hidden ? "rotate(180deg)" : "rotate(0deg)";
    });
}
