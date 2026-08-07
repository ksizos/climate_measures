<?php

// app/Models/User.php

namespace App\Models;

use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;

class User extends Authenticatable
{
    use Notifiable;

    /**
     * Роли пользователей.
     */
    public const ROLE_ADMIN = 'admin';
    public const ROLE_USER = 'user';
    public const ROLE_OPERATOR = 'operator';

    /**
     * Поля, доступные для массового заполнения.
     */
    protected $fillable = [
        'name',
        'full_name',
        'organization',
        'position',
        'email',
        'password',
        'role',
    ];

    /**
     * Поля, скрываемые при сериализации.
     */
    protected $hidden = [
        'password',
        'remember_token',
    ];

    /**
     * Диалоги пользователя.
     */
    public function conversations()
    {
        return $this->hasMany(Conversation::class);
    }

    /**
     * Администратор системы.
     */
    public function isAdmin(): bool
    {
        return $this->role === self::ROLE_ADMIN;
    }

    /**
     * Сотрудник МО, работающий с данными.
     */
    public function isOperator(): bool
    {
        return $this->role === self::ROLE_OPERATOR;
    }

    /**
     * Обычный пользователь.
     */
    public function isUser(): bool
    {
        return $this->role === self::ROLE_USER;
    }
}
