@extends('layouts.app')


@section('title', 'Авторизация')


@push('styles')
<link
    rel="stylesheet"
    href="{{ asset('css/auth/index.css') }}">
@endpush


@section('content')

<div
    class="auth_block d-flex align-items-center justify-content-center">
    <div class="auth_panel shadow-sm p-4 d-flex align-items-center justify-content-center flex-column">
        <img
            class="logo mb-4"
            src="{{ asset('icons/logo.svg') }}"
            alt="Лого" />
        <p class="auth_header m-0 p-0">Вход в информационную систему</p>
        <p class="auth_text_muted p-0 mb-4">Введите данные учётной записи для продолжения работы</p>
        <form
            class="auth_form"
            method="POST"
            action="{{ route('login.store') }}">
            @csrf
            {{-- Логин --}}
            <div>
                <label
                    for="email"
                    class="form-label">
                    {{ __('Логин') }}
                </label>

                <input
                    id="email"
                    class="form-control"
                    type="email"
                    name="email"
                    value="{{ old('email') }}"
                    required
                    autofocus
                    autocomplete="email"
                    placeholder="Введите email">
                @error('email')
                <div class="text-danger mt-2">
                    {{ $message }}
                </div>
                @enderror
            </div>

            {{-- Пароль --}}
            <div class="mt-4">
                <label
                    for="password"
                    class="form-label">
                    {{ __('Пароль') }}
                </label>
                <input
                    id="password"
                    class="form-control"
                    type="password"
                    name="password"
                    required
                    autocomplete="current-password"
                    placeholder="Введите пароль">
                @error('password')
                <div class="text-danger mt-2">
                    {{ $message }}
                </div>
                @enderror
            </div>

            {{-- Запомнить пользователя --}}

            <div class="form-check mt-4">
                <input
                    id="remember_me"
                    class="form-check-input"
                    type="checkbox"
                    name="remember"
                    value="1"
                    {{ old('remember') ? 'checked' : '' }}>

                <label
                    for="remember_me"
                    class="form-check-label">
                    {{ __('Не выходить из системы') }}
                </label>
            </div>

            {{-- Вход --}}

            <div
                class="w-100 d-flex align-items-center justify-content-center mt-4">
                <button
                    type="submit"
                    class="sumbit_button w-100 py-2">
                    {{ __('ВОЙТИ') }}
                </button>

            </div>

        </form>
    </div>
</div>

<img src="{{ asset('icons/auth_background.svg') }}" class="auth_background" alt="">

@endsection


@push('scripts')
<script
    src="{{ asset('js/auth/index.js') }}">
</script>
@endpush
