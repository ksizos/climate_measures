<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('industry', function (Blueprint $table): void {
            $table->renameColumn('industry_id', 'id');
        });

        Schema::table('territory_type', function (Blueprint $table): void {
            $table->renameColumn('territory_type_id', 'id');
        });

        Schema::table('unit', function (Blueprint $table): void {
            $table->renameColumn('unit_id', 'id');
        });

        Schema::table('period_type', function (Blueprint $table): void {
            $table->renameColumn('period_type_id', 'id');
        });

        Schema::table('territory', function (Blueprint $table): void {
            $table->renameColumn('territory_id', 'id');
        });

        Schema::table('section', function (Blueprint $table): void {
            $table->renameColumn('section_id', 'id');
        });

        Schema::table('indicator', function (Blueprint $table): void {
            $table->renameColumn('indicator_id', 'id');
        });

        Schema::table('period', function (Blueprint $table): void {
            $table->renameColumn('period_id', 'id');
        });

        Schema::table('statistic', function (Blueprint $table): void {
            $table->renameColumn('statistic_id', 'id');
        });
    }


    public function down(): void
    {
        Schema::table('statistic', function (Blueprint $table): void {
            $table->renameColumn('id', 'statistic_id');
        });

        Schema::table('period', function (Blueprint $table): void {
            $table->renameColumn('id', 'period_id');
        });

        Schema::table('indicator', function (Blueprint $table): void {
            $table->renameColumn('id', 'indicator_id');
        });

        Schema::table('section', function (Blueprint $table): void {
            $table->renameColumn('id', 'section_id');
        });

        Schema::table('territory', function (Blueprint $table): void {
            $table->renameColumn('id', 'territory_id');
        });

        Schema::table('period_type', function (Blueprint $table): void {
            $table->renameColumn('id', 'period_type_id');
        });

        Schema::table('unit', function (Blueprint $table): void {
            $table->renameColumn('id', 'unit_id');
        });

        Schema::table('territory_type', function (Blueprint $table): void {
            $table->renameColumn('id', 'territory_type_id');
        });

        Schema::table('industry', function (Blueprint $table): void {
            $table->renameColumn('id', 'industry_id');
        });
    }
};