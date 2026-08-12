@extends('layouts.app')

@section('title', 'Авторизация')

@push('styles')
<link
    rel="stylesheet"
    href="{{ asset('css/auth/index.css') }}">
@endpush


@section('content')

<div class="auth_block d-flex align-items-center justify-content-center">
    <form сlass="auth_panel shadow-sm px-2 py-1"
        method="POST"
        action="{{ route('login.store') }}">
        @csrf

        <!-- Username -->
        <div>
            <label for="name">
                {{ __('Логин') }}
            </label>

            <input
                id="name"
                class="block mt-1 w-full"
                type="text"
                name="name"
                value="{{ old('name') }}"
                required
                autofocus
                autocomplete="username">

            @error('name')
            <div class="mt-2">
                {{ $message }}
            </div>
            @enderror
        </div>


        <!-- Password -->
        <div class="mt-4">

            <label for="password">
                {{ __('Пароль') }}
            </label>

            <input
                id="password"
                class="block mt-1 w-full"
                type="password"
                name="password"
                required
                autocomplete="current-password">

            @error('password')
            <div class="mt-2">
                {{ $message }}
            </div>
            @enderror

        </div>


        <!-- Remember Me -->
        <div class="block mt-4">

            <label
                for="remember_me"
                class="inline-flex items-center">
                <input
                    id="remember_me"
                    type="checkbox"
                    class="rounded border-gray-300 text-indigo-600 shadow-sm focus:ring-indigo-500"
                    name="remember"
                    value="1"
                    {{ old('remember') ? 'checked' : '' }}>

                <span class="ms-2 text-sm text-gray-600">
                    {{ __('Не выходить из системы') }}
                </span>
            </label>

        </div>


        <div class="flex items-center justify-end mt-4">

            <button
                type="submit"
                class="ms-3">
                {{ __('Войти') }}
            </button>

        </div>

    </form>
</div>

@endsection


@push('scripts')
<script src="{{ asset('js/auth/index.js') }}"></script>
@endpush
