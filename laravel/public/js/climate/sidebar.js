export function initSidebar() {
    const sidebar = document.getElementById("sidebar");

    const toggleButton = document.getElementById("sidebarToggleButton");

    if (!sidebar || !toggleButton) {
        return;
    }

    toggleButton.addEventListener("click", () => {
        sidebar.classList.toggle("sidebar-hidden");

        const hidden = sidebar.classList.contains("sidebar-hidden");

        toggleButton.setAttribute(
            "aria-label",
            hidden ? "Развернуть боковую панель" : "Свернуть боковую панель",
        );
    });
}
