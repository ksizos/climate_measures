export function initSidebar() {
    const sidebar = document.getElementById("sidebar");

    const toggleButton = document.getElementById("sidebarToggleButton");

    const backdrop = document.getElementById("sidebarBackdrop");

    if (!sidebar || !toggleButton) {
        return;
    }

    const mobileMedia = window.matchMedia("(max-width: 768px)");

    function isMobile() {
        return mobileMedia.matches;
    }

    function updateDesktopButtonState() {
        const hidden = sidebar.classList.contains("sidebar-hidden");

        toggleButton.setAttribute("aria-expanded", hidden ? "false" : "true");

        toggleButton.setAttribute(
            "aria-label",
            hidden ? "Развернуть боковую панель" : "Свернуть боковую панель",
        );
    }

    function updateMobileButtonState() {
        const opened = sidebar.classList.contains("mobile-open");

        toggleButton.setAttribute("aria-expanded", opened ? "true" : "false");

        toggleButton.setAttribute(
            "aria-label",
            opened ? "Закрыть боковую панель" : "Открыть боковую панель",
        );
    }

    function openMobileSidebar() {
        sidebar.classList.add("mobile-open");

        backdrop?.classList.add("is-open");

        backdrop?.setAttribute("aria-hidden", "false");

        document.body.classList.add("sidebar-mobile-open");

        updateMobileButtonState();
    }

    function closeMobileSidebar() {
        sidebar.classList.remove("mobile-open");

        backdrop?.classList.remove("is-open");

        backdrop?.setAttribute("aria-hidden", "true");

        document.body.classList.remove("sidebar-mobile-open");

        updateMobileButtonState();
    }

    function toggleMobileSidebar() {
        const opened = sidebar.classList.contains("mobile-open");

        if (opened) {
            closeMobileSidebar();

            return;
        }

        openMobileSidebar();
    }

    function toggleDesktopSidebar() {
        sidebar.classList.toggle("sidebar-hidden");

        updateDesktopButtonState();
    }

    function applyResponsiveMode() {
        /*
         * MOBILE
         */
        if (isMobile()) {
            /*
             * Desktop collapsed-состояние
             * на мобильном не используется.
             */
            sidebar.classList.remove("sidebar-hidden");

            closeMobileSidebar();

            return;
        }

        /*
         * DESKTOP
         */
        sidebar.classList.remove("mobile-open");

        backdrop?.classList.remove("is-open");

        backdrop?.setAttribute("aria-hidden", "true");

        document.body.classList.remove("sidebar-mobile-open");

        updateDesktopButtonState();
    }

    toggleButton.addEventListener("click", () => {
        if (isMobile()) {
            toggleMobileSidebar();

            return;
        }

        toggleDesktopSidebar();
    });

    backdrop?.addEventListener("click", () => {
        if (isMobile()) {
            closeMobileSidebar();
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key !== "Escape") {
            return;
        }

        if (isMobile() && sidebar.classList.contains("mobile-open")) {
            closeMobileSidebar();
        }
    });

    mobileMedia.addEventListener("change", applyResponsiveMode);

    applyResponsiveMode();
}
