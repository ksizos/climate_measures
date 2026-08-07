import { initChat } from "./chat.js";

import { initConversations, loadConversations } from "./conversations.js";

import { initSidebar } from "./sidebar.js";

import { checkServiceStatus } from "./status.js";

import { scrollToBottom } from "./ui.js";

marked.setOptions({
    breaks: true,
    gfm: true,
});

document.addEventListener("DOMContentLoaded", async () => {
    initSidebar();
    initChat();
    initConversations();

    await loadConversations();
    await checkServiceStatus();

    scrollToBottom();
});
