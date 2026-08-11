import { state } from "./state.js";

import { escapeHtml, addTargetBlankToLinks } from "./utils.js";

import { scrollToBottom, scrollToElement, hideWelcome } from "./ui.js";

import { exportToDocx, exportToExcel } from "./export.js";

import { sendApprovedMeasure, addApproveButtonsToTables } from "./measure.js";

import { loadConversations } from "./conversations.js";

let currentRequestController = null;
let isGenerating = false;

/**
 * Инициализация чата.
 */
export function initChat() {
    const questionInput = document.getElementById("question");

    const submitBtn = document.getElementById("submitBtn");

    if (!questionInput || !submitBtn) {
        return;
    }

    /**
     * Автоматическое изменение высоты textarea
     * + управление доступностью кнопки.
     */
    questionInput.addEventListener("input", function () {
        this.style.height = "auto";

        this.style.height = Math.min(this.scrollHeight, 150) + "px";

        if (!isGenerating) {
            submitBtn.disabled = !this.value.trim();
        }
    });

    /**
     * Ctrl + Enter / Cmd + Enter
     */
    questionInput.addEventListener("keydown", (event) => {
        if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
            event.preventDefault();

            if (!isGenerating) {
                sendMessage();
            }
        }
    });

    /**
     * Обычная отправка / остановка запроса.
     */
    submitBtn.addEventListener("click", () => {
        if (isGenerating) {
            stopGeneration();
            return;
        }

        sendMessage();
    });

    questionInput.focus();
}

/**
 * Переключение состояния кнопки:
 *
 * submit.svg
 *     ↓
 * stop.svg
 *     ↓
 * submit.svg
 */
function setGeneratingState(generating) {
    const submitBtn = document.getElementById("submitBtn");

    const submitIcon = submitBtn?.querySelector("img");

    const questionInput = document.getElementById("question");

    if (!submitBtn || !submitIcon) {
        return;
    }

    isGenerating = generating;

    if (generating) {
        // Кнопка STOP должна оставаться кликабельной.
        submitBtn.disabled = false;

        submitIcon.src = "/icons/stop.svg";

        submitIcon.alt = "Остановить";

        submitBtn.title = "Остановить генерацию";

        submitBtn.classList.add("is-generating");

        return;
    }

    submitIcon.src = "/icons/submit.svg";

    submitIcon.alt = "Отправить";

    submitBtn.title = "Отправить";

    submitBtn.classList.remove("is-generating");

    submitBtn.disabled = !questionInput?.value.trim();
}

/**
 * Остановка текущего клиентского запроса.
 *
 * Пока останавливается fetch Laravel.
 * Python отдельно не прерываем.
 */
function stopGeneration() {
    if (!isGenerating || !currentRequestController) {
        return;
    }

    currentRequestController.abort();
}

/**
 * Очистка сообщений чата.
 */
export function clearChatMessages() {
    const chatMessages = document.getElementById("chatMessages");

    if (!chatMessages) {
        return;
    }

    chatMessages.innerHTML = "";
}

/**
 * Добавление пары:
 *
 * пользователь
 * ассистент
 */
export function addQuestionAnswerPair(question, answer) {
    const chatMessages = document.getElementById("chatMessages");

    if (!chatMessages) {
        return {
            questionDiv: null,
            answerDiv: null,
        };
    }

    /*
     * Сообщение пользователя
     */
    const questionDiv = document.createElement("div");

    questionDiv.className = "message user-message fade-in";

    questionDiv.innerHTML = `
        <div class="message-content">
            ${escapeHtml(question)}
        </div>
    `;

    chatMessages.appendChild(questionDiv);

    /*
     * Сообщение ассистента
     */
    const answerDiv = document.createElement("div");

    answerDiv.className = "message assistant-message fade-in mt-2";

    chatMessages.appendChild(answerDiv);

    /*
     * Markdown.
     *
     * ВАЖНО:
     * markdown-content присутствует сразу.
     */
    const markdownHTML = marked.parse(answer || "");

    const safeHTML = addTargetBlankToLinks(markdownHTML);

    answerDiv.innerHTML = `
        <div class="message-content markdown-content">
            ${safeHTML}
        </div>
    `;

    /*
     * Если это уже сохранённый ответ,
     * сразу добавляем действия для таблиц.
     */
    setupAnswerActions(answerDiv);

    scrollToBottom();

    return {
        questionDiv,
        answerDiv,
    };
}

/**
 * Добавляет к ответу:
 *
 * - кнопки DOCX / Excel;
 * - кнопки одобрения мероприятий;
 * - обработчики экспорта.
 */
function setupAnswerActions(answerDiv) {
    if (!answerDiv) {
        return;
    }

    const markdownContent = answerDiv.querySelector(".markdown-content");

    if (!markdownContent) {
        return;
    }

    const tables = markdownContent.querySelectorAll("table");

    if (tables.length === 0) {
        return;
    }

    /*
     * Не создаём кнопки повторно.
     */
    if (answerDiv.querySelector(".export-buttons")) {
        return;
    }

    const exportButtonsDiv = document.createElement("div");

    exportButtonsDiv.className = "export-buttons mt-2 d-flex gap-2";

    exportButtonsDiv.innerHTML = `
    <button
        type="button"
        class="btn btn-sm btn-outline-primary export-docx"
        title="Скачать DOCX"
    >
        <i class="fas fa-file-word me-1"></i>
        DOCX
    </button>

    <button
        type="button"
        class="btn btn-sm btn-outline-success export-excel"
        title="Скачать Excel"
    >
        <i class="fas fa-file-excel me-1"></i>
        Excel
    </button>
`;

    answerDiv.appendChild(exportButtonsDiv);

    /*
     * Добавляем кнопки подтверждения
     * адаптационных мероприятий.
     */
    addApproveButtonsToTables(answerDiv);

    /*
     * DOCX
     */
    const exportDocxBtn = answerDiv.querySelector(".export-docx");

    if (exportDocxBtn) {
        exportDocxBtn.addEventListener("click", (event) => {
            event.preventDefault();
            event.stopPropagation();

            const tableHtml = markdownContent.innerHTML;

            exportToDocx(
                tableHtml,
                `dialog_${state.currentConversationId}_tables.docx`,
                exportDocxBtn,
            );
        });
    }

    /*
     * Excel
     */
    const exportExcelBtn = answerDiv.querySelector(".export-excel");

    if (exportExcelBtn) {
        exportExcelBtn.addEventListener("click", (event) => {
            event.preventDefault();
            event.stopPropagation();

            const tableHtml = markdownContent.innerHTML;

            exportToExcel(
                tableHtml,
                `dialog_${state.currentConversationId}_tables.xlsx`,
                exportExcelBtn,
            );
        });
    }
}

