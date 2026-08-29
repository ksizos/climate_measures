<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('messages', function (Blueprint $table) {
            $table
                ->string('status', 30)
                ->default('success')
                ->after('answer');

            $table
                ->string('error_code', 100)
                ->nullable()
                ->after('status');
        });
    }

    public function down(): void
    {
        Schema::table('messages', function (Blueprint $table) {
            $table->dropColumn([
                'status',
                'error_code',
            ]);
        });
    }
};
