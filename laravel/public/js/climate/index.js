import { initChat } from "./chat.js";

import { initConversations, loadConversations } from "./conversations.js";

import { initSidebar } from "./sidebar.js";

import { scrollToBottom } from "./ui.js";

document.addEventListener("DOMContentLoaded", async () => {
    initSidebar();

    if (
        typeof marked !== "undefined" &&
        typeof marked.setOptions === "function"
    ) {
        marked.setOptions({
            breaks: true,
            gfm: true,
        });
    }

    initChat();

    initConversations();
    try {
        await loadConversations();
    } catch (error) {
        console.error("Ошибка загрузки диалогов:", error);
    }

    scrollToBottom();
});
