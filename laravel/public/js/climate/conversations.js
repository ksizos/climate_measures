import { state } from "./state.js";

import {
    scrollToBottom,
    showError,
    hideError,
    hideWelcome,
    showWelcome,
} from "./ui.js";

import { clearChatMessages, addQuestionAnswerPair } from "./chat.js";

import { escapeHtml } from "./utils.js";

let conversationsCache = [];
let conversationPendingRename = null;

let currentSort = "new";

let conversationPendingDelete = null;
let deleteModalMode = null;

let currentSearch = "";
let searchTimeout = null;

let conversationsRequestController = null;

/* =========================================================
   НОВЫЙ ДИАЛОГ
   ========================================================= */

export async function startNewConversation() {
    if (state.isTrashMode) {
        state.isTrashMode = false;

        const binIcon = document.querySelector(".bin-icon");

        if (binIcon) {
            binIcon.style.filter = "";
        }
    }

    state.currentConversationId = null;

    updateActiveConversation();

    clearChatMessages();

    showWelcome();

    scrollToBottom();
}

/* =========================================================
   ПЕРЕИМЕНОВАНИЕ
   ========================================================= */

async function renameConversation(id, title) {
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]');

        const response = await fetch(`/climate/conversation/${id}/title`, {
            method: "PATCH",

            headers: {
                "X-CSRF-TOKEN": csrfToken?.content ?? "",

                "X-Requested-With": "XMLHttpRequest",

                Accept: "application/json",

                "Content-Type": "application/json",
            },

            body: JSON.stringify({
                title,
            }),
        });

        let data = {};

        try {
            data = await response.json();
        } catch {
            data = {};
        }

        if (!response.ok || !data.success) {
            return {
                success: false,

                message:
                    data.message ||
                    data.error ||
                    "Не удалось переименовать диалог.",
            };
        }

        const conversation = conversationsCache.find(
            (item) => String(item.id) === String(id),
        );

        if (conversation) {
            conversation.title = data.conversation?.title ?? title;
        }

        animateConversationsRender();

        return {
            success: true,
        };
    } catch (error) {
        console.error("Ошибка переименования диалога:", error);

        return {
            success: false,

            message: "Не удалось переименовать диалог.",
        };
    }
}

function openRenameConversationModal(id) {
    const modal = document.getElementById("renameConversationModal");

    const input = document.getElementById("renameConversationInput");

    const counter = document.getElementById("renameConversationCounter");

    const error = document.getElementById("renameConversationError");

    const confirmButton = document.getElementById("confirmRenameConversation");

    if (!modal || !input) {
        return;
    }

    const conversation = conversationsCache.find(
        (item) => String(item.id) === String(id),
    );

    conversationPendingRename = id;

    input.value = conversation?.title ?? "";

    if (counter) {
        counter.textContent = String(input.value.length);
    }

    if (error) {
        error.textContent = "";
    }

    if (confirmButton) {
        confirmButton.disabled = false;

        confirmButton.textContent = "Сохранить";
    }

    const openedPopover = document.querySelector(
        ".conversation-settings-panel:popover-open",
    );

    if (openedPopover && typeof openedPopover.hidePopover === "function") {
        openedPopover.hidePopover();
    }

    modal.classList.add("is-open");

    modal.setAttribute("aria-hidden", "false");

    document.body.style.overflow = "hidden";

    requestAnimationFrame(() => {
        input.focus();

        input.select();
    });
}

function closeRenameConversationModal() {
    const modal = document.getElementById("renameConversationModal");

    if (!modal) {
        return;
    }

    modal.classList.remove("is-open");

    modal.setAttribute("aria-hidden", "true");

    document.body.style.overflow = "";

    conversationPendingRename = null;

    const error = document.getElementById("renameConversationError");

    if (error) {
        error.textContent = "";
    }
}

/* =========================================================
   ЗАГРУЗКА КОНКРЕТНОГО ДИАЛОГА
   ========================================================= */

export async function loadConversation(id) {
    try {
        hideError();

        const response = await fetch(`/climate/conversation/${id}`, {
            headers: {
                Accept: "application/json",

                "X-Requested-With": "XMLHttpRequest",
            },
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            showError("Не удалось загрузить диалог");

            return;
        }

        state.currentConversationId = id;

        updateActiveConversation();

        hideWelcome();

        clearChatMessages();

        if (data.conversation && Array.isArray(data.conversation.messages)) {
            data.conversation.messages.forEach((pair) => {
                addQuestionAnswerPair(
                    pair.question,
                    pair.answer,
                    pair.status ?? "success",
                );
            });
        }

        scrollToBottom();
    } catch (error) {
        showError("Ошибка при загрузке диалога: " + error.message);
    }
}

/* =========================================================
   ЗАГРУЗКА ИСТОРИИ + ПОИСК
   ========================================================= */

export async function loadConversations(search = currentSearch) {
    let requestController = null;

    try {
        currentSearch = String(search ?? "").trim();

        if (conversationsRequestController) {
            conversationsRequestController.abort();
        }

        requestController = new AbortController();

        conversationsRequestController = requestController;

        const params = new URLSearchParams();

        if (currentSearch) {
            params.set("search", currentSearch);
        }

        const url = params.toString()
            ? `/climate/conversations?${params.toString()}`
            : "/climate/conversations";

        const response = await fetch(url, {
            headers: {
                Accept: "application/json",

                "X-Requested-With": "XMLHttpRequest",
            },

            signal: requestController.signal,
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            showError("Не удалось загрузить историю диалогов");

            return;
        }

        conversationsCache = Array.isArray(data.conversations)
            ? data.conversations
            : [];

        animateConversationsRender();
    } catch (error) {
        if (error.name === "AbortError") {
            return;
        }

        console.error("Ошибка загрузки диалогов:", error);

        showError("Ошибка загрузки истории диалогов");
    } finally {
        if (conversationsRequestController === requestController) {
            conversationsRequestController = null;
        }
    }
}

/* =========================================================
   УДАЛЕНИЕ ОДНОГО
   ========================================================= */

export async function deleteConversation(id) {
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]');

        const response = await fetch(`/climate/conversation/${id}`, {
            method: "DELETE",

            headers: {
                "X-CSRF-TOKEN": csrfToken?.content ?? "",

                "X-Requested-With": "XMLHttpRequest",

                Accept: "application/json",

                "Content-Type": "application/json",
            },
        });

        let data = {};

        try {
            data = await response.json();
        } catch {
            data = {};
        }

        if (!response.ok || !data.success) {
            showError(
                "Не удалось удалить диалог: " +
                    (data.error || data.message || "Неизвестная ошибка"),
            );

            return false;
        }

        if (String(state.currentConversationId) === String(id)) {
            state.currentConversationId = null;

            clearChatMessages();

            showWelcome();
        }

        await loadConversations();

        return true;
    } catch (error) {
        showError("Ошибка при удалении диалога: " + error.message);

        return false;
    }
}

/* =========================================================
   ОЧИСТКА ВСЕЙ ИСТОРИИ
   ========================================================= */

export async function clearConversationHistory() {
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]');

        const response = await fetch("/climate/conversations", {
            method: "DELETE",

            headers: {
                "X-CSRF-TOKEN": csrfToken?.content ?? "",

                "X-Requested-With": "XMLHttpRequest",

                Accept: "application/json",

                "Content-Type": "application/json",
            },
        });

        let data = {};

        try {
            data = await response.json();
        } catch {
            data = {};
        }

        if (!response.ok || !data.success) {
            showError("Не удалось очистить историю диалогов");

            return false;
        }

        state.currentConversationId = null;

        state.isTrashMode = false;

        currentSearch = "";

        conversationsCache = [];

        const searchInput = document.querySelector(".search");

        if (searchInput) {
            searchInput.value = "";
        }

        const binIcon = document.querySelector(".bin-icon");

        if (binIcon) {
            binIcon.style.filter = "";
        }

        clearChatMessages();

        showWelcome();

        animateConversationsRender();

        return true;
    } catch (error) {
        console.error("Ошибка очистки истории:", error);

        showError("Не удалось очистить историю диалогов");

        return false;
    }
}

/* =========================================================
   РЕЖИМ УДАЛЕНИЯ
   ========================================================= */

export function toggleTrashMode() {
    state.isTrashMode = !state.isTrashMode;

    animateConversationsRender();

    const binIcon = document.querySelector(".bin-icon");

    if (binIcon) {
        binIcon.style.filter = state.isTrashMode
            ? "invert(25%) sepia(94%) saturate(5072%) hue-rotate(358deg) brightness(102%) contrast(103%)"
            : "";
    }
}

/* =========================================================
   АНИМАЦИЯ
   ========================================================= */

function animateConversationsRender() {
    const scrollContainer = document.querySelector(".scroll_container");

    if (!scrollContainer) {
        renderSortedConversations();

        return;
    }

    scrollContainer.classList.add("is-sorting");

    setTimeout(() => {
        renderSortedConversations();

        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                scrollContainer.classList.remove("is-sorting");
            });
        });
    }, 180);
}

/* =========================================================
   ДАТА
   ========================================================= */

function parseRussianDate(dateString) {
    if (!dateString) {
        return null;
    }

    const [datePart, timePart] = dateString.split(" ");

    if (!datePart || !timePart) {
        return null;
    }

    const [day, month, year] = datePart.split(".");

    const [hours, minutes] = timePart.split(":");

    if (
        !day ||
        !month ||
        !year ||
        hours === undefined ||
        minutes === undefined
    ) {
        return null;
    }

    const date = new Date(
        Number(year),
        Number(month) - 1,
        Number(day),
        Number(hours),
        Number(minutes),
    );

    if (Number.isNaN(date.getTime())) {
        return null;
    }

    return date;
}

/* =========================================================
   СОРТИРОВКА
   ========================================================= */

function sortConversations(conversations) {
    const sorted = [...conversations];

    sorted.sort((a, b) => {
        const dateA = parseRussianDate(a.last_interaction_at);

        const dateB = parseRussianDate(b.last_interaction_at);

        if (!dateA && !dateB) {
            return 0;
        }

        if (!dateA) {
            return 1;
        }

        if (!dateB) {
            return -1;
        }

        if (currentSort === "old") {
            return dateA.getTime() - dateB.getTime();
        }

        return dateB.getTime() - dateA.getTime();
    });

    return sorted;
}

function renderSortedConversations() {
    const sorted = sortConversations(conversationsCache);

    renderConversations(sorted);
}

/* =========================================================
   РЕНДЕР
   ========================================================= */

function renderConversations(conversations) {
    const scrollContainer = document.querySelector(".scroll_container");

    if (!scrollContainer) {
        return;
    }

    const now = new Date();

    const todayStart = new Date(
        now.getFullYear(),
        now.getMonth(),
        now.getDate(),
    );

    const yesterdayStart = new Date(todayStart);

    yesterdayStart.setDate(yesterdayStart.getDate() - 1);

    const todayConvs = [];
    const yesterdayConvs = [];
    const olderConvs = [];

    conversations.forEach((conv) => {
        const interactionDate = parseRussianDate(conv.last_interaction_at);

        if (!interactionDate) {
            olderConvs.push(conv);

            return;
        }

        if (interactionDate >= todayStart) {
            todayConvs.push(conv);

            return;
        }

        if (interactionDate >= yesterdayStart) {
            yesterdayConvs.push(conv);

            return;
        }

        olderConvs.push(conv);
    });

    let html = "";

    if (currentSort === "old") {
        html += renderConversationGroup("Ранее", olderConvs, "mt-2");

        html += renderConversationGroup("Вчера", yesterdayConvs, "mt-3");

        html += renderConversationGroup("Сегодня", todayConvs, "mt-3");
    } else {
        html += renderConversationGroup("Сегодня", todayConvs, "mt-2");

        html += renderConversationGroup("Вчера", yesterdayConvs, "mt-3");

        html += renderConversationGroup("Ранее", olderConvs, "mt-3");
    }

    scrollContainer.innerHTML =
        html ||
        `
            <p class="text-muted text-center mt-3">
                ${currentSearch ? "Ничего не найдено" : "Нет диалогов"}
            </p>
        `;

    updateActiveConversation();

    bindConversationClickHandlers();

    updateDeleteButtonsVisibility();
}

/* =========================================================
   ГРУППЫ
   ========================================================= */

