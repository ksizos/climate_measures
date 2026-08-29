<?php

namespace App\Http\Controllers;

use App\Models\Conversation;
use App\Models\Message;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Str;
use Illuminate\Validation\Rule;

class ClimateController extends Controller
{
    private $apiBaseUrl;


    public function __construct()
    {
        $this->apiBaseUrl = env(
            'CLIMATE_API_URL',
            'http://localhost:8001'
        );
    }


    /**
     * Показать интерфейс системы.
     */
    public function showInterface()
    {
        $user = auth()->user();


        if ($user->role === 'admin') {
            return redirect()->route(
                'admin.climate'
            );
        }


        $conversations = $user
            ->conversations()
            ->orderBy(
                'last_interaction_at',
                'desc'
            )
            ->take(10)
            ->get();


        return view(
            'climate.index',
            compact('conversations')
        );
    }


    /**
     * Начать новый диалог.
     */
    public function newConversation()
    {
        $conversation = Conversation::create([
            'user_id' =>
            auth()->id(),

            'title' =>
            'Новый диалог',

            'last_interaction_at' =>
            now(),
        ]);


        return response()->json([
            'success' =>
            true,

            'conversation_id' =>
            $conversation->id,
        ]);
    }

    /**
     * Получить конкретный диалог вместе с сообщениями.
     */
    public function getConversation($id)
    {
        $conversation =
            Conversation::where(
                'user_id',
                auth()->id()
            )
            ->with([
                'messages' => function ($query) {
                    $query->orderBy(
                        'interaction_time',
                        'asc'
                    );
                },
            ])
            ->findOrFail($id);


        return response()->json([
            'success' =>
            true,

            'conversation' =>
            $conversation,
        ]);
    }


    /**
     * Получить историю диалога.
     */
    public function getConversations(
        Request $request
    ) {
        $search =
            trim(
                (string) $request->query(
                    'search',
                    ''
                )
            );


        $query =
            auth()
            ->user()
            ->conversations();


        /*
     * Поиск исключительно
     * по вопросам пользователя.
     *
     * messages.answer здесь
     * намеренно не используется.
     */
        if ($search !== '') {

            $words =
                preg_split(
                    '/\s+/u',
                    $search,
                    -1,
                    PREG_SPLIT_NO_EMPTY
                );


            $query->whereHas(
                'messages',
                function ($messageQuery) use ($words) {

                    foreach ($words as $word) {

                        $escapedWord =
                            str_replace(
                                [
                                    '\\',
                                    '%',
                                    '_',
                                ],
                                [
                                    '\\\\',
                                    '\%',
                                    '\_',
                                ],
                                $word
                            );


                        $messageQuery->where(
                            'question',
                            'ILIKE',
                            '%'
                                . $escapedWord
                                . '%'
                        );
                    }
                }
            );
        }


        $conversations =
            $query
            ->orderBy(
                'last_interaction_at',
                'desc'
            )
            ->get()
            ->map(
                function ($conversation) {

                    $lastPair =
                        $conversation
                        ->messages()
                        ->orderBy(
                            'interaction_time',
                            'desc'
                        )
                        ->first();


                    return [
                        'id' =>
                        $conversation->id,

                        'title' =>
                        $conversation->title
                            ??
                            (
                                $lastPair
                                ? Str::limit(
                                    $lastPair->question,
                                    50
                                )
                                : 'Без названия'
                            ),

                        'last_interaction_at' =>
                        $conversation
                            ->last_interaction_at
                            ->format(
                                'd.m.Y H:i'
                            ),

                        'pair_count' =>
                        $conversation
                            ->messages()
                            ->count(),

                        'last_question' =>
                        $lastPair
                            ? Str::limit(
                                $lastPair->question,
                                70
                            )
                            : null,

                        'last_answer_preview' =>
                        $lastPair
                            ? Str::limit(
                                strip_tags(
                                    $lastPair->answer
                                ),
                                100
                            )
                            : null,
                    ];
                }
            );


        return response()->json([
            'success' =>
            true,

            'conversations' =>
            $conversations,

            'search' =>
            $search,
        ]);
    }


