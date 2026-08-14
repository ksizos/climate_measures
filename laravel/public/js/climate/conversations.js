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

let currentSort = "new";

let conversationPendingDelete = null;

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
   ЗАГРУЗКА СПИСКА ДИАЛОГОВ + ПОИСК
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
   УДАЛЕНИЕ ДИАЛОГА
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
   РЕЖИМ КОРЗИНЫ
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
   АНИМАЦИЯ СОРТИРОВКИ
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
   ПАРСИНГ ДАТЫ
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
   РЕНДЕР ИСТОРИИ
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

    if (state.isTrashMode) {
        html += `
            <div
                class="trash-mode-header d-flex justify-content-between align-items-center mb-3 p-2 bg-light rounded"
            >
                <h5 class="mb-0 text-danger">
                    <i class="fas fa-trash me-2"></i>
                    Режим удаления
                </h5>

                <button
                    type="button"
                    class="btn btn-sm btn-outline-secondary exit-trash-mode"
                    title="Выйти из режима удаления"
                    style="border: none;"
                >
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
    }

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
            <p
                class="text-muted text-center mt-3"
            >
                ${currentSearch ? "Ничего не найдено" : "Нет диалогов"}
            </p>
        `;

    updateActiveConversation();

    bindConversationClickHandlers();

    bindTrashModeHandlers();

    updateDeleteButtonsVisibility();
}

/* =========================================================
   ГРУППА ДИАЛОГОВ
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
   СТАРЫЙ TRASH MODE
   ========================================================= */

function bindTrashModeHandlers() {
    document.querySelectorAll(".delete-conversation").forEach((btn) => {
        btn.addEventListener("click", function (event) {
            event.preventDefault();

            event.stopPropagation();

            const id = this.dataset.id;

            if (!id) {
                return;
            }

            openDeleteConversationModal(id);
        });
    });

    const exitBtn = document.querySelector(".exit-trash-mode");

    if (exitBtn) {
        exitBtn.addEventListener("click", function (event) {
            event.preventDefault();

            event.stopPropagation();

            state.isTrashMode = false;

            renderSortedConversations();

            const binIcon = document.querySelector(".bin-icon");

            if (binIcon) {
                binIcon.style.filter = "";
            }
        });
    }
}

/* =========================================================
   ACTIVE CONVERSATION
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
   TRASH MODE VISIBILITY
   ========================================================= */

function updateDeleteButtonsVisibility() {
    const deleteButtons = document.querySelectorAll(".delete-conversation");

    deleteButtons.forEach((btn) => {
        const conversationItem = btn.closest(".conversation-item");

        if (!conversationItem) {
            return;
        }

        if (state.isTrashMode) {
            if (btn.parentElement) {
                btn.parentElement.style.display = "block";
            }

            conversationItem.classList.add("trash-mode-item");
        } else {
            if (btn.parentElement) {
                btn.parentElement.style.display = "none";
            }

            conversationItem.classList.remove("trash-mode-item");
        }
    });
}

/* =========================================================
   DELETE MODAL
   ========================================================= */

function openDeleteConversationModal(id) {
    const modal = document.getElementById("deleteConversationModal");

    if (!modal) {
        console.error("Не найден #deleteConversationModal");

        return;
    }

    conversationPendingDelete = id;

    const openedPopover = document.querySelector(
        ".conversation-settings-panel:popover-open",
    );

    if (openedPopover && typeof openedPopover.hidePopover === "function") {
        openedPopover.hidePopover();
    }

    modal.classList.add("is-open");

    modal.setAttribute("aria-hidden", "false");

    document.body.style.overflow = "hidden";

    const confirmButton = document.getElementById("confirmDeleteConversation");

    if (confirmButton) {
        confirmButton.disabled = false;

        confirmButton.textContent = "Да, удалить";

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
            class="conversation-item fade_text w-100 position-relative p-2 mb-1 rounded ${
                state.isTrashMode ? "trash-mode-item" : ""
            } ${isActive ? "active" : ""}"
            data-id="${conv.id}"
        >
            <div
                class="d-flex justify-content-between align-items-start"
            >

                <div
                    class="flex-grow-1 me-2"
                >

                    <p
                        class="conversation-title fw-bold mb-1"
                    >
                        ${escapeHtml(conv.title ?? "Без названия")}
                    </p>

                    ${
                        conv.last_question
                            ? `
                                <p
                                    class="m-0 conversation-text-small"
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
                                    class="m-0 conversation-text-small text-muted fst-italic"
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
                    style="anchor-name: ${anchorName};"
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
                    class="conversation-settings-panel"
                    popover="auto"
                    style="position-anchor: ${anchorName};"
                >

                    <button
                        type="button"
                        class="conversation-settings-panel__item"
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
                        class="conversation-settings-panel__item conversation-settings-panel__item--danger"
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
   ИНИЦИАЛИЗАЦИЯ
   ========================================================= */

export function initConversations() {
    const newChatBtn = document.querySelector(".new-chat-block");

    const binIcon = document.querySelector(".bin-icon");

    const conversationSort = document.getElementById("conversationSort");

    const searchInput = document.querySelector(".search");

    const cancelDeleteButton = document.getElementById(
        "cancelDeleteConversation",
    );

    const confirmDeleteButton = document.getElementById(
        "confirmDeleteConversation",
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

    document.addEventListener("click", function (event) {
        const target = event.target;

        if (!(target instanceof Element)) {
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

        openDeleteConversationModal(conversationId);
    });

    if (cancelDeleteButton) {
        cancelDeleteButton.addEventListener(
            "click",
            closeDeleteConversationModal,
        );
    }

    if (confirmDeleteButton) {
        confirmDeleteButton.addEventListener("click", async function () {
            if (conversationPendingDelete === null) {
                return;
            }

            const conversationId = conversationPendingDelete;

            this.disabled = true;

            this.textContent = "Удаление...";

            const success = await deleteConversation(conversationId);

            if (success) {
                closeDeleteConversationModal();

                return;
            }

            this.disabled = false;

            this.textContent = "Да, удалить";
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

        const modal = document.getElementById("deleteConversationModal");

        if (modal?.classList.contains("is-open")) {
            closeDeleteConversationModal();
        }
    });
}