function renderConversationGroup(title, conversations, marginClass) {
    if (conversations.length === 0) {
        return "";
    }

    let html = `
        <h2
            class="scroll_header ${marginClass} mb-0 me-0 ms-0"
        >
            ${escapeHtml(title)}
        </h2>
    `;

    conversations.forEach((conv) => {
        html += createConversationHTML(conv);
    });

    return html;
}

/* =========================================================
   КЛИК ПО ДИАЛОГУ
   ========================================================= */

function bindConversationClickHandlers() {
    document.querySelectorAll(".conversation-item").forEach((item) => {
        item.addEventListener("click", function (event) {
            if (
                event.target.closest(".conversation-settings") ||
                event.target.closest(".conversation-settings-panel")
            ) {
                return;
            }

            if (state.isTrashMode) {
                return;
            }

            const id = this.dataset.id;

            if (!id) {
                return;
            }

            if (String(state.currentConversationId) === String(id)) {
                return;
            }

            loadConversation(id);
        });
    });
}

/* =========================================================
   ACTIVE
   ========================================================= */

function updateActiveConversation() {
    const items = document.querySelectorAll(".conversation-item");

    items.forEach((item) => {
        const isActive =
            state.currentConversationId !== null &&
            String(item.dataset.id) === String(state.currentConversationId);

        item.classList.toggle("active", isActive);
    });
}

/* =========================================================
   TRASH VISIBILITY
   ========================================================= */

function updateDeleteButtonsVisibility() {
    const deleteButtons = document.querySelectorAll(".delete-conversation");

    deleteButtons.forEach((btn) => {
        const conversationItem = btn.closest(".conversation-item");

        if (!conversationItem) {
            return;
        }

        conversationItem.classList.toggle("trash-mode-item", state.isTrashMode);
    });
}

/* =========================================================
   DELETE MODAL
   ========================================================= */

function openDeleteConversationModal(id = null, mode = "single") {
    const modal = document.getElementById("deleteConversationModal");

    if (!modal) {
        return;
    }

    const title = document.getElementById("deleteConversationTitle");

    const text = modal.querySelector(".delete-modal__text");

    const confirmButton = document.getElementById("confirmDeleteConversation");

    deleteModalMode = mode;

    if (mode === "all") {
        conversationPendingDelete = null;

        if (title) {
            title.textContent = "Очистить историю?";
        }

        if (text) {
            text.textContent =
                "Вы уверены, что хотите удалить всю историю диалогов? Это действие нельзя отменить.";
        }

        if (confirmButton) {
            confirmButton.textContent = "Да, очистить";
        }
    } else {
        conversationPendingDelete = id;

        if (title) {
            title.textContent = "Удалить диалог?";
        }

        if (text) {
            text.textContent =
                "Вы уверены, что хотите удалить этот диалог? Это действие нельзя отменить.";
        }

        if (confirmButton) {
            confirmButton.textContent = "Да, удалить";
        }
    }

    const openedPopover = document.querySelector(
        ".conversation-settings-panel:popover-open",
    );

    if (openedPopover && typeof openedPopover.hidePopover === "function") {
        openedPopover.hidePopover();
    }

    const filterPanel = document.getElementById("filterPanel");

    if (filterPanel && typeof filterPanel.hidePopover === "function") {
        filterPanel.hidePopover();
    }

    modal.classList.add("is-open");

    modal.setAttribute("aria-hidden", "false");

    document.body.style.overflow = "hidden";

    if (confirmButton) {
        confirmButton.disabled = false;

        confirmButton.focus();
    }
}

function closeDeleteConversationModal() {
    const modal = document.getElementById("deleteConversationModal");

    if (!modal) {
        return;
    }

    modal.classList.remove("is-open");

    modal.setAttribute("aria-hidden", "true");

    document.body.style.overflow = "";

    conversationPendingDelete = null;

    deleteModalMode = null;
}

/* =========================================================
   HTML ДИАЛОГА
   ========================================================= */

function createConversationHTML(conv) {
    const anchorName = `--conversation-settings-${conv.id}`;

    const panelId = `conversation-settings-${conv.id}`;

    const isActive =
        state.currentConversationId !== null &&
        String(state.currentConversationId) === String(conv.id);

    return `
        <div
            class="
                conversation-item
                fade_text
                w-100
                position-relative
                p-2
                mb-1
                rounded
                ${isActive ? "active" : ""}
            "
            data-id="${conv.id}"
        >

            <div
                class="
                    d-flex
                    justify-content-between
                    align-items-start
                "
            >

                <div
                    class="flex-grow-1 me-2"
                >

                    <p
                        class="
                            conversation-title
                            fw-bold
                            mb-1
                        "
                    >
                        ${escapeHtml(conv.title ?? "Без названия")}
                    </p>


                    ${
                        conv.last_question
                            ? `
                                <p
                                    class="
                                        m-0
                                        conversation-text-small
                                    "
                                >
                                    ${escapeHtml(conv.last_question)}
                                </p>
                            `
                            : ""
                    }


                    ${
                        conv.last_answer_preview
                            ? `
                                <p
                                    class="
                                        m-0
                                        conversation-text-small
                                        text-muted
                                        fst-italic
                                    "
                                >
                                    ${escapeHtml(conv.last_answer_preview)}...
                                </p>
                            `
                            : ""
                    }

                </div>


                <div
                    class="fade_block"
                ></div>

            </div>


            <div
                class="conversation-settings"
            >

                <button
                    type="button"
                    class="settings-btn"
                    data-conversation-id="${conv.id}"
                    popovertarget="${panelId}"
                    style="
                        anchor-name:
                        ${anchorName};
                    "
                    aria-label="Настройки диалога"
                >

                    <img
                        class="settings_img"
                        src="/icons/dots.svg"
                        alt=""
                    >

                </button>


                <div
                    id="${panelId}"
                    class="
                        conversation-settings-panel
                    "
                    popover="auto"
                    style="
                        position-anchor:
                        ${anchorName};
                    "
                >

                    <button
                        type="button"
                        class="
                            conversation-settings-panel__item
                        "
                        data-action="rename"
                        data-conversation-id="${conv.id}"
                    >

                        <img
                            src="/icons/edit.svg"
                            class="conversation_panel_image"
                            alt=""
                        >

                        Переименовать
                    </button>


                    <button
                        type="button"
                        class="
                            conversation-settings-panel__item
                            conversation-settings-panel__item--danger
                        "
                        data-action="delete"
                        data-conversation-id="${conv.id}"
                    >

                        <img
                            src="/icons/delete.svg"
                            class="conversation_panel_image"
                            alt=""
                        >

                        Удалить
                    </button>

                </div>

            </div>

        </div>
    `;
}

/* =========================================================
   INIT
   ========================================================= */

