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

// Начать новый диалог
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

// Загрузка конкретного диалога
export async function loadConversation(id) {
    try {
        hideError();

        const response = await fetch(`/climate/conversation/${id}`);

        const data = await response.json();

        if (!data.success) {
            showError("Не удалось загрузить диалог");
            return;
        }

        // Запоминаем текущий открытый диалог
        state.currentConversationId = id;

        // Обновляем active в sidebar
        updateActiveConversation();

        hideWelcome();

        clearChatMessages();

        if (data.conversation && data.conversation.messages) {
            data.conversation.messages.forEach((pair) => {
                addQuestionAnswerPair(pair.question, pair.answer);
            });
        }

        scrollToBottom();
    } catch (error) {
        showError("Ошибка при загрузке диалога: " + error.message);
    }
}

// Удаление диалога
export async function deleteConversation(id) {
    if (
        !confirm(
            "Вы уверены, что хотите удалить этот диалог? Это действие нельзя отменить.",
        )
    ) {
        return;
    }

    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]');

        const response = await fetch(`/climate/conversation/${id}`, {
            method: "DELETE",

            headers: {
                "X-CSRF-TOKEN": csrfToken?.content ?? "",

                "X-Requested-With": "XMLHttpRequest",

                "Content-Type": "application/json",
            },
        });

        const data = await response.json();

        if (data.success) {
            if (String(state.currentConversationId) === String(id)) {
                state.currentConversationId = null;

                clearChatMessages();

                showWelcome();
            }

            await loadConversations();
        } else {
            showError(
                "Не удалось удалить диалог: " +
                    (data.error || "Неизвестная ошибка"),
            );
        }
    } catch (error) {
        showError("Ошибка при удалении диалога: " + error.message);
    }
}

// Переключение режима корзины
export function toggleTrashMode() {
    state.isTrashMode = !state.isTrashMode;

    loadConversations();

    const binIcon = document.querySelector(".bin-icon");

    if (binIcon) {
        binIcon.style.filter = state.isTrashMode
            ? "invert(25%) sepia(94%) saturate(5072%) hue-rotate(358deg) brightness(102%) contrast(103%)"
            : "";
    }
}

// Загрузка списка диалогов
export async function loadConversations() {
    try {
        const response = await fetch("/climate/conversations");

        const data = await response.json();

        if (data.success) {
            renderConversations(data.conversations);
        }
    } catch (error) {
        console.error("Ошибка загрузки диалогов:", error);

        showError("Ошибка загрузки истории диалогов");
    }
}