    /**
     * Обработать запрос пользователя
     * с сохранением результата в БД.
     */
    public function askQuestion(
        Request $request
    ) {
        set_time_limit(
            (int) config(
                'services.climate_api.timeout',
                600
            )
        );


        $request->validate([
            'question' => [
                'required',
                'string',
                'min:3',
                'max:1000',
            ],

            'conversation_id' => [
                'nullable',

                Rule::exists(
                    'conversations',
                    'id'
                )
                    ->where(
                        'user_id',
                        auth()->id()
                    )
                    ->whereNull(
                        'deleted_at'
                    ),
            ],

            'request_id' => [
                'required',
                'string',
                'max:100',
            ],
        ]);


        /*
         * =====================================================
         * 1. СОЗДАНИЕ / ПОЛУЧЕНИЕ ДИАЛОГА
         * =====================================================
         */

        if (!$request->conversation_id) {

            $conversation =
                Conversation::create([
                    'user_id' =>
                    auth()->id(),

                    'title' =>
                    Str::limit(
                        $request->question,
                        50
                    ),

                    'last_interaction_at' =>
                    now(),
                ]);
        } else {

            $conversation =
                Conversation::where(
                    'user_id',
                    auth()->id()
                )
                ->findOrFail(
                    $request->conversation_id
                );


            if (
                !$conversation->title
                ||
                $conversation->title
                ===
                'Новый диалог'
            ) {
                $conversation->title =
                    Str::limit(
                        $request->question,
                        50
                    );


                $conversation->save();
            }
        }


        $conversationId =
            $conversation->id;


        /*
         * =====================================================
         * 2. КОНТЕКСТ
         *
         * В контекст передаём только успешные ответы.
         * Ошибки сервиса не должны попадать к LLM.
         * =====================================================
         */

        $contextPairs =
            Message::where(
                'conversation_id',
                $conversationId
            )
            ->where(
                'status',
                'success'
            )
            ->orderBy(
                'interaction_time',
                'desc'
            )
            ->take(3)
            ->get()
            ->reverse();


        $context = '';


        foreach ($contextPairs as $pair) {

            $context .=
                "Пользователь: "
                . $pair->question
                . "\n";


            $context .=
                "Ассистент: "
                . $pair->answer
                . "\n\n";
        }


        Log::info(
            'Отправка запроса к Climate API',
            [
                'question' =>
                $request->question,

                'conversation_id' =>
                $conversationId,

                'context' =>
                $context,

                'request_id' =>
                $request->request_id,
            ]
        );


        try {

            /*
             * =================================================
             * 3. ЗАПРОС К PYTHON API
             * =================================================
             */

            $response =
                Http::connectTimeout(10)
                ->timeout(
                    (int) config(
                        'services.climate_api.timeout',
                        600
                    )
                )
                ->post(
                    $this->apiBaseUrl
                        . '/ask',
                    [
                        'question' =>
                        $request->question,

                        'conversation_id' =>
                        $conversationId,

                        'context' =>
                        $context,

                        'request_id' =>
                        $request->request_id,
                    ]
                );


            /*
             * =================================================
             * 4. PYTHON ВЕРНУЛ HTTP 2XX
             * =================================================
             */

            if ($response->successful()) {

                $data =
                    $response->json();


                /*
                 * Защита от неожидаемого формата.
                 */
                $rawAnswer =
                    $data['answer']
                    ?? '';


                $answer =
                    is_string($rawAnswer)
                    ? trim($rawAnswer)
                    : '';


                /*
                 * ---------------------------------------------
                 * ПУСТОЙ ОТВЕТ
                 * ---------------------------------------------
                 */

                if ($answer === '') {

                    $errorMessage =
                        'Модель не вернула ответ. '
                        . 'Попробуйте повторить запрос.';


                    Message::create([
                        'conversation_id' =>
                        $conversationId,

                        'question' =>
                        $request->question,

                        'answer' =>
                        $errorMessage,

                        'status' =>
                        'error',

                        'error_code' =>
                        'empty_response',

                        'interaction_time' =>
                        now(),
                    ]);


                    $conversation
                        ->updateLastInteractionTime();


                    Log::warning(
                        'Climate API вернул пустой ответ',
                        [
                            'conversation_id' =>
                            $conversationId,

                            'request_id' =>
                            $request->request_id,

                            'response' =>
                            $data,
                        ]
                    );


                    return response()->json(
                        [
                            'success' =>
                            false,

                            'error' =>
                            $errorMessage,

                            'status' =>
                            'error',

                            'error_code' =>
                            'empty_response',

                            'conversation_id' =>
                            $conversationId,
                        ],
                        422
                    );
                }


                /*
                 * ---------------------------------------------
                 * НОРМАЛЬНЫЙ ОТВЕТ
                 * ---------------------------------------------
                 */

                Message::create([
                    'conversation_id' =>
                    $conversationId,

                    'question' =>
                    $request->question,

                    'answer' =>
                    $answer,

                    'status' =>
                    'success',

                    'error_code' =>
                    null,

                    'interaction_time' =>
                    now(),
                ]);


                $conversation
                    ->updateLastInteractionTime();


                Log::info(
                    'Успешный ответ от Climate API',
                    [
                        'answer_length' =>
                        strlen($answer),

                        'status' =>
                        $data['status']
                            ?? 'success',

                        'conversation_id' =>
                        $conversationId,

                        'request_id' =>
                        $request->request_id,
                    ]
                );


                return response()->json([
                    'success' =>
                    true,

                    'answer' =>
                    $answer,

                    'status' =>
                    'success',

                    'conversation_id' =>
                    $conversationId,
                ]);
            }


            /*
             * =================================================
             * 5. PYTHON ДОСТУПЕН,
             * НО ВЕРНУЛ HTTP-ОШИБКУ
             * =================================================
             */

            Log::error(
                'Ошибка Climate API',
                [
                    'status' =>
                    $response->status(),

                    'body' =>
                    $response->body(),

                    'conversation_id' =>
                    $conversationId,

                    'request_id' =>
                    $request->request_id,
                ]
            );


            $errorMessage =
                'Сервис временно недоступен. '
                . 'Попробуйте позже.';


            Message::create([
                'conversation_id' =>
                $conversationId,

                'question' =>
                $request->question,

                'answer' =>
                $errorMessage,

                'status' =>
                'error',

                'error_code' =>
                'api_error_'
                    . $response->status(),

                'interaction_time' =>
                now(),
            ]);


            $conversation
                ->updateLastInteractionTime();


            return response()->json(
                [
                    'success' =>
                    false,

                    'error' =>
                    $errorMessage,

                    'status' =>
                    'error',

                    'error_code' =>
                    'api_error_'
                        . $response->status(),

                    'conversation_id' =>
                    $conversationId,
                ],
                $response->status() >= 400
                    ? $response->status()
                    : 500
            );
        } catch (
            \Illuminate\Http\Client\ConnectionException $e
        ) {

            /*
             * =================================================
             * 6. PYTHON ВООБЩЕ НЕДОСТУПЕН
             * =================================================
             */

            $errorMessage =
                'Не удалось подключиться к сервису. '
                . 'Проверьте, запущен ли Python сервер.';


            Log::error(
                'Не удалось подключиться к Climate API',
                [
                    'message' =>
                    $e->getMessage(),

                    'conversation_id' =>
                    $conversationId,

                    'request_id' =>
                    $request->request_id,
                ]
            );


            Message::create([
                'conversation_id' =>
                $conversationId,

                'question' =>
                $request->question,

                'answer' =>
                $errorMessage,

                'status' =>
                'error',

                'error_code' =>
                'connection_error',

                'interaction_time' =>
                now(),
            ]);


            $conversation
                ->updateLastInteractionTime();


            return response()->json(
                [
                    'success' =>
                    false,

                    'error' =>
                    $errorMessage,

                    'status' =>
                    'error',

                    'error_code' =>
                    'connection_error',

                    'conversation_id' =>
                    $conversationId,
                ],
                503
            );
        } catch (\Throwable $e) {

            /*
             * =================================================
             * 7. НЕПРЕДВИДЕННАЯ ОШИБКА
             * =================================================
             */

            $errorMessage =
                'Произошла ошибка при обработке запроса.';


            Log::error(
                'Исключение при обработке Climate API',
                [
                    'message' =>
                    $e->getMessage(),

                    'trace' =>
                    $e->getTraceAsString(),

                    'conversation_id' =>
                    $conversationId,

                    'request_id' =>
                    $request->request_id,
                ]
            );


            Message::create([
                'conversation_id' =>
                $conversationId,

                'question' =>
                $request->question,

                'answer' =>
                $errorMessage,

                'status' =>
                'error',

                'error_code' =>
                'internal_error',

                'interaction_time' =>
                now(),
            ]);


            $conversation
                ->updateLastInteractionTime();


            return response()->json(
                [
                    'success' =>
                    false,

                    'error' =>
                    $errorMessage,

                    'status' =>
                    'error',

                    'error_code' =>
                    'internal_error',

                    'conversation_id' =>
                    $conversationId,
                ],
                500
            );
        }
    }


    /**
     * Остановить текущую генерацию.
     */
    public function cancelGeneration(
        Request $request
    ) {
        $request->validate([
            'request_id' =>
            'required|string|max:100',
        ]);


        try {

            Http::connectTimeout(2)
                ->timeout(5)
                ->post(
                    $this->apiBaseUrl
                        . '/cancel/'
                        . urlencode(
                            $request->request_id
                        )
                );


            return response()->json([
                'success' =>
                true,
            ]);
        } catch (\Exception $e) {

            Log::warning(
                'Не удалось отправить отмену в Climate API',
                [
                    'request_id' =>
                    $request->request_id,

                    'message' =>
                    $e->getMessage(),
                ]
            );


            return response()->json([
                'success' =>
                true,
            ]);
        }
    }


    /**
     * Проверить статус сервиса.
     */
    public function checkHealth()
    {
        try {

            $response =
                Http::timeout(10)
                ->get(
                    $this->apiBaseUrl
                        . '/health'
                );


            return response()->json([
                'status' =>
                $response->successful()
                    ? 'healthy'
                    : 'unhealthy',

                'api_status' =>
                $response->status(),
            ]);
        } catch (\Exception $e) {

            return response()->json(
                [
                    'status' =>
                    'unhealthy',

                    'error' =>
                    $e->getMessage(),
                ],
                500
            );
        }
    }

    /**
     * Переименовать диалог.
     */
    public function renameConversation(
        Request $request,
        $id
    ) {
        $validated =
            $request->validate([
                'title' => [
                    'required',
                    'string',
                    'max:30',
                ],
            ]);


        $title =
            trim(
                $validated['title']
            );


        if ($title === '') {
            return response()->json(
                [
                    'success' =>
                    false,

                    'message' =>
                    'Название не может быть пустым.',
                ],
                422
            );
        }


        $conversation =
            Conversation::where(
                'user_id',
                auth()->id()
            )
            ->findOrFail($id);


        $conversation->title =
            $title;


        $conversation->save();


        return response()->json([
            'success' =>
            true,

            'conversation' => [
                'id' =>
                $conversation->id,

                'title' =>
                $conversation->title,
            ],
        ]);
    }

    /**
     * Удалить диалог.
     *
     * При использовании SoftDeletes
     * запись остаётся в БД.
     */
    public function deleteConversation($id)
    {
        $conversation =
            Conversation::where(
                'user_id',
                auth()->id()
            )
            ->findOrFail($id);


        $conversation->delete();


        return response()->json([
            'success' =>
            true,
        ]);
    }

    public function clearConversations()
    {
        Conversation::where(
            'user_id',
            auth()->id()
        )->delete();


        return response()->json([
            'success' => true,
        ]);
    }

