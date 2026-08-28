<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create(
            'organizations',
            function (Blueprint $table): void {
                $table->id();

                $table->string(
                    'name',
                    255
                )->unique();

                $table->foreignId(
                    'territory_id'
                )->nullable();

                $table->timestamps();

                $table->foreign(
                    'territory_id'
                )
                    ->references('territory_id')
                    ->on('territory')
                    ->nullOnDelete();
            }
        );

        Schema::table(
            'users',
            function (Blueprint $table): void {
                $table->foreignId(
                    'organization_id'
                )
                    ->nullable()
                    ->after('full_name')
                    ->constrained('organizations')
                    ->nullOnDelete();
            }
        );

        /*
         * Переносим существующие строковые
         * названия организаций.
         */
        $users = DB::table('users')
            ->select(
                'id',
                'organization'
            )
            ->whereNotNull('organization')
            ->get();

        foreach ($users as $user) {
            $name = trim(
                (string) $user->organization
            );

            if ($name === '') {
                continue;
            }

            $organizationId = DB::table(
                'organizations'
            )
                ->where(
                    'name',
                    $name
                )
                ->value('id');

            if (!$organizationId) {
                $organizationId = DB::table(
                    'organizations'
                )->insertGetId([
                    'name' => $name,
                    'territory_id' => null,
                    'created_at' => now(),
                    'updated_at' => now(),
                ]);
            }

            DB::table('users')
                ->where(
                    'id',
                    $user->id
                )
                ->update([
                    'organization_id'
                        => $organizationId,
                ]);
        }
    }

    public function down(): void
    {
        Schema::table(
            'users',
            function (Blueprint $table): void {
                $table->dropConstrainedForeignId(
                    'organization_id'
                );
            }
        );

        Schema::dropIfExists(
            'organizations'
        );
    }
};