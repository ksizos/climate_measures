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
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'email' => [
                'required',
                'string',
                'email',
            ],

            'password' => [
                'required',
                'string',
            ],
        ];
    }

    public function messages(): array
    {
        return [
            'email.required' =>
            'Введите адрес электронной почты.',

            'email.email' =>
            'Введите корректный адрес электронной почты.',

            'password.required' =>
            'Введите пароль.',
        ];
    }

    public function authenticate(): void
    {
        $this->ensureIsNotRateLimited();

        $credentials = [
            'email' => trim(
                $this->string('email')->toString()
            ),

            'password' =>
            $this->input('password'),
        ];

        $remember =
            $this->boolean('remember');

        if (!Auth::attempt(
            $credentials,
            $remember
        )) {
            RateLimiter::hit(
                $this->throttleKey()
            );

            throw ValidationException::withMessages([
                'email' =>
                'Неверная электронная почта или пароль.',
            ]);
        }

        RateLimiter::clear(
            $this->throttleKey()
        );
    }

    public function ensureIsNotRateLimited(): void
    {
        if (
            !RateLimiter::tooManyAttempts(
                $this->throttleKey(),
                5
            )
        ) {
            return;
        }

        event(new Lockout($this));

        $seconds =
            RateLimiter::availableIn(
                $this->throttleKey()
            );

        throw ValidationException::withMessages([
            'email' =>
            "Слишком много попыток входа. Повторите через {$seconds} сек.",
        ]);
    }

    public function throttleKey(): string
    {
        $email = trim(
            $this->string('email')->toString()
        );

        return Str::transliterate(
            Str::lower($email)
                . '|'
                . $this->ip()
        );
    }
}
