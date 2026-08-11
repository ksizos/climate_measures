<header class="d-flex justify-content-end align-items-center">

    <div
        class="profile-dropdown"
        id="profile-fixed">

        <button
            type="button"
            class="profile-trigger"
            aria-label="Открыть профиль">

            <img
                class="profile-avatar"
                src="{{ asset('icons/account.svg') }}"
                alt="Личный кабинет">

            <img
                class="profile-arrow"
                src="{{ asset('icons/arrow.svg') }}"
                alt="">
        </button>


        <div class="profile-panel">

            <div class="profile-panel__user">
                <p class="profile-panel__name">
                    {{ auth()->user()->full_name ?? 'Пользователь' }}
                </p>

                <p class="profile-panel__position">
                    {{ auth()->user()->position ?? 'Сотрудник' }}
                </p>
            </div>


            <div class="profile-panel__menu">

                <a
                    href="#"
                    class="profile-panel__item">
                    Профиль
                </a>

                <a
                    href="#"
                    class="profile-panel__item">
                    Настройки
                </a>

                <form
                    id="logout-form"
                    action="{{ route('logout') }}"
                    method="POST">
                    @csrf

                    <button
                        type="submit"
                        class="profile-panel__item profile-panel__item--logout">
                        Выйти
                    </button>
                </form>

            </div>

        </div>

    </div>

</header>
