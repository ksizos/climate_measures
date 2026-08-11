import { showTemporaryMessage } from "./ui.js";

// Получение CSRF-токена
function getCsrfToken() {
    const token = document.querySelector('meta[name="csrf-token"]');

    return token?.content ?? "";
}

// Скачивание полученного Blob
function downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);

    const link = document.createElement("a");

    link.href = url;
    link.download = filename;

    document.body.appendChild(link);

    link.click();

    link.remove();

    window.URL.revokeObjectURL(url);
}

// Получение текста ошибки от сервера
async function getResponseError(response) {
    try {
        const contentType = response.headers.get("content-type") || "";

        if (contentType.includes("application/json")) {
            const data = await response.json();

            return (
                data.error ||
                data.message ||
                `Ошибка сервера: ${response.status}`
            );
        }

        const text = await response.text();

        return text || `Ошибка сервера: ${response.status}`;
    } catch {
        return `Ошибка сервера: ${response.status}`;
    }
}

// Экспорт в DOCX
export async function exportToDocx(content, filename, button = null) {
    if (!button) {
        console.error("Не передана кнопка экспорта DOCX");

        showTemporaryMessage("Не удалось запустить экспорт DOCX", "danger");

        return;
    }

    const originalHtml = button.innerHTML;

    button.disabled = true;

    button.innerHTML = `
        <i class="fas fa-spinner fa-spin me-1"></i>
        Загрузка...
    `;

    try {
        const answerDiv = button.closest(".assistant-message");

        const contentDiv = answerDiv
            ? answerDiv.querySelector(".message-content")
            : null;

        const fullHtml = contentDiv?.innerHTML || content;

        const response = await fetch("/climate/export/docx", {
            method: "POST",

            headers: {
                "Content-Type": "application/json",

                "X-CSRF-TOKEN": getCsrfToken(),

                "X-Requested-With": "XMLHttpRequest",
            },

            body: JSON.stringify({
                content: fullHtml,
                filename: filename,
            }),
        });

        if (!response.ok) {
            const message = await getResponseError(response);

            throw new Error(message);
        }

        const blob = await response.blob();

        const downloadFilename =
            filename ||
            `export_${new Date().toISOString().replace(/[:.]/g, "-")}.docx`;

        downloadBlob(blob, downloadFilename);

        showTemporaryMessage("Файл DOCX успешно скачан!", "success");
    } catch (error) {
        console.error("Ошибка экспорта DOCX:", error);

        showTemporaryMessage(
            `Ошибка при создании DOCX: ${error.message}`,
            "danger",
        );
    } finally {
        button.disabled = false;
        button.innerHTML = originalHtml;
    }
}

// Экспорт в Excel
export async function exportToExcel(content, filename, button = null) {
    if (!button) {
        console.error("Не передана кнопка экспорта Excel");

        showTemporaryMessage("Не удалось запустить экспорт Excel", "danger");

        return;
    }

    const originalHtml = button.innerHTML;

    button.disabled = true;

    button.innerHTML = `
        <i class="fas fa-spinner fa-spin me-1"></i>
        Загрузка...
    `;

    try {
        const answerDiv = button.closest(".assistant-message");

        const contentDiv = answerDiv
            ? answerDiv.querySelector(".message-content")
            : null;

        const fullHtml = contentDiv?.innerHTML || content;

        const response = await fetch("/climate/export/excel", {
            method: "POST",

            headers: {
                "Content-Type": "application/json",

                "X-CSRF-TOKEN": getCsrfToken(),

                "X-Requested-With": "XMLHttpRequest",
            },

            body: JSON.stringify({
                content: fullHtml,
                filename: filename,
            }),
        });

        if (!response.ok) {
            const message = await getResponseError(response);

            throw new Error(message);
        }

        const blob = await response.blob();

        const downloadFilename =
            filename ||
            `export_${new Date().toISOString().replace(/[:.]/g, "-")}.xlsx`;

        downloadBlob(blob, downloadFilename);

        showTemporaryMessage("Файл Excel успешно скачан!", "success");
    } catch (error) {
        console.error("Ошибка экспорта Excel:", error);

        showTemporaryMessage(
            `Ошибка при создании Excel: ${error.message}`,
            "danger",
        );
    } finally {
        button.disabled = false;
        button.innerHTML = originalHtml;
    }
}
