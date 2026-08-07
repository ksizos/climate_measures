import { state } from "./state.js";

import { escapeHtml, addTargetBlankToLinks } from "./utils.js";

import {
    scrollToBottom,
    scrollToElement,
    showLoading,
    hideLoading,
    showError,
    hideError,
    hideWelcome,
} from "./ui.js";

import { exportToDocx, exportToExcel } from "./export.js";

import { sendApprovedMeasure, addApproveButtonsToTables } from "./measure.js";

import { loadConversations } from "./conversations.js";

export function initChat() {
    const questionInput = document.getElementById("question");

    const submitBtn = document.getElementById("submitBtn");

    if (!questionInput || !submitBtn) {
        return;
    }

    questionInput.addEventListener("input", function () {
        this.style.height = "auto";

        this.style.height = Math.min(this.scrollHeight, 150) + "px";

        submitBtn.disabled = !this.value.trim();
    });

    questionInput.addEventListener("keydown", (event) => {
        if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
            sendMessage();
        }
    });

    submitBtn.addEventListener("click", sendMessage);

    questionInput.focus();
}

// Очистить сообщения чата
export function clearChatMessages() {
    const chatMessages = document.getElementById("chatMessages");

    if (chatMessages) {
        chatMessages.innerHTML = "";
    }
}

// Добавление пары вопрос-ответ в чат
export function addQuestionAnswerPair(question, answer) {
    const chatMessages = document.getElementById("chatMessages");

    // Вопрос пользователя
    const questionDiv = document.createElement("div");
    questionDiv.className = "message user-message fade-in";
    questionDiv.innerHTML = `<div class="message-content">${escapeHtml(question)}</div>`;
    chatMessages.appendChild(questionDiv);

    // Ответ ассистента
    const answerDiv = document.createElement("div");
    answerDiv.className = "message assistant-message fade-in mt-2";
    chatMessages.appendChild(answerDiv);

    // Убираем welcome-сообщение
    const welcomeMessage = chatMessages.querySelector(".welcome-message");
    if (welcomeMessage) {
        welcomeMessage.remove();
    }

    // Рендерим Markdown в HTML
    const markdownHTML = marked.parse(answer);
    const safeHTML = addTargetBlankToLinks(markdownHTML);
    answerDiv.innerHTML = `<div class="message-content markdown-content">${safeHTML}</div>`;

    // === ПРОВЕРЯЕМ НАЛИЧИЕ ТАБЛИЦ И ДОБАВЛЯЕМ КНОПКИ ЭКСПОРТА ===
    const tables = answerDiv.querySelectorAll(".markdown-content table");

    if (tables.length > 0) {
        // Создаём контейнер для кнопок экспорта
        const exportButtonsDiv = document.createElement("div");
        exportButtonsDiv.className = "export-buttons mt-2 d-flex gap-2";
        exportButtonsDiv.innerHTML = `
            <button class="btn btn-sm btn-outline-primary export-docx" title="Скачать DOCX">
                <i class="fas fa-file-word me-1"></i>DOCX
            </button>
            <button class="btn btn-sm btn-outline-success export-excel" title="Скачать Excel">
                <i class="fas fa-file-excel me-1"></i>Excel
            </button>
        `;
        answerDiv.appendChild(exportButtonsDiv);

        // === ДОБАВЛЯЕМ ГАЛОЧКИ В ТАБЛИЦЫ ===
        tables.forEach((table, tableIdx) => {
            const rows = table.querySelectorAll("tbody tr");
            rows.forEach((row, rowIdx) => {
                const cells = row.querySelectorAll("td");
                if (cells.length >= 5) {
                    // Проверяем, нет ли уже кнопки
                    const existingApprove =
                        row.querySelector(".approve-measure");
                    if (existingApprove) return;

                    const approveCell = document.createElement("td");
                    approveCell.innerHTML = `
                        <button class="btn btn-sm btn-success approve-measure"
                                title="Добавить в базу знаний"
                                data-table="${tableIdx}"
                                data-row="${rowIdx}">
                            <i class="fas fa-check"></i>
                             &#x2713;
                        </button>
                    `;
                    row.appendChild(approveCell);

                    // Обработчик нажатия на галочку
                    approveCell
                        .querySelector(".approve-measure")
                        .addEventListener("click", () => {
                            const rowData = Array.from(cells)
                                .slice(0, 5)
                                .map((c) => c.innerText.trim());
                            sendApprovedMeasure({
                                conversation_id: state.currentConversationId,
                                measure: {
                                    name: rowData[0],
                                    mitigation: rowData[1],
                                    adaptation: rowData[2],
                                    relevance: rowData[3],
                                    responsible: rowData[4],
                                },
                                source_question: state.lastQuestion,
                            });
                        });
                }
            });
        });

        // === ОБРАБОТЧИКИ КНОПОК ЭКСПОРТА ===
        const exportDocxBtn = answerDiv.querySelector(".export-docx");
        const exportExcelBtn = answerDiv.querySelector(".export-excel");

        if (exportDocxBtn) {
            exportDocxBtn.addEventListener("click", () => {
                // Берём весь ответ, включая ссылки после таблицы
                const answerContent =
                    answerDiv.querySelector(".message-content");
                const tableHtml =
                    answerDiv.querySelector(".markdown-content").innerHTML;
                exportToDocx(
                    tableHtml,
                    `dialog_${state.currentConversationId}_tables.docx`,
                );
            });
        }

        if (exportExcelBtn) {
            exportExcelBtn.addEventListener("click", () => {
                const tableHtml =
                    answerDiv.querySelector(".markdown-content").innerHTML;
                exportToExcel(
                    tableHtml,
                    `dialog_${state.currentConversationId}_tables.xlsx`,
                );
            });
        }
    }

    scrollToBottom();

    return { questionDiv, answerDiv };
}

