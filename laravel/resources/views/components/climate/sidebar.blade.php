<aside id="sidebar" class="sidebar col-md-3 col-lg-2">
    <div class="sidebar-toggle-wrapper">
        <button
            type="button"
            class="aside_img_block shadow-sm"
            id="sidebarToggleButton"
            aria-label="Свернуть боковую панель">
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
                    <a href="#" class="logo d-flex align-items-center justify-content-center">
                        <img
                            class="logo_img"
                            src="{{ asset('icons/logo.svg') }}"
                            alt="Лого" />
                    </a>
                </div>

                <div class="d-flex justify-content-between align-items-center mb-3">
                    <div class="d-flex align-items-center justify-content-start gap-3 new-chat-block shadow-sm">
                        <img
                            class="new-chat-btn"
                            src="{{ asset('icons/plus.svg') }}"
                            alt="Создать" />

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
                            class="filter-panel"
                            popover="auto"
                            style="position-anchor: --filter-button;">
                            <button
                                type="button"
                                class="filter-panel__item"
                                data-filter="all">
                                Все диалоги
                            </button>

                            <button
                                type="button"
                                class="filter-panel__item"
                                data-filter="today">
                                Сегодня
                            </button>

                            <button
                                type="button"
                                class="filter-panel__item"
                                data-filter="yesterday">
                                Вчера
                            </button>

                            <button
                                type="button"
                                class="filter-panel__item"
                                data-filter="older">
                                Ранее
                            </button>
                        </div>
                    </div>
                </div>

                <div class="position-relative d-flex align-items-center justify-content-center mb-4">
                    <img
                        src="{{ asset('icons/search.png') }}"
                        class="search_icon position-absolute"
                        alt="Поиск" />

                    <input
                        type="search"
                        class="search w-100 m-0"
                        placeholder="Поиск в истории..." />
                </div>

                <div class="scroll_container"></div>
            </div>

            <a
                href="https://clck.ru/3Rti7j"
                class="help-text m-0 p-0"
                target="_blank">
                <div class="help_button ps-2 py-2 d-flex justify-content-start align-items-center gap-2">
                    <img
                        class="input_img"
                        src="{{ asset('icons/question.svg') }}">

                    Помощь
                </div>
            </a>
        </div>
    </div>
</aside>
