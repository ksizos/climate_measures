import { escapeHtml } from "./utils.js";

// Прокрутка чата вниз
export function scrollToBottom() {
    const chatMessages = document.getElementById("chatMessages");

    if (!chatMessages) {
        return;
    }

    requestAnimationFrame(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });
}

// Прокрутка к конкретному элементу
export function scrollToElement(element) {
    if (!element) {
        return;
    }

    requestAnimationFrame(() => {
        element.scrollIntoView({
            behavior: "smooth",
            block: "nearest",
        });
    });
}

// Показать ошибку
export function showError(message) {
    const errorDiv = document.getElementById("error");

    const errorMessage = document.getElementById("errorMessage");

    if (!errorDiv || !errorMessage) {
        return;
    }

    errorMessage.textContent = message;

    errorDiv.classList.remove("d-none");

    setTimeout(() => {
        hideError();
    }, 5000);
}

// Скрыть ошибку
export function hideError() {
    const errorDiv = document.getElementById("error");

    if (errorDiv) {
        errorDiv.classList.add("d-none");
    }
}

// Временное уведомление
export function showTemporaryMessage(message, type = "info") {
    const climateMain = document.querySelector(".climate-main");

    if (!climateMain) {
        return;
    }

    const messageDiv = document.createElement("div");

    messageDiv.className = `alert alert-${type} temporary-message`;

    messageDiv.innerHTML = `
        <i class="fas fa-info-circle me-2"></i>
        ${escapeHtml(message)}
    `;

    climateMain.appendChild(messageDiv);

    setTimeout(() => {
        messageDiv.classList.add("fade-out");

        setTimeout(() => {
            messageDiv.remove();
        }, 300);
    }, 3000);
}

export function hideWelcome() {
    const welcome = document.getElementById("welcomeMessage");
    const chatContainer = document.querySelector(".chat-container");

    if (welcome) {
        welcome.classList.add("d-none");
    }

    if (chatContainer) {
        chatContainer.classList.remove("d-none");
    }
}

export function showWelcome() {
    const welcome = document.getElementById("welcomeMessage");
    const chatContainer = document.querySelector(".chat-container");

    if (chatContainer) {
        chatContainer.classList.add("d-none");
    }

    if (welcome) {
        welcome.classList.remove("d-none");

        welcome.classList.remove("welcome-appear");

        void welcome.offsetWidth;

        welcome.classList.add("welcome-appear");
    }
}
