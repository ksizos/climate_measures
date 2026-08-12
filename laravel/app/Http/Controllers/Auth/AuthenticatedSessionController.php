<?php

namespace App\Http\Controllers\Auth;

use App\Http\Controllers\Controller;
use App\Http\Requests\Auth\LoginRequest;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\View\View;

class AuthenticatedSessionController extends Controller
{
    /**
     * Показ страницы авторизации.
     */
    public function create(): View|RedirectResponse
    {
        if (Auth::check()) {
            return $this->redirectAuthenticatedUser();
        }

        return view('auth.login');
    }

    /**
     * Авторизация пользователя.
     */
    public function store(LoginRequest $request): RedirectResponse
    {
        $request->authenticate();

        $request->session()->regenerate();

        return $this->redirectAuthenticatedUser();
    }

    /**
     * Выход пользователя.
     */
    public function destroy(Request $request): RedirectResponse
    {
        Auth::guard('web')->logout();

        $request->session()->invalidate();

        $request->session()->regenerateToken();

        return redirect()->route('login');
    }

    /**
     * Перенаправление после авторизации.
     */
    private function redirectAuthenticatedUser(): RedirectResponse
    {
        $user = Auth::user();

        if ($user && $user->role === 'admin') {
            return redirect()->route('admin.climate');
        }

        return redirect()->route('climate.index');
    }
}
