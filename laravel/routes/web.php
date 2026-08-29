<?php

use App\Http\Controllers\AdminClimateController;
use App\Http\Controllers\ClimateController;
use Illuminate\Support\Facades\Route;
use Illuminate\Support\Facades\Auth;

/*
|--------------------------------------------------------------------------
| Главная
|--------------------------------------------------------------------------
|
| Перенаправление пользователя в зависимости от его роли.
|
*/

Route::get('/', function () {
    if (!Auth::check()) {
        return redirect()->route('login');
    }

    $user = Auth::user();

    if ($user->role === 'admin') {
        return redirect()->route('admin.climate');
    }

    return redirect()->route('climate.index');
})->name('home');


/*
|--------------------------------------------------------------------------
| Административная панель
|--------------------------------------------------------------------------
|
| Доступна только авторизованным пользователям
| с ролью admin.
|
*/

Route::middleware([
    'auth',
    'admin',
])
    ->prefix('admin')
    ->name('admin.')
    ->group(function () {

        /*
        |--------------------------------------------------------------------------
        | Главный экран администратора
        |--------------------------------------------------------------------------
        */

        Route::get(
            '/climate',
            [
                AdminClimateController::class,
                'index',
            ],
        )->name('climate');


        /*
        |--------------------------------------------------------------------------
        | CRUD кейсов
        |--------------------------------------------------------------------------
        */

        Route::get(
            '/climate/cases',
            [
                AdminClimateController::class,
                'getCases',
            ],
        )->name('cases.index');


        /*
         * ВАЖНО:
         * search должен находиться ДО /cases/{id},
         * иначе Laravel может воспринять "search"
         * как значение {id}.
         */
        Route::get(
            '/climate/cases/search',
            [
                AdminClimateController::class,
                'search',
            ],
        )->name('cases.search');


        Route::get(
            '/climate/cases/{id}',
            [
                AdminClimateController::class,
                'getCase',
            ],
        )->name('cases.show');


        Route::post(
            '/climate/cases',
            [
                AdminClimateController::class,
                'store',
            ],
        )->name('cases.store');


        Route::put(
            '/climate/cases/{id}',
            [
                AdminClimateController::class,
                'update',
            ],
        )->name('cases.update');


        Route::delete(
            '/climate/cases/{id}',
            [
                AdminClimateController::class,
                'destroy',
            ],
        )->name('cases.destroy');


        /*
        |--------------------------------------------------------------------------
        | AI-генерация
        |--------------------------------------------------------------------------
        */

        Route::post(
            '/climate/generate-data',
            [
                AdminClimateController::class,
                'generateData',
            ],
        )->name('generate.data');


        Route::post(
            '/climate/save-generated-data',
            [
                AdminClimateController::class,
                'saveGeneratedData',
            ],
        )->name('save.generated.data');


        /*
        |--------------------------------------------------------------------------
        | Обратная совместимость
        |--------------------------------------------------------------------------
        */

        Route::post(
            '/climate/generate-sql',
            [
                AdminClimateController::class,
                'generateData',
            ],
        )->name('generate.sql');


        Route::post(
            '/climate/execute-sql',
            [
                AdminClimateController::class,
                'executeSql',
            ],
        )->name('execute.sql');
    });


/*
|--------------------------------------------------------------------------
| Пользовательская часть
|--------------------------------------------------------------------------
|
| Доступна авторизованным пользователям.
| Администратор перенаправляется в admin-панель
| через middleware admin.redirect.
|
*/

Route::middleware([
    'auth',
    'admin.redirect',
])->group(function () {

    /*
    |--------------------------------------------------------------------------
    | Основной интерфейс
    |--------------------------------------------------------------------------
    */

    Route::get(
        '/climate',
        [
            ClimateController::class,
            'showInterface',
        ],
    )->name('climate.index');


    Route::post(
        '/climate/ask',
        [
            ClimateController::class,
            'askQuestion',
        ],
    )->name('climate.ask');


    Route::post(
        '/climate/cancel',
        [
            ClimateController::class,
            'cancelGeneration',
        ],
    )->name('climate.cancel');


    Route::get(
        '/climate/health',
        [
            ClimateController::class,
            'checkHealth',
        ],
    )->name('climate.health');

    /*
    |--------------------------------------------------------------------------
    | Диалоги
    |--------------------------------------------------------------------------
    */

    Route::post(
        '/climate/conversation/new',
        [
            ClimateController::class,
            'newConversation',
        ],
    )->name('conversation.new');


    /*
     * conversations лучше объявлять ДО conversation/{id},
     * чтобы статический маршрут не конфликтовал
     * с динамическим параметром {id}.
     */
    Route::get(
        '/climate/conversations',
        [
            ClimateController::class,
            'getConversations',
        ],
    )->name('conversations.get');


    Route::get(
        '/climate/conversation/{id}',
        [
            ClimateController::class,
            'getConversation',
        ],
    )->name('conversation.get');

    Route::patch(
        '/climate/conversation/{id}/title',
        [
            ClimateController::class,
            'renameConversation',
        ],
    )->name('conversation.rename');

    Route::delete(
        '/climate/conversation/{id}',
        [
            ClimateController::class,
            'deleteConversation',
        ],
    )->name('conversation.delete');

    Route::delete(
        '/climate/conversations',
        [
            ClimateController::class,
            'clearConversations',
        ],
    )->name('conversations.clear');


    /*
    |--------------------------------------------------------------------------
    | Адаптационные мероприятия
    |--------------------------------------------------------------------------
    */

    Route::post(
        '/climate/approve-measure',
        [
            ClimateController::class,
            'approveMeasure',
        ],
    )->name('climate.approve-measure');


    /*
    |--------------------------------------------------------------------------
    | Экспорт
    |--------------------------------------------------------------------------
    |
    | Прокси Laravel -> Python API.
    |
    */

    Route::post(
        '/climate/export/docx',
        [
            ClimateController::class,
            'exportDocx',
        ],
    )->name('climate.export.docx');


    Route::post(
        '/climate/export/excel',
        [
            ClimateController::class,
            'exportExcel',
        ],
    )->name('climate.export.excel');
});


/*
|--------------------------------------------------------------------------
| Аутентификация
|--------------------------------------------------------------------------
*/

require __DIR__ . '/auth.php';
