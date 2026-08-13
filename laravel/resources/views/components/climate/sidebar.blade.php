<aside id="sidebar" class="sidebar">
    <div class="sidebar-toggle-wrapper">
        <button
            type="button"
            class="aside_img_block shadow-sm"
            id="sidebarToggleButton"
            aria-label="Свернуть боковую панель"
            aria-expanded="true">

            <img
                id="sidebarToggle"
                class="aside_img"
                src="{{ asset('icons/arrow.svg') }}"
                alt="">
        </button>
    </div>

    <div class="sidebar-content">
        <div class="d-flex flex-column justify-content-between h-100">
            <div>

                <div class="sidebar-header mb-4">
                    <a
                        href="{{ route('climate.index') }}"
                        class="logo d-flex align-items-center justify-content-center">

                        <img
                            class="logo_img"
                            src="{{ asset('icons/logo.svg') }}"
                            alt="Лого">
                    </a>
                </div>

                <div class="d-flex justify-content-between align-items-center mb-3">

                    <div
                        class="d-flex align-items-center justify-content-start gap-3 new-chat-block shadow-sm">

                        <img
                            class="new-chat-btn"
                            src="{{ asset('icons/plus.svg') }}"
                            alt="Создать">

                        <p class="new-chat-text m-0 p-0">
                            Новый диалог
                        </p>
                    </div>

                    <div class="filter-wrapper">

                        <button
                            type="button"
                            class="filter-block shadow-sm"
                            popovertarget="filterPanel"
                            style="anchor-name: --filter-button;"
                            aria-label="Фильтр">

                            <img
                                class="filter-btn"
                                src="{{ asset('icons/filter.svg') }}"
                                alt="Фильтр">
                        </button>

                        <div
                            id="filterPanel"
                            class="filter-panel p-2"
                            popover="auto"
                            style="position-anchor: --filter-button;">

                            <p class="filter_header mb-3">
                                Настройки истории
                            </p>

                            <div class="filter-sort d-flex align-items-stretch justify-content-start flex-column">

                                <label
                                    for="conversationSort"
                                    class="filter-sort__label mb-1">
                                    Сортировка
                                </label>

                                <select
                                    id="conversationSort"
                                    class="filter-sort__select px-3 py-2">

                                    <option value="new">
                                        Сначала новые
                                    </option>

                                    <option value="old">
                                        Сначала старые
                                    </option>
                                </select>

                                <button
                                    type="button"
                                    class="filter_button d-flex align-items-center justify-content-center gap-2 mt-3 px-3 py-2">

                                    <img
                                        class="filter-btn-img"
                                        src="{{ asset('icons/delete.svg') }}"
                                        alt="">

                                    Очистить всю историю
                                </button>

                            </div>
                        </div>
                    </div>
                </div>

                <div class="position-relative d-flex align-items-center justify-content-center mb-2">

                    <img
                        src="{{ asset('icons/search.png') }}"
                        class="search_icon position-absolute"
                        alt="Поиск">

                    <input
                        type="search"
                        class="search w-100 m-0"
                        placeholder="Поиск в истории...">
                </div>

                <div class="scroll_container"></div>
            </div>

            <a
                href="https://clck.ru/3Rti7j"
                class="help-text m-0 p-0"
                target="_blank"
                rel="noopener noreferrer">

                <div class="help_button ps-2 py-2 d-flex justify-content-start align-items-center gap-2">

                    <img
                        class="input_img"
                        src="{{ asset('icons/question.svg') }}"
                        alt="">

                    Помощь
                </div>
            </a>
        </div>
    </div>
</aside>

<div
    id="deleteConversationModal"
    class="delete-modal"
    aria-hidden="true">

    <div
        class="delete-modal__backdrop"
        data-delete-modal-close>
    </div>

    <div
        class="delete-modal__dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="deleteConversationTitle">

        <div class="delete-modal__icon">
            <img
                src="{{ asset('icons/delete.svg') }}"
                alt="">
        </div>

        <h3
            id="deleteConversationTitle"
            class="delete-modal__title">
            Удалить диалог?
        </h3>

        <p class="delete-modal__text">
            Вы уверены, что хотите удалить этот диалог?
            Это действие нельзя отменить.
        </p>

        <div class="delete-modal__actions">

            <button
                type="button"
                id="cancelDeleteConversation"
                class="delete-modal__button delete-modal__button--cancel">

                Нет
            </button>

            <button
                type="button"
                id="confirmDeleteConversation"
                class="delete-modal__button delete-modal__button--confirm">

                Да, удалить
            </button>

        </div>

    </div>
</div>
