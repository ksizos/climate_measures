import { showTemporaryMessage, showError } from "./ui.js";

// Экспорт в DOCX
export function exportToDocx(content, filename) {
    const btn = document.querySelector(".export-docx");
    if (btn) {
        btn.disabled = true;
        btn.innerHTML =
            '<i class="fas fa-spinner fa-spin me-1"></i>Загрузка...';
    }

    // === ИСПРАВЛЕНИЕ: берём полный HTML ответа ===
    const answerDiv = btn.closest(".assistant-message");
    const contentDiv = answerDiv
        ? answerDiv.querySelector(".message-content")
        : null;
    const fullHtml = contentDiv ? contentDiv.innerHTML : content;

    fetch("/climate/export/docx", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRF-TOKEN": document.querySelector('meta[name="csrf-token"]')
                .content,
            "X-Requested-With": "XMLHttpRequest",
        },
        body: JSON.stringify({
            content: fullHtml, // Отправляем ВЕСЬ HTML, не только таблицы
            filename: filename,
        }),
    })
        .then((response) => {
            if (response.ok) {
                return response.blob();
            } else {
                return response.json().then((data) => {
                    throw new Error(data.error || "Ошибка при генерации файла");
                });
            }
        })
        .then((blob) => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download =
                filename ||
                "export_" +
                    new Date().toISOString().replace(/[:.]/g, "-") +
                    ".docx";
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            showTemporaryMessage("Файл DOCX успешно скачан!", "success");
        })
        .catch((error) => {
            console.error("Ошибка экспорта DOCX:", error);
            showError("Ошибка при создании DOCX файла: " + error.message);
        })
        .finally(() => {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-file-word me-1"></i>DOCX';
            }
        });
}

// Экспорт в Excel
export function exportToExcel(content, filename) {
    const btn = document.querySelector(".export-excel");
    if (btn) {
        btn.disabled = true;
        btn.innerHTML =
            '<i class="fas fa-spinner fa-spin me-1"></i>Загрузка...';
    }

    // === ИСПРАВЛЕНИЕ: берём полный HTML ответа ===
    const answerDiv = btn.closest(".assistant-message");
    const contentDiv = answerDiv
        ? answerDiv.querySelector(".message-content")
        : null;
    const fullHtml = contentDiv ? contentDiv.innerHTML : content;

    fetch("/climate/export/excel", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRF-TOKEN": document.querySelector('meta[name="csrf-token"]')
                .content,
            "X-Requested-With": "XMLHttpRequest",
        },
        body: JSON.stringify({
            content: fullHtml, // Отправляем ВЕСЬ HTML
            filename: filename,
        }),
    })
        .then((response) => {
            if (response.ok) {
                return response.blob();
            } else {
                return response.json().then((data) => {
                    throw new Error(data.error || "Ошибка при генерации файла");
                });
            }
        })
        .then((blob) => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download =
                filename ||
                "export_" +
                    new Date().toISOString().replace(/[:.]/g, "-") +
                    ".xlsx";
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            showTemporaryMessage("Файл Excel успешно скачан!", "success");
        })
        .catch((error) => {
            console.error("Ошибка экспорта Excel:", error);
            showError("Ошибка при создании Excel файла: " + error.message);
        })
        .finally(() => {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-file-excel me-1"></i>Excel';
            }
        });
}
