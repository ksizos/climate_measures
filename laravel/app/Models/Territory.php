<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Territory extends Model
{
    protected $table = 'territory';

    public $timestamps = false;

    protected $fillable = [
        'name',
        'territory_type_id',
        'parent_territory_id',
    ];

    public function organizations(): HasMany
    {
        return $this->hasMany(
            Organization::class,
            'territory_id'
        );
    }
}