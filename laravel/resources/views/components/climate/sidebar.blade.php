<aside id="sidebar" class="sidebar col-md-3 col-lg-2 px-4 py-5">
    <div class="d-flex flex-column justify-content-between h-100">
        <div>
            <div class="d-flex justify-content-between align-items-center mb-4">
                <!-- <a href="#">
                    <img class="logo" src="{{ asset('icons/logo.png') }}" alt="Лого" />
                </a> -->
                <!-- СТРЕЛКА СЛЕВА -->
                <div>
                    <img
                        id="sidebarToggle"
                        class="aside_img"
                        src="{{ asset('icons/arrow.svg') }}"
                        alt="Свернуть"
                        style="cursor:pointer;" />
                </div>

                <!-- ИКОНКИ СПРАВА -->
                <div class="d-flex align-items-center gap-3">
                    <img class="aside_img bin-icon"
                        src="{{ asset('icons/bin.png') }}"
                        alt="Корзина"
                        title="Режим удаления" />

                    <img class="aside_img new-chat-btn"
                        src="{{ asset('icons/chat.png') }}"
                        alt="Новый чат"
                        title="Новый чат" />
                </div>

            </div>

            <div class="position-relative d-flex align-items-center mb-3">
                <input type="search" class="search w-100 py-0 px-2" placeholder="Поиск в истории..." />
                <img
                    src="{{ asset('icons/search.png') }}"
                    class="search_icon position-absolute"
                    alt="Поиск" />
            </div>

            <div class="scroll_container">

            </div>
        </div>

        <!-- Индикатор статуса сервиса -->
        <div class="mb-3">
            <div class="status-indicator text-center p-2 rounded">
                <small id="statusIndicator" class="text-muted">
                    <i class="fas fa-circle me-1"></i>Загрузка...
                </small>
            </div>
        </div>

        <div class="input_button px-5 py-2 d-flex justify-content-center align-items-center gap-4">
            <img class="input_img" src="{{ asset('icons/question.png') }}">
            <a href="https://clck.ru/3Rti7j" target="_blank"><input class="p-0 m-0" type="button" name="help" value="Помощь" /></a>
        </div>
    </div>
</aside>
