<header class="d-flex justify-content-end align-items-center px-4 py-2">

    <div
        class="d-flex align-items-center justify-content-center dropdown profile-dropdown"
        id="profile-fixed">

        <a
            href="#"
            class="d-flex align-items-center justify-content-center header_text dropdown-toggle gap-3 py-2 text-decoration-none"
            id="userProfileDropdown"
            role="button"
            aria-expanded="false"
            onclick="event.preventDefault();">
            <img
                class="header_img"
                src="{{ asset('icons/account.svg') }}"
                alt="Личный кабинет" />

            <div class="d-flex flex-column">
                <p class="dropdown_name p-0 m-0">
                    {{ auth()->user()->full_name ?? 'Пользователь' }}
                </p>

                <p class="dropdown_position p-0 m-0">
                    {{ auth()->user()->position ?? 'Сотрудник' }}
                </p>
            </div>

            <img
                class="profile-arrow"
                src="{{ asset('icons/arrow.svg') }}"
                alt="Развернуть">
        </a>


        <ul
            id="profile-info"
            class="dropdown-menu dropdown-menu-end shadow-sm p-0 m-0"
            aria-labelledby="userProfileDropdown">
            <li>
                <form
                    id="logout-form"
                    action="{{ route('logout') }}"
                    method="POST"
                    class="d-none">
                    @csrf
                </form>

                <a
                    onclick="event.preventDefault(); document.getElementById('logout-form').submit();"
                    class="dropdown-item text-danger fw-medium pt-1 m-0">
                    <i class="fas fa-sign-out-alt"></i>
                    Выйти
                </a>
            </li>
        </ul>

    </div>

</header>