    /**
     * Одобрить мероприятие.
     */
    public function approveMeasure(
        Request $request
    ) {
        $request->validate([
            'measure.name' =>
            'required|string',

            'measure.mitigation' =>
            'nullable|string',

            'measure.adaptation' =>
            'required|string',

            'measure.relevance' =>
            'required|string',

            'measure.responsible' =>
            'required|string',

            'source_question' =>
            'nullable|string',
        ]);


        $response =
            Http::timeout(10)
            ->post(
                $this->apiBaseUrl
                    . '/approve-measure',
                $request->measure
            );


        if ($response->successful()) {

            return response()->json([
                'success' =>
                true,
            ]);
        }


        Log::error(
            'Ошибка при одобрении меры',
            $response->json()
        );


        return response()->json(
            [
                'success' =>
                false,

                'error' =>
                'Не удалось сохранить',
            ],
            500
        );
    }


    /**
     * Прокси-экспорт в DOCX.
     */
    public function exportDocx(
        Request $request
    ) {
        try {

            $response =
                Http::timeout(60)
                ->withHeaders([
                    'Content-Type' =>
                    'application/json',

                    'Accept' =>
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                ])
                ->post(
                    $this->apiBaseUrl
                        . '/export/docx',
                    [
                        'content' =>
                        $request->input(
                            'content'
                        ),

                        'filename' =>
                        $request->input(
                            'filename',
                            'export.docx'
                        ),
                    ]
                );


            if ($response->successful()) {

                return response(
                    $response->body(),
                    200
                )
                    ->header(
                        'Content-Type',
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                    )
                    ->header(
                        'Content-Disposition',
                        'attachment; filename="'
                            .
                            (
                                $request->input(
                                    'filename'
                                )
                                ??
                                'export_'
                                . time()
                                . '.docx'
                            )
                            . '"'
                    );
            }


            $error =
                $response->json();


            return response()->json(
                [
                    'success' =>
                    false,

                    'error' =>
                    $error['detail']
                        ??
                        'Ошибка генерации файла',
                ],
                $response->status()
                    ?: 500
            );
        } catch (\Exception $e) {

            Log::error(
                'DOCX export proxy error',
                [
                    'message' =>
                    $e->getMessage(),
                ]
            );


            return response()->json(
                [
                    'success' =>
                    false,

                    'error' =>
                    'Не удалось сгенерировать DOCX файл',
                ],
                500
            );
        }
    }


    /**
     * Прокси-экспорт в Excel.
     */
    public function exportExcel(
        Request $request
    ) {
        try {

            $response =
                Http::timeout(60)
                ->withHeaders([
                    'Content-Type' =>
                    'application/json',

                    'Accept' =>
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                ])
                ->post(
                    $this->apiBaseUrl
                        . '/export/excel',
                    [
                        'content' =>
                        $request->input(
                            'content'
                        ),

                        'filename' =>
                        $request->input(
                            'filename',
                            'export.xlsx'
                        ),
                    ]
                );


            if ($response->successful()) {

                return response(
                    $response->body(),
                    200
                )
                    ->header(
                        'Content-Type',
                        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
                    ->header(
                        'Content-Disposition',
                        'attachment; filename="'
                            .
                            (
                                $request->input(
                                    'filename'
                                )
                                ??
                                'export_'
                                . time()
                                . '.xlsx'
                            )
                            . '"'
                    );
            }


            $error =
                $response->json();


            return response()->json(
                [
                    'success' =>
                    false,

                    'error' =>
                    $error['detail']
                        ??
                        'Ошибка генерации файла',
                ],
                $response->status()
                    ?: 500
            );
        } catch (\Exception $e) {

            Log::error(
                'Excel export proxy error',
                [
                    'message' =>
                    $e->getMessage(),
                ]
            );


            return response()->json(
                [
                    'success' =>
                    false,

                    'error' =>
                    'Не удалось сгенерировать Excel файл',
                ],
                500
            );
        }
    }
}
