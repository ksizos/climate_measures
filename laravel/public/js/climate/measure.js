import { state } from "./state.js";

import { showTemporaryMessage, showError } from "./ui.js";

// Отправка одобренного мероприятия
export async function sendApprovedMeasure(data) {
    try {
        const response = await fetch("/climate/approve-measure", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRF-TOKEN": document.querySelector(
                    'meta[name="csrf-token"]',
                ).content,
                "X-Requested-With": "XMLHttpRequest",
            },
            body: JSON.stringify(data),
        });
        const result = await response.json();

        if (result.success) {
            showTemporaryMessage(
                "Мероприятие добавлено в базу знаний!",
                "success",
            );
        } else {
            showError("Ошибка добавления: " + (result.error || "неизвестно"));
        }
    } catch (err) {
        showError("Ошибка отправки: " + err.message);
    }
}

// Добавление кнопок одобрения в таблицы
export function addApproveButtonsToTables(answerDiv) {
    const tables = answerDiv.querySelectorAll(".markdown-content table");
    tables.forEach((table, tableIdx) => {
        const rows = table.querySelectorAll("tbody tr");
        rows.forEach((row, rowIdx) => {
            const cells = row.querySelectorAll("td");
            if (cells.length >= 5) {
                const existingApprove = row.querySelector(".approve-measure");
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
}
