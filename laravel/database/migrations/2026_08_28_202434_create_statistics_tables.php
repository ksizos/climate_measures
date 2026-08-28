<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        /*
        |--------------------------------------------------------------------------
        | Справочники
        |--------------------------------------------------------------------------
        */

        Schema::create('industry', function (Blueprint $table): void {
            $table->id('industry_id');
            $table->string('name', 200)->unique();
        });

        Schema::create('territory_type', function (Blueprint $table): void {
            $table->id('territory_type_id');
            $table->string('name', 200)->unique();
        });

        Schema::create('unit', function (Blueprint $table): void {
            $table->id('unit_id');
            $table->string('name', 200)->unique();
        });

        Schema::create('period_type', function (Blueprint $table): void {
            $table->id('period_type_id');
            $table->string('name', 200)->unique();
        });

        /*
        |--------------------------------------------------------------------------
        | Основные справочники
        |--------------------------------------------------------------------------
        */

        Schema::create('territory', function (Blueprint $table): void {
            $table->id('territory_id');

            $table->bigInteger('parent_territory_id')->nullable();
            $table->bigInteger('territory_type_id');
            $table->string('name', 255);

            $table->foreign(
                'parent_territory_id',
                'fk_territory_parent'
            )
                ->references('territory_id')
                ->on('territory')
                ->onDelete('set null');

            $table->foreign(
                'territory_type_id',
                'fk_territory_type'
            )
                ->references('territory_type_id')
                ->on('territory_type')
                ->onDelete('restrict');

            $table->unique(
                [
                    'name',
                    'territory_type_id',
                    'parent_territory_id',
                ],
                'uq_territory_name_type_parent'
            );
        });

        DB::statement(
            '
            ALTER TABLE territory
            ADD CONSTRAINT chk_territory_not_self_parent
            CHECK (
                parent_territory_id IS NULL
                OR parent_territory_id <> territory_id
            )
            '
        );

        Schema::create('section', function (Blueprint $table): void {
            $table->id('section_id');

            $table->bigInteger('industry_id');
            $table->string('name', 255);

            $table->foreign(
                'industry_id',
                'fk_section_industry'
            )
                ->references('industry_id')
                ->on('industry')
                ->onDelete('restrict');

            $table->unique(
                'name',
                'uq_section_name'
            );

            $table->index(
                'industry_id',
                'idx_section_industry'
            );
        });

        Schema::create('indicator', function (Blueprint $table): void {
            $table->id('indicator_id');

            $table->bigInteger('section_id');
            $table->bigInteger('unit_id');
            $table->text('name');

            $table->foreign(
                'section_id',
                'fk_indicator_section'
            )
                ->references('section_id')
                ->on('section')
                ->onDelete('restrict');

            $table->foreign(
                'unit_id',
                'fk_indicator_unit'
            )
                ->references('unit_id')
                ->on('unit')
                ->onDelete('restrict');

            $table->unique(
                [
                    'section_id',
                    'name',
                ],
                'uq_indicator_section_name'
            );

            $table->index(
                'section_id',
                'idx_indicator_section'
            );

            $table->index(
                'unit_id',
                'idx_indicator_unit'
            );
        });

        Schema::create('period', function (Blueprint $table): void {
            $table->id('period_id');

            $table->bigInteger('period_type_id');
            $table->string('name', 255);
            $table->date('start_date')->nullable();
            $table->date('end_date')->nullable();

            $table->foreign(
                'period_type_id',
                'fk_period_period_type'
            )
                ->references('period_type_id')
                ->on('period_type')
                ->onDelete('restrict');

            $table->unique(
                [
                    'period_type_id',
                    'name',
                ],
                'uq_period_name_type'
            );

            $table->index(
                'period_type_id',
                'idx_period_period_type'
            );
        });

        DB::statement(
            '
            ALTER TABLE period
            ADD CONSTRAINT chk_period_dates
            CHECK (
                start_date IS NULL
                OR end_date IS NULL
                OR start_date <= end_date
            )
            '
        );

        /*
        |--------------------------------------------------------------------------
        | Таблица фактов
        |--------------------------------------------------------------------------
        */

        Schema::create('statistic', function (Blueprint $table): void {
            $table->id('statistic_id');

            $table->bigInteger('territory_id');
            $table->bigInteger('indicator_id');
            $table->bigInteger('period_id');

            $table->decimal(
                'value',
                20,
                4
            );

            $table->foreign(
                'territory_id',
                'fk_statistic_territory'
            )
                ->references('territory_id')
                ->on('territory')
                ->onDelete('cascade');

            $table->foreign(
                'indicator_id',
                'fk_statistic_indicator'
            )
                ->references('indicator_id')
                ->on('indicator')
                ->onDelete('cascade');

            $table->foreign(
                'period_id',
                'fk_statistic_period'
            )
                ->references('period_id')
                ->on('period')
                ->onDelete('cascade');

            $table->unique(
                [
                    'territory_id',
                    'indicator_id',
                    'period_id',
                ],
                'uq_statistic_territory_indicator_period'
            );

            $table->index(
                'territory_id',
                'idx_statistic_territory'
            );

            $table->index(
                'indicator_id',
                'idx_statistic_indicator'
            );

            $table->index(
                'period_id',
                'idx_statistic_period'
            );
        });
    }


    public function down(): void
    {
        /*
         * Удаляем строго в обратном порядке зависимостей.
         */

        Schema::dropIfExists('statistic');
        Schema::dropIfExists('indicator');
        Schema::dropIfExists('period');
        Schema::dropIfExists('section');
        Schema::dropIfExists('territory');
        Schema::dropIfExists('unit');
        Schema::dropIfExists('period_type');
        Schema::dropIfExists('territory_type');
        Schema::dropIfExists('industry');
    }
};
/*
НА БУДУЩЕЕ

<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {

        Schema::create('industry', function (Blueprint $table): void {
            $table->id();
            $table->string('name', 200)->unique();
        });

        Schema::create('territory_type', function (Blueprint $table): void {
            $table->id();
            $table->string('name', 200)->unique();
        });

        Schema::create('unit', function (Blueprint $table): void {
            $table->id();
            $table->string('name', 200)->unique();
        });

        Schema::create('period_type', function (Blueprint $table): void {
            $table->id();
            $table->string('name', 200)->unique();
        });



        Schema::create('territory', function (Blueprint $table): void {
            $table->id();

            $table->bigInteger('parent_territory_id')->nullable();
            $table->bigInteger('territory_type_id');
            $table->string('name', 255);

            $table->foreign(
                'parent_territory_id',
                'fk_territory_parent'
            )
                ->references('id')
                ->on('territory')
                ->onDelete('set null');

            $table->foreign(
                'territory_type_id',
                'fk_territory_type'
            )
                ->references('id')
                ->on('territory_type')
                ->onDelete('restrict');

            $table->unique(
                [
                    'name',
                    'territory_type_id',
                    'parent_territory_id',
                ],
                'uq_territory_name_type_parent'
            );
        });

        DB::statement(
            '
            ALTER TABLE territory
            ADD CONSTRAINT chk_territory_not_self_parent
            CHECK (
                parent_territory_id IS NULL
                OR parent_territory_id <> id
            )
            '
        );

        Schema::create('section', function (Blueprint $table): void {
            $table->id();

            $table->bigInteger('industry_id');
            $table->string('name', 255);

            $table->foreign(
                'industry_id',
                'fk_section_industry'
            )
                ->references('id')
                ->on('industry')
                ->onDelete('restrict');

            $table->unique(
                'name',
                'uq_section_name'
            );

            $table->index(
                'industry_id',
                'idx_section_industry'
            );
        });

        Schema::create('indicator', function (Blueprint $table): void {
            $table->id();

            $table->bigInteger('section_id');
            $table->bigInteger('unit_id');
            $table->text('name');

            $table->foreign(
                'section_id',
                'fk_indicator_section'
            )
                ->references('id')
                ->on('section')
                ->onDelete('restrict');

            $table->foreign(
                'unit_id',
                'fk_indicator_unit'
            )
                ->references('id')
                ->on('unit')
                ->onDelete('restrict');

            $table->unique(
                [
                    'section_id',
                    'name',
                ],
                'uq_indicator_section_name'
            );

            $table->index(
                'section_id',
                'idx_indicator_section'
            );

            $table->index(
                'unit_id',
                'idx_indicator_unit'
            );
        });

        Schema::create('period', function (Blueprint $table): void {
            $table->id();

            $table->bigInteger('period_type_id');
            $table->string('name', 255);
            $table->date('start_date')->nullable();
            $table->date('end_date')->nullable();

            $table->foreign(
                'period_type_id',
                'fk_period_period_type'
            )
                ->references('id')
                ->on('period_type')
                ->onDelete('restrict');

            $table->unique(
                [
                    'period_type_id',
                    'name',
                ],
                'uq_period_name_type'
            );

            $table->index(
                'period_type_id',
                'idx_period_period_type'
            );
        });

        DB::statement(
            '
            ALTER TABLE period
            ADD CONSTRAINT chk_period_dates
            CHECK (
                start_date IS NULL
                OR end_date IS NULL
                OR start_date <= end_date
            )
            '
        );


        Schema::create('statistic', function (Blueprint $table): void {
            $table->id();

            $table->bigInteger('territory_id');
            $table->bigInteger('indicator_id');
            $table->bigInteger('period_id');

            $table->decimal(
                'value',
                20,
                4
            );

            $table->foreign(
                'territory_id',
                'fk_statistic_territory'
            )
                ->references('id')
                ->on('territory')
                ->onDelete('cascade');

            $table->foreign(
                'indicator_id',
                'fk_statistic_indicator'
            )
                ->references('id')
                ->on('indicator')
                ->onDelete('cascade');

            $table->foreign(
                'period_id',
                'fk_statistic_period'
            )
                ->references('id')
                ->on('period')
                ->onDelete('cascade');

            $table->unique(
                [
                    'territory_id',
                    'indicator_id',
                    'period_id',
                ],
                'uq_statistic_territory_indicator_period'
            );

            $table->index(
                'territory_id',
                'idx_statistic_territory'
            );

            $table->index(
                'indicator_id',
                'idx_statistic_indicator'
            );

            $table->index(
                'period_id',
                'idx_statistic_period'
            );
        });
    }


    public function down(): void
    {
        Schema::dropIfExists('statistic');
        Schema::dropIfExists('indicator');
        Schema::dropIfExists('period');
        Schema::dropIfExists('section');
        Schema::dropIfExists('territory');
        Schema::dropIfExists('unit');
        Schema::dropIfExists('period_type');
        Schema::dropIfExists('territory_type');
        Schema::dropIfExists('industry');
    }
};
*/