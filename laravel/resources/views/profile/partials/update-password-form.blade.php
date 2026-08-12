<section>

    <header>

        <h2 class="text-lg font-medium text-gray-900">
            {{ __('Update Password') }}
        </h2>

        <p class="mt-1 text-sm text-gray-600">
            {{ __('Ensure your account is using a long, random password to stay secure.') }}
        </p>

    </header>


    <form
        method="POST"
        action="{{ route('password.update') }}"
        class="mt-6 space-y-6">

        @csrf
        @method('PUT')


        {{-- Текущий пароль --}}

        <div>

            <label
                for="update_password_current_password"
                class="block font-medium text-sm text-gray-700">
                {{ __('Current Password') }}
            </label>


            <input
                id="update_password_current_password"
                name="current_password"
                type="password"
                class="mt-1 block w-full"
                autocomplete="current-password">


            @if ($errors->updatePassword->has('current_password'))

            <div class="mt-2 text-sm text-red-600">
                {{ $errors->updatePassword->first('current_password') }}
            </div>

            @endif

        </div>


        {{-- Новый пароль --}}

        <div>

            <label
                for="update_password_password"
                class="block font-medium text-sm text-gray-700">
                {{ __('New Password') }}
            </label>


            <input
                id="update_password_password"
                name="password"
                type="password"
                class="mt-1 block w-full"
                autocomplete="new-password">


            @if ($errors->updatePassword->has('password'))

            <div class="mt-2 text-sm text-red-600">
                {{ $errors->updatePassword->first('password') }}
            </div>

            @endif

        </div>


        {{-- Повтор нового пароля --}}

        <div>

            <label
                for="update_password_password_confirmation"
                class="block font-medium text-sm text-gray-700">
                {{ __('Confirm Password') }}
            </label>


            <input
                id="update_password_password_confirmation"
                name="password_confirmation"
                type="password"
                class="mt-1 block w-full"
                autocomplete="new-password">


            @if ($errors->updatePassword->has('password_confirmation'))

            <div class="mt-2 text-sm text-red-600">
                {{ $errors->updatePassword->first('password_confirmation') }}
            </div>

            @endif

        </div>


        {{-- Сохранение --}}

        <div class="flex items-center gap-4">

            <button
                type="submit"
                class="inline-flex items-center px-4 py-2 bg-gray-800 border border-transparent rounded-md font-semibold text-xs text-white uppercase tracking-widest">
                {{ __('Save') }}
            </button>


            @if (session('status') === 'password-updated')

            <p class="text-sm text-gray-600">
                {{ __('Saved.') }}
            </p>

            @endif

        </div>

    </form>

</section>