/**
 * Отправка сообщения.
 */
async function sendMessage() {
    /*
     * Не разрешаем отправить второй запрос,
     * пока выполняется текущий.
     */
    if (isGenerating) {
        return;
    }

    const questionInput = document.getElementById("question");

    if (!questionInput) {
        return;
    }

    const question = questionInput.value.trim();

    if (!question) {
        return;
    }

    hideWelcome();

    state.lastQuestion = question;

    /*
     * Добавляем вопрос и пустой
     * assistant-message.
     */
    const pairElements = addQuestionAnswerPair(question, "");

    if (!pairElements.questionDiv || !pairElements.answerDiv) {
        return;
    }

    /*
     * Спиннер.
     *
     * ВАЖНО:
     * markdown-content НЕ удаляем.
     */
    pairElements.answerDiv.innerHTML = `
        <div
            class="message-content markdown-content processing-content"
        >
            <span
                class="spinner-border spinner-border-sm"
                role="status"
                aria-hidden="true"
            ></span>
        </div>
    `;

    scrollToElement(pairElements.questionDiv);

    /*
     * Очищаем textarea.
     */
    questionInput.value = "";
    questionInput.style.height = "auto";

    /*
     * Создаём контроллер отмены.
     */
    currentRequestController = new AbortController();

    /*
     * submit.svg -> stop.svg
     */
    setGeneratingState(true);

    try {
        const payload = {
            question: question,
        };

        if (state.currentConversationId) {
            payload.conversation_id = state.currentConversationId;
        }

        const response = await fetch("/climate/ask", {
            method: "POST",

            headers: {
                "Content-Type": "application/json",

                "X-CSRF-TOKEN": document.querySelector(
                    'meta[name="csrf-token"]',
                ).content,

                "X-Requested-With": "XMLHttpRequest",
            },

            body: JSON.stringify(payload),

            signal: currentRequestController.signal,
        });

        const data = await response.json();

        /*
         * Успешный ответ Laravel.
         */
        if (data.success) {
            if (data.conversation_id) {
                state.currentConversationId = data.conversation_id;
            }

            const messageContent =
                pairElements.answerDiv.querySelector(".message-content");

            if (messageContent) {
                /*
                 * Спиннер больше не нужен.
                 */
                messageContent.classList.remove("processing-content");

                /*
                 * Явно гарантируем наличие
                 * markdown-content.
                 */
                messageContent.classList.add("markdown-content");

                /*
                 * Рендерим Markdown.
                 */
                const markdownHTML = marked.parse(data.answer || "");

                const safeHTML = addTargetBlankToLinks(markdownHTML);

                messageContent.innerHTML = safeHTML;
            }

            /*
             * Теперь .markdown-content
             * точно существует,
             * поэтому таблицы будут найдены.
             */
            setupAnswerActions(pairElements.answerDiv);

            scrollToElement(pairElements.answerDiv);

            /*
             * Обновляем историю диалогов.
             */
            loadConversations();

            return;
        }

        /*
         * Laravel вернул success=false.
         */
        const messageContent =
            pairElements.answerDiv.querySelector(".message-content");

        if (messageContent) {
            messageContent.classList.remove("processing-content");

            messageContent.classList.add("markdown-content");

            messageContent.innerHTML = `
                <span class="text-danger">
                    ${escapeHtml(data.error || "Неизвестная ошибка")}
                </span>
            `;
        }
    } catch (err) {
        /*
         * Пользователь нажал STOP.
         *
         * Никакого текста
         * "Генерация остановлена".
         *
         * Незавершённый assistant-message
         * просто удаляется.
         */
        if (err.name === "AbortError") {
            pairElements.answerDiv?.remove();

            return;
        }

        /*
         * Остальные ошибки показываем
         * прямо внутри assistant-message.
         */
        const messageContent =
            pairElements.answerDiv?.querySelector(".message-content");

        if (messageContent) {
            messageContent.classList.remove("processing-content");

            messageContent.classList.add("markdown-content");

            messageContent.innerHTML = `
                <span class="text-danger">
                    Ошибка:
                    ${escapeHtml(err.message)}
                </span>
            `;
        }
    } finally {
        /*
         * Всегда возвращаем:
         *
         * stop.svg -> submit.svg
         */
        currentRequestController = null;

        setGeneratingState(false);
    }
}

/**
 * Карточки примеров на welcome-screen.
 *
 * При клике:
 * - помещаем запрос в textarea;
 * - сразу отправляем.
 */
document.querySelectorAll(".example_card").forEach((card) => {
    card.addEventListener("click", () => {
        const question = card.dataset.question;

        const questionInput = document.getElementById("question");

        if (!questionInput || !question || isGenerating) {
            return;
        }

        questionInput.value = question;

        sendMessage();
    });
});
