<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create(
            'climate_cases',
            function (Blueprint $table): void {
                $table->id();

                $table->text(
                    'problem'
                )->nullable();

                $table->string(
                    'measure_name',
                    2000
                );

                $table->text(
                    'mitigation_effect'
                )->nullable();

                $table->text(
                    'adaptation_effect'
                )->nullable();

                $table->string(
                    'district_name'
                )->nullable();

                $table->text(
                    'climate_conditions'
                )->nullable();

                $table->string(
                    'responsible_org',
                    500
                )->nullable();

                $table->string(
                    'source_url',
                    1000
                )->nullable();

                $table->timestamps();
            }
        );
    }

    public function down(): void
    {
        Schema::dropIfExists(
            'climate_cases'
        );
    }
};
