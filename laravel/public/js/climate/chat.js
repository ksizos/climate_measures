import { state } from "./state.js";

import { escapeHtml, addTargetBlankToLinks } from "./utils.js";

import { scrollToBottom, scrollToElement, hideWelcome } from "./ui.js";

import { exportToDocx, exportToExcel } from "./export.js";

import { addApproveButtonsToTables } from "./measure.js";

import { loadConversations } from "./conversations.js";

let currentRequestController = null;

let currentRequestId = null;

let currentAnswerElement = null;

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
     * Автоматическая высота textarea
     * + состояние submit.
     */
    questionInput.addEventListener("input", function () {
        this.style.height = "auto";

        this.style.height = Math.min(this.scrollHeight, 150) + "px";

        if (!isGenerating) {
            submitBtn.disabled = !this.value.trim();
        }
    });

    /**
     * Ctrl + Enter / Cmd + Enter.
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
     * Отправка / остановка.
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
 * Уникальный ID конкретной генерации.
 */
function createRequestId() {
    if (
        typeof crypto !== "undefined" &&
        typeof crypto.randomUUID === "function"
    ) {
        return crypto.randomUUID();
    }

    return Date.now().toString(36) + "-" + Math.random().toString(36).slice(2);
}

/**
 * submit.svg <-> stop.svg
 */
function setGeneratingState(generating) {
    const submitBtn = document.getElementById("submitBtn");

    const questionInput = document.getElementById("question");

    if (!submitBtn) {
        return;
    }

    isGenerating = generating;

    if (generating) {
        /*
         * Кнопка STOP должна оставаться
         * доступной во время генерации.
         */
        submitBtn.disabled = false;

        submitBtn.classList.add("is-generating");

        submitBtn.title = "Остановить генерацию";

        return;
    }

    submitBtn.classList.remove("is-generating");

    submitBtn.title = "Отправить";

    submitBtn.disabled = !questionInput?.value.trim();
}
/**
 * Отправляет серверу команду STOP.
 *
 * Ошибки здесь намеренно игнорируются:
 * пользователь не должен видеть
 * уведомлений при остановке.
 */
async function cancelServerGeneration(requestId) {
    if (!requestId) {
        return;
    }

    const csrfToken = document.querySelector(
        'meta[name="csrf-token"]',
    )?.content;

    try {
        await fetch("/climate/cancel", {
            method: "POST",

            headers: {
                "Content-Type": "application/json",

                "X-CSRF-TOKEN": csrfToken,

                "X-Requested-With": "XMLHttpRequest",
            },

            body: JSON.stringify({
                request_id: requestId,
            }),
        });
    } catch {
        /*
         * Ошибка остановки
         * не выводится пользователю.
         */
    }
}

/**
 * Немедленная остановка генерации.
 */
async function stopGeneration() {
    if (!isGenerating) {
        return;
    }

    /*
     * Запоминаем значения именно
     * отменяемого запроса.
     */
    const requestId = currentRequestId;

    const controller = currentRequestController;

    const answerElement = currentAnswerElement;

    /*
     * Сразу помечаем запрос
     * остановленным.
     *
     * Это важно, чтобы старый запрос
     * больше не считался активным
     * на клиенте.
     */
    currentRequestId = null;

    currentRequestController = null;

    currentAnswerElement = null;

    /*
     * Сразу возвращаем кнопку
     * в состояние submit.
     */
    setGeneratingState(false);

    /*
     * Вместо удаления сообщения
     * показываем статус остановки.
     */
    if (answerElement) {
        const messageContent = answerElement.querySelector(".message-content");

        if (messageContent) {
            messageContent.classList.remove("processing-content");

            messageContent.innerHTML = `
                <span class="generation-stopped">
                    Генерация остановлена
                </span>
            `;
        }
    }

    /*
     * Сначала отправляем серверу
     * настоящую команду отмены.
     *
     * ВАЖНО:
     * browser fetch /ask пока ещё
     * не прерываем, чтобы Laravel
     * успел выполнить /cancel.
     */
    await cancelServerGeneration(requestId);

    /*
     * После отправки STOP
     * разрываем старый /ask.
     */
    if (controller) {
        controller.abort();
    }

    const questionInput = document.getElementById("question");

    questionInput?.focus();
}

/**
 * Очистка сообщений.
 */
export function clearChatMessages() {
    const chatMessages = document.getElementById("chatMessages");

    if (!chatMessages) {
        return;
    }

    chatMessages.innerHTML = "";
}

/**
 * Добавление вопроса + ответа.
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
     * Пользователь.
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
     * Ассистент.
     */
    const answerDiv = document.createElement("div");

    answerDiv.className = "message assistant-message fade-in mt-2";

    chatMessages.appendChild(answerDiv);

    const markdownHTML = marked.parse(answer || "");

    const safeHTML = addTargetBlankToLinks(markdownHTML);

    answerDiv.innerHTML = `
        <div
            class="message-content markdown-content"
        >
            ${safeHTML}
        </div>
    `;

    setupAnswerActions(answerDiv);

    scrollToBottom();

    return {
        questionDiv,
        answerDiv,
    };
}

/**
 * Действия над таблицами ответа.
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

    addApproveButtonsToTables(answerDiv);

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

    const pairElements = addQuestionAnswerPair(question, "");

    if (!pairElements.questionDiv || !pairElements.answerDiv) {
        return;
    }

    /*
     * Текущее незавершённое
     * сообщение ассистента.
     */
    currentAnswerElement = pairElements.answerDiv;

    pairElements.answerDiv.innerHTML = `
        <div
            class="
                message-content
                markdown-content
                processing-content
            "
        >
            <span
                class="
                    spinner-border
                    spinner-border-sm
                "
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
     * Уникальный запрос.
     */
    const requestId = createRequestId();

    currentRequestId = requestId;

    /*
     * AbortController относится
     * только к этому запросу.
     */
    const controller = new AbortController();

    currentRequestController = controller;

    setGeneratingState(true);

    try {
        const payload = {
            question: question,

            request_id: requestId,
        };

        if (state.currentConversationId) {
            payload.conversation_id = state.currentConversationId;
        }

        const csrfToken = document.querySelector(
            'meta[name="csrf-token"]',
        )?.content;

        const response = await fetch("/climate/ask", {
            method: "POST",

            headers: {
                "Content-Type": "application/json",

                "X-CSRF-TOKEN": csrfToken,

                "X-Requested-With": "XMLHttpRequest",
            },

            body: JSON.stringify(payload),

            signal: controller.signal,
        });

        /*
         * Если запрос уже остановлен,
         * ничего больше не рендерим.
         */
        if (currentRequestId !== requestId) {
            return;
        }

        const data = await response.json();

        if (currentRequestId !== requestId) {
            return;
        }

        if (data.success) {
            if (data.conversation_id) {
                state.currentConversationId = data.conversation_id;
            }

            const messageContent =
                pairElements.answerDiv.querySelector(".message-content");

            if (messageContent) {
                messageContent.classList.remove("processing-content");

                messageContent.classList.add("markdown-content");

                const markdownHTML = marked.parse(data.answer || "");

                const safeHTML = addTargetBlankToLinks(markdownHTML);

                messageContent.innerHTML = safeHTML;
            }

            setupAnswerActions(pairElements.answerDiv);

            scrollToElement(pairElements.answerDiv);

            loadConversations();

            return;
        }

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
         * STOP.
         *
         * Без текста,
         * без alert,
         * без сообщения.
         */
        if (err.name === "AbortError") {
            return;
        }

        /*
         * Если это уже не текущий
         * request — игнорируем.
         */
        if (currentRequestId !== requestId) {
            return;
        }

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
         * Очень важно:
         *
         * старый остановленный request
         * не должен сбросить состояние
         * уже нового запроса.
         */
        if (currentRequestId === requestId) {
            currentRequestId = null;

            currentRequestController = null;

            currentAnswerElement = null;

            setGeneratingState(false);
        }
    }
}

/**
 * Карточки примеров.
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