// Отправка сообщения с сохранением в диалог
async function sendMessage() {
    const questionInput = document.getElementById("question");
    const question = questionInput.value.trim();
    if (!question) return;
    hideWelcome();
    state.lastQuestion = question;

    // Добавляем пару вопрос-ответ (временно, пока нет ответа)
    const pairElements = addQuestionAnswerPair(
        question,
        '<i class="text-muted">Обработка...</i>',
    );

    // Прокручиваем к сообщению пользователя
    scrollToElement(pairElements.questionDiv);

    // Очищаем поле ввода
    questionInput.value = "";
    questionInput.style.height = "auto";
    document.getElementById("submitBtn").disabled = true;

    // Показываем индикатор загрузки
    showLoading();
    hideError();

    try {
        const payload = { question: question };
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
        });
        const data = await response.json();

        if (data.success) {
            if (data.conversation_id) {
                state.currentConversationId = data.conversation_id;
            }

            // Обновляем ответ в DOM
            if (
                pairElements.answerDiv &&
                pairElements.answerDiv.querySelector(".message-content")
            ) {
                pairElements.answerDiv.querySelector(
                    ".message-content",
                ).innerHTML = marked.parse(data.answer || "");

                // === ПОВТОРНО ПРОВЕРЯЕМ ТАБЛИЦЫ ПОСЛЕ ПОЛУЧЕНИЯ ОТВЕТА ===
                const tables = pairElements.answerDiv.querySelectorAll(
                    ".markdown-content table",
                );
                if (
                    tables.length > 0 &&
                    !pairElements.answerDiv.querySelector(".export-buttons")
                ) {
                    // Удаляем временный текст загрузки
                    pairElements.answerDiv.querySelector(
                        ".message-content",
                    ).innerHTML = marked.parse(data.answer || "");

                    // Добавляем кнопки экспорта
                    const exportButtonsDiv = document.createElement("div");
                    exportButtonsDiv.className =
                        "export-buttons mt-2 d-flex gap-2";
                    exportButtonsDiv.innerHTML = `
                        <button class="btn btn-sm btn-outline-primary export-docx" title="Скачать DOCX">
                            <i class="fas fa-file-word me-1"></i>DOCX
                        </button>
                        <button class="btn btn-sm btn-outline-success export-excel" title="Скачать Excel">
                            <i class="fas fa-file-excel me-1"></i>Excel
                        </button>
                    `;
                    pairElements.answerDiv.appendChild(exportButtonsDiv);

                    // Добавляем галочки в таблицы
                    addApproveButtonsToTables(pairElements.answerDiv);

                    // Навешиваем обработчики на кнопки экспорта
                    const exportDocxBtn =
                        pairElements.answerDiv.querySelector(".export-docx");
                    const exportExcelBtn =
                        pairElements.answerDiv.querySelector(".export-excel");

                    if (exportDocxBtn) {
                        exportDocxBtn.addEventListener("click", () => {
                            const tableHtml =
                                pairElements.answerDiv.querySelector(
                                    ".markdown-content",
                                ).innerHTML;
                            exportToDocx(
                                tableHtml,
                                `dialog_${state.currentConversationId}_tables.docx`,
                            );
                        });
                    }

                    if (exportExcelBtn) {
                        exportExcelBtn.addEventListener("click", () => {
                            const tableHtml =
                                pairElements.answerDiv.querySelector(
                                    ".markdown-content",
                                ).innerHTML;
                            exportToExcel(
                                tableHtml,
                                `dialog_${state.currentConversationId}_tables.xlsx`,
                            );
                        });
                    }
                }
            }

            scrollToElement(pairElements.answerDiv);
            loadConversations();
        } else {
            if (
                pairElements.answerDiv &&
                pairElements.answerDiv.querySelector(".message-content")
            ) {
                pairElements.answerDiv.querySelector(
                    ".message-content",
                ).innerHTML =
                    `<span class="text-danger">${data.error || "Неизвестная ошибка"}</span>`;
            }
            showError(data.error || "Неизвестная ошибка при получении ответа");
        }
    } catch (err) {
        if (
            pairElements.answerDiv &&
            pairElements.answerDiv.querySelector(".message-content")
        ) {
            pairElements.answerDiv.querySelector(".message-content").innerHTML =
                `<span class="text-danger">Ошибка: ${err.message}</span>`;
        }
        showError("Произошла ошибка при отправке запроса: " + err.message);
    } finally {
        hideLoading();
    }
}

document.querySelectorAll(".example_card").forEach((card) => {
    card.addEventListener("click", () => {
        const question = card.dataset.question + " - адаптационные мероприятия";
        const questionInput = document.getElementById("question");

        if (!questionInput || !question) {
            return;
        }

        // Записываем текст карточки в обычное поле ввода
        questionInput.value = question;

        sendMessage();
    });
});
