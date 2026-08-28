<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class Organization extends Model
{
    protected $fillable = [
        'name',
        'territory_id',
    ];

    public function users(): HasMany
    {
        return $this->hasMany(
            User::class
        );
    }

    public function territory(): BelongsTo
{
    return $this->belongsTo(
        Territory::class,
        'territory_id'
    );
}
}