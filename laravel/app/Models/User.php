<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class User extends Authenticatable
{
    use Notifiable;


    public const ROLE_ADMIN = 'admin';
    public const ROLE_USER = 'user';
    public const ROLE_OPERATOR = 'operator';


    protected $fillable = [
        'name',
        'full_name',
        'organization_id',
        'position',
        'email',
        'password',
        'role',
    ];


    protected $hidden = [
        'password',
        'remember_token',
    ];


    protected function casts(): array
    {
        return [
            'password' => 'hashed',
        ];
    }


    public function conversations(): HasMany
    {
        return $this->hasMany(
            Conversation::class,
        );
    }


    public function isAdmin(): bool
    {
        return $this->role === self::ROLE_ADMIN;
    }


    public function isOperator(): bool
    {
        return $this->role === self::ROLE_OPERATOR;
    }


    public function isUser(): bool
    {
        return $this->role === self::ROLE_USER;
    }

    

    public function organization(): BelongsTo
    {
        return $this->belongsTo(
            Organization::class
        );
    }
}
