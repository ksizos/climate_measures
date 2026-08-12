<?php

namespace App\Http\Requests\Auth;

use Illuminate\Auth\Events\Lockout;
use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\RateLimiter;
use Illuminate\Support\Str;
use Illuminate\Validation\ValidationException;

class LoginRequest extends FormRequest
{
    /**
     * Разрешение выполнения запроса.
     */
    public function authorize(): bool
    {
        return true;
    }

    /**
     * Правила валидации.
     */
    public function rules(): array
    {
        return [
            'name' => [
                'required',
                'string',
            ],

            'password' => [
                'required',
                'string',
            ],
        ];
    }

    /**
     * Сообщения валидации.
     */
    public function messages(): array
    {
        return [
            'name.required' =>
            'Поле логина обязательно для заполнения.',

            'name.string' =>
            'Логин должен быть строкой.',

            'password.required' =>
            'Поле пароля обязательно для заполнения.',

            'password.string' =>
            'Пароль должен быть строкой.',
        ];
    }

    /**
     * Попытка авторизации.
     */
    public function authenticate(): void
    {
        $this->ensureIsNotRateLimited();

        $credentials = [
            'name' => $this->string('name')->toString(),
            'password' => $this->input('password'),
        ];

        $remember = $this->boolean('remember');

        if (!Auth::attempt($credentials, $remember)) {
            RateLimiter::hit(
                $this->throttleKey(),
            );

            throw ValidationException::withMessages([
                'name' => 'Неверный логин или пароль.',
            ]);
        }

        RateLimiter::clear(
            $this->throttleKey(),
        );
    }

    /**
     * Проверка ограничения количества попыток.
     */
    public function ensureIsNotRateLimited(): void
    {
        if (
            !RateLimiter::tooManyAttempts(
                $this->throttleKey(),
                5,
            )
        ) {
            return;
        }

        event(new Lockout($this));

        $seconds = RateLimiter::availableIn(
            $this->throttleKey(),
        );

        throw ValidationException::withMessages([
            'name' =>
            "Слишком много попыток входа. Повторите через {$seconds} сек.",
        ]);
    }

    /**
     * Ключ rate limiter.
     */
    public function throttleKey(): string
    {
        return Str::transliterate(
            Str::lower(
                $this->string('name')->toString(),
            )
                . '|'
                . $this->ip(),
        );
    }
}