// Отображение списка диалогов
function renderConversations(conversations) {
    const scrollContainer = document.querySelector(".scroll_container");

    if (!scrollContainer) {
        return;
    }

    const today = new Date();

    const yesterday = new Date();

    yesterday.setDate(today.getDate() - 1);

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

        if (!day || !month || !year || !hours || !minutes) {
            return null;
        }

        return new Date(year, month - 1, day, hours, minutes);
    }

    const todayConvs = [];
    const yesterdayConvs = [];
    const olderConvs = [];

    conversations.forEach((conv) => {
        const interactionDate = parseRussianDate(conv.last_interaction_at);

        const now = new Date();

        if (!interactionDate) {
            olderConvs.push(conv);
            return;
        }

        const isToday =
            interactionDate.getDate() === now.getDate() &&
            interactionDate.getMonth() === now.getMonth() &&
            interactionDate.getFullYear() === now.getFullYear();

        const isYesterday =
            interactionDate.getDate() === yesterday.getDate() &&
            interactionDate.getMonth() === yesterday.getMonth() &&
            interactionDate.getFullYear() === yesterday.getFullYear();

        if (isToday) {
            todayConvs.push(conv);
        } else if (isYesterday) {
            yesterdayConvs.push(conv);
        } else {
            olderConvs.push(conv);
        }
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
                    style="border: none;"
                    class="btn btn-sm btn-outline-secondary exit-trash-mode"
                    title="Выйти из режима удаления"
                >
                    <i class="fas fa-times"></i>
                    x
                </button>
            </div>
        `;
    }

    if (todayConvs.length > 0) {
        html += `
            <h2 class="scroll_header mt-2 mb-0 me-0 ms-0">
                Сегодня
            </h2>
        `;

        todayConvs.forEach((conv) => {
            html += createConversationHTML(conv);
        });
    }

    if (yesterdayConvs.length > 0) {
        html += `
            <h2 class="scroll_header mt-3 mb-0 me-0 ms-0">
                Вчера
            </h2>
        `;

        yesterdayConvs.forEach((conv) => {
            html += createConversationHTML(conv);
        });
    }

    if (olderConvs.length > 0) {
        html += `
            <h2 class="scroll_header mt-3 mb-0 me-0 ms-0">
                Ранее
            </h2>
        `;

        olderConvs.forEach((conv) => {
            html += createConversationHTML(conv);
        });
    }

    scrollContainer.innerHTML =
        html ||
        `
            <p class="text-muted text-center mt-3">
                Нет диалогов
            </p>
        `;

    /*
     * На случай перерендера sidebar.
     *
     * createConversationHTML уже добавляет active,
     * но дополнительно синхронизируем DOM.
     */
    updateActiveConversation();

    // Обработчики клика по диалогам
    document.querySelectorAll(".conversation-item").forEach((item) => {
        item.addEventListener("click", function (event) {
            // Клик по настройкам не открывает диалог
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

            // Диалог уже открыт — ничего не делаем
            if (String(state.currentConversationId) === String(id)) {
                return;
            }

            loadConversation(id);
        });
    });

    // Обработчики удаления старого trash-mode
    document.querySelectorAll(".delete-conversation").forEach((btn) => {
        btn.addEventListener("click", function (event) {
            event.stopPropagation();

            const id = this.getAttribute("data-id");

            if (!id) {
                return;
            }

            deleteConversation(id);
        });
    });

    // Выход из режима корзины
    const exitBtn = document.querySelector(".exit-trash-mode");

    if (exitBtn) {
        exitBtn.addEventListener("click", function (event) {
            event.stopPropagation();

            state.isTrashMode = false;

            loadConversations();

            const binIcon = document.querySelector(".bin-icon");

            if (binIcon) {
                binIcon.style.filter = "";
            }
        });
    }

    updateDeleteButtonsVisibility();
}

// Добавление класса active текущему диалогу
function updateActiveConversation() {
    const items = document.querySelectorAll(".conversation-item");

    items.forEach((item) => {
        const isActive =
            state.currentConversationId !== null &&
            String(item.dataset.id) === String(state.currentConversationId);

        item.classList.toggle("active", isActive);
    });
}

// Обновление видимости кнопок удаления
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

// Создание HTML диалога
function createConversationHTML(conv) {
    const anchorName = `--conversation-settings-${conv.id}`;

    const panelId = `conversation-settings-${conv.id}`;

    const isActive =
        state.currentConversationId !== null &&
        String(state.currentConversationId) === String(conv.id);

    return `
        <div
            class="conversation-item fade_text w-100 position-relative p-2 mb-3 rounded ${state.isTrashMode ? "trash-mode-item" : ""} ${isActive ? "active" : ""}"
            data-id="${conv.id}"
        >
            <div
                class="d-flex justify-content-between align-items-start"
            >
                <div class="flex-grow-1 me-2">
                    <p
                        class="m-0 conversation-title fw-bold mb-2"
                    >
                        ${escapeHtml(conv.title)}
                    </p>

                    ${
                        conv.last_question
                            ? `
                                <p class="m-0 small">
                                    ${escapeHtml(conv.last_question)}
                                </p>
                            `
                            : ""
                    }

                    ${
                        conv.last_answer_preview
                            ? `
                                <p class="m-0 text-muted small fst-italic">
                                    ${escapeHtml(conv.last_answer_preview)}...
                                </p>
                            `
                            : ""
                    }
                </div>

                <div class="fade_block"></div>
            </div>


            <div class="conversation-settings">
                <button
                    type="button"
                    class="settings-btn"
                    data-conversation-id="${conv.id}"
                    popovertarget="${panelId}"
                    style="anchor-name: ${anchorName};"
                    aria-label="Настройки чата"
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
                        class="conversation-settings-panel__item d-flex align-items-center justify-content-start"
                        data-action="rename"
                        data-conversation-id="${conv.id}"
                    >
                    <img src="/icons/edit.svg" class="conversation_panel_image" alt="">
                        Переименовать
                    </button>

                    <button
                        type="button"
                        class="conversation-settings-panel__item conversation-settings-panel__item--danger d-flex align-items-center justify-content-start"
                        data-action="delete"
                        data-conversation-id="${conv.id}"
                    >
                    <img src="/icons/delete.svg" class="conversation_panel_image" alt="">
                        Удалить
                    </button>
                </div>
            </div>


            <small class="text-muted d-block mt-1">
                ${escapeHtml(conv.last_interaction_at ?? "")}
            </small>
        </div>
    `;
}

// Инициализация диалогов
export function initConversations() {
    const newChatBtn = document.querySelector(".new-chat-block");

    const binIcon = document.querySelector(".bin-icon");

    if (newChatBtn) {
        newChatBtn.addEventListener("click", startNewConversation);
    }

    if (binIcon) {
        binIcon.addEventListener("click", toggleTrashMode);
    }
}