export function initConversations() {
    const newChatBtn = document.querySelector(".new-chat-block");

    const binIcon = document.querySelector(".bin-icon");

    const conversationSort = document.getElementById("conversationSort");

    const searchInput = document.querySelector(".search");

    const clearHistoryButton = document.getElementById(
        "clearConversationHistory",
    );

    const cancelDeleteButton = document.getElementById(
        "cancelDeleteConversation",
    );

    const confirmDeleteButton = document.getElementById(
        "confirmDeleteConversation",
    );

    const renameInput = document.getElementById("renameConversationInput");

    const renameCounter = document.getElementById("renameConversationCounter");

    const renameError = document.getElementById("renameConversationError");

    const cancelRenameButton = document.getElementById(
        "cancelRenameConversation",
    );

    const confirmRenameButton = document.getElementById(
        "confirmRenameConversation",
    );

    if (newChatBtn) {
        newChatBtn.addEventListener("click", startNewConversation);
    }

    if (binIcon) {
        binIcon.addEventListener("click", toggleTrashMode);
    }

    if (conversationSort) {
        currentSort = conversationSort.value || "new";

        conversationSort.addEventListener("change", function () {
            currentSort = this.value;

            animateConversationsRender();
        });
    }

    if (searchInput) {
        searchInput.addEventListener("input", function () {
            clearTimeout(searchTimeout);

            const value = this.value.trim();

            searchTimeout = setTimeout(() => {
                currentSearch = value;

                loadConversations(currentSearch);
            }, 300);
        });

        searchInput.addEventListener("search", function () {
            clearTimeout(searchTimeout);

            currentSearch = this.value.trim();

            loadConversations(currentSearch);
        });
    }

    if (clearHistoryButton) {
        clearHistoryButton.addEventListener("click", function (event) {
            event.preventDefault();

            event.stopPropagation();

            openDeleteConversationModal(null, "all");
        });
    }

    document.addEventListener("click", function (event) {
        const target = event.target;

        if (!(target instanceof Element)) {
            return;
        }

        const renameButton = target.closest('[data-action="rename"]');

        if (renameButton) {
            event.preventDefault();

            event.stopPropagation();

            const conversationId = renameButton.dataset.conversationId;

            if (!conversationId) {
                return;
            }

            openRenameConversationModal(conversationId);

            return;
        }

        const deleteButton = target.closest('[data-action="delete"]');

        if (!deleteButton) {
            return;
        }

        event.preventDefault();

        event.stopPropagation();

        const conversationId = deleteButton.dataset.conversationId;

        if (!conversationId) {
            return;
        }

        openDeleteConversationModal(conversationId, "single");
    });

    if (renameInput) {
        renameInput.addEventListener("input", function () {
            if (this.value.length > 30) {
                this.value = this.value.slice(0, 30);
            }

            if (renameCounter) {
                renameCounter.textContent = String(this.value.length);
            }

            if (renameError) {
                renameError.textContent = "";
            }
        });

        renameInput.addEventListener("keydown", function (event) {
            if (event.key === "Enter") {
                event.preventDefault();

                confirmRenameButton?.click();
            }
        });
    }

    if (cancelRenameButton) {
        cancelRenameButton.addEventListener(
            "click",
            closeRenameConversationModal,
        );
    }

    if (confirmRenameButton) {
        confirmRenameButton.addEventListener("click", async function () {
            if (conversationPendingRename === null) {
                return;
            }

            const title = renameInput?.value.trim() ?? "";

            if (!title) {
                if (renameError) {
                    renameError.textContent = "Введите название диалога.";
                }

                renameInput?.focus();

                return;
            }

            if (title.length > 30) {
                if (renameError) {
                    renameError.textContent =
                        "Название не должно превышать 30 символов.";
                }

                renameInput?.focus();

                return;
            }

            const conversationId = conversationPendingRename;

            this.disabled = true;

            this.textContent = "Сохранение...";

            const result = await renameConversation(conversationId, title);

            if (result.success) {
                closeRenameConversationModal();

                return;
            }

            this.disabled = false;

            this.textContent = "Сохранить";

            if (renameError) {
                renameError.textContent = result.message;
            }
        });
    }

    document
        .querySelectorAll("[data-rename-modal-close]")
        .forEach((element) => {
            element.addEventListener("click", closeRenameConversationModal);
        });

    if (cancelDeleteButton) {
        cancelDeleteButton.addEventListener(
            "click",
            closeDeleteConversationModal,
        );
    }

    if (confirmDeleteButton) {
        confirmDeleteButton.addEventListener("click", async function () {
            this.disabled = true;

            if (deleteModalMode === "all") {
                this.textContent = "Очистка...";

                const success = await clearConversationHistory();

                if (success) {
                    closeDeleteConversationModal();

                    return;
                }

                this.disabled = false;

                this.textContent = "Да, очистить";

                return;
            }

            if (
                deleteModalMode === "single" &&
                conversationPendingDelete !== null
            ) {
                const conversationId = conversationPendingDelete;

                this.textContent = "Удаление...";

                const success = await deleteConversation(conversationId);

                if (success) {
                    closeDeleteConversationModal();

                    return;
                }

                this.disabled = false;

                this.textContent = "Да, удалить";

                return;
            }

            this.disabled = false;
        });
    }

    document
        .querySelectorAll("[data-delete-modal-close]")
        .forEach((element) => {
            element.addEventListener("click", closeDeleteConversationModal);
        });

    document.addEventListener("keydown", function (event) {
        if (event.key !== "Escape") {
            return;
        }

        const renameModal = document.getElementById("renameConversationModal");

        if (renameModal?.classList.contains("is-open")) {
            closeRenameConversationModal();

            return;
        }

        const deleteModal = document.getElementById("deleteConversationModal");

        if (deleteModal?.classList.contains("is-open")) {
            closeDeleteConversationModal();
        }
    });
}
