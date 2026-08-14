<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use App\Models\Conversation;
use App\Models\Message;
use Illuminate\Support\Str;
use Illuminate\Support\Facades\Storage;

class ClimateController extends Controller
{
    private $apiBaseUrl;

    public function __construct()
    {
        $this->apiBaseUrl = env('CLIMATE_API_URL', 'http://localhost:8001');
    }

    /**
     * Показать интерфейс системы
     *
     * @return \Illuminate\Contracts\View\View|\Illuminate\Http\RedirectResponse
     */

    public function showInterface()
    {
        $user = auth()->user();

        // Администратор работает только через админ-панель
        if ($user->role === 'admin') {
            return redirect()->route('admin.climate');
        }

        $conversations = $user
            ->conversations()
            ->orderBy('last_interaction_at', 'desc')
            ->take(10)
            ->get();

        return view(
            'climate.index',
            compact('conversations')
        );
    }

    /**
     * Начать новый диалог
     */
    public function newConversation()
    {
        $conversation = Conversation::create([
            'user_id' => auth()->id(),
            'title' => 'Новый диалог',
            'last_interaction_at' => now()
        ]);

        return response()->json([
            'success' => true,
            'conversation_id' => $conversation->id
        ]);
    }

    /**
     * Получить историю диалога
     */
    public function getConversation($id)
    {
        $conversation = Conversation::where('user_id', auth()->id())
            ->with('messages')
            ->findOrFail($id);

        return response()->json([
            'success' => true,
            'conversation' => $conversation
        ]);
    }

    /**
     * Обработать запрос пользователя с сохранением в БД и контекстом
     */
    public function askQuestion(Request $request)
    {
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
                'exists:conversations,id,user_id,' . auth()->id(),
            ],

            'request_id' => [
                'required',
                'string',
                'max:100',
            ],
        ]);


        /*
     * -----------------------------------------------------
     * 1. Сначала создаём / получаем диалог.
     *
     * Это специально находится ДО обращения к Python.
     * Даже если Python недоступен, диалог уже существует.
     * -----------------------------------------------------
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
     * -----------------------------------------------------
     * 2. Контекст.
     *
     * В контекст модели отправляем только успешные ответы.
     *
     * Сообщения вроде:
     * "Не удалось подключиться к сервису"
     * не должны становиться частью LLM-контекста.
     * -----------------------------------------------------
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
         * -------------------------------------------------
         * 3. Python API.
         * -------------------------------------------------
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
         * -------------------------------------------------
         * 4. Успешный ответ.
         * -------------------------------------------------
         */
            if ($response->successful()) {

                $data =
                    $response->json();


                $answer =
                    $data['answer']
                    ??
                    'Ошибка генерации ответа';


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
                            ??
                            'success',
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
         * -------------------------------------------------
         * 5. Python доступен,
         * но вернул HTTP-ошибку.
         * -------------------------------------------------
         */

            Log::error(
                'Ошибка Climate API',
                [
                    'status' =>
                    $response->status(),

                    'body' =>
                    $response->body(),
                ]
            );


            $errorMessage =
                'Сервис временно недоступен. Попробуйте позже.';


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

                    'conversation_id' =>
                    $conversationId,
                ],
                500
            );
        } catch (\Illuminate\Http\Client\ConnectionException $e) {

            /*
         * -------------------------------------------------
         * 6. Python вообще недоступен.
         *
         * Это как раз твой случай со скриншота.
         * -------------------------------------------------
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

                    'conversation_id' =>
                    $conversationId,
                ],
                500
            );
        } catch (\Throwable $e) {

            /*
         * -------------------------------------------------
         * 7. Любая другая непредвиденная ошибка.
         * -------------------------------------------------
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
                'success' => true,
            ]);
        } catch (\Exception $e) {

            /*
         * Для STOP пользователю ошибка не показывается.
         *
         * Клиентская генерация уже будет остановлена
         * через AbortController.
         */
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
                'success' => true,
            ]);
        }
    }
    /**
     * Проверить статус сервиса
     */
    public function checkHealth()
    {
        try {
            $response = Http::timeout(10)->get($this->apiBaseUrl . '/health');

            return response()->json([
                'status' => $response->successful() ? 'healthy' : 'unhealthy',
                'api_status' => $response->status()
            ]);
        } catch (\Exception $e) {
            return response()->json([
                'status' => 'unhealthy',
                'error' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Получить список диалогов пользователя
     */
    public function getConversations()
    {
        $conversations = auth()->user()->conversations()
            ->orderBy('last_interaction_at', 'desc')
            ->get()
            ->map(function ($conversation) {
                // Берем последнюю пару для отображения в списке
                $lastPair = $conversation->messages()->orderBy('interaction_time', 'desc')->first();

                return [
                    'id' => $conversation->id,
                    'title' => $conversation->title ?? ($lastPair ? Str::limit($lastPair->question, 50) : 'Без названия'),
                    'last_interaction_at' => $conversation->last_interaction_at->format('d.m.Y H:i'),
                    'pair_count' => $conversation->messages()->count(),
                    'last_question' => $lastPair ? Str::limit($lastPair->question, 70) : null,
                    'last_answer_preview' => $lastPair ? Str::limit(strip_tags($lastPair->answer), 100) : null
                ];
            });

        return response()->json([
            'success' => true,
            'conversations' => $conversations
        ]);
    }

    /**
     * Удалить диалог
     */
    public function deleteConversation($id)
    {
        $conversation = Conversation::where(
            'user_id',
            auth()->id()
        )->findOrFail($id);


        $conversation->delete();


        return response()->json([
            'success' => true,
        ]);
    }

    /**
     * Одобрить мероприятие
     */
    public function approveMeasure(Request $request)
    {
        $request->validate([
            'measure.name' => 'required|string',
            'measure.mitigation' => 'nullable|string',
            'measure.adaptation' => 'required|string',
            'measure.relevance' => 'required|string',
            'measure.responsible' => 'required|string',
            'source_question' => 'nullable|string',
        ]);

        $response = Http::timeout(10)
            ->post($this->apiBaseUrl . '/approve-measure', $request->measure);

        if ($response->successful()) {
            return response()->json(['success' => true]);
        } else {
            \Log::error('Ошибка при одобрении меры', $response->json());
            return response()->json(['success' => false, 'error' => 'Не удалось сохранить'], 500);
        }
    }

    /**
     * Прокси-экспорт в DOCX (через Python API)
     */
    public function exportDocx(Request $request)
    {
        try {
            $response = Http::timeout(60)
                ->withHeaders([
                    'Content-Type' => 'application/json',
                    'Accept' => 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                ])
                ->post($this->apiBaseUrl . '/export/docx', [
                    'content' => $request->input('content'),
                    'filename' => $request->input('filename', 'export.docx')
                ]);

            if ($response->successful()) {
                return response($response->body(), 200)
                    ->header('Content-Type', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                    ->header('Content-Disposition', 'attachment; filename="' .
                        ($request->input('filename') ?? 'export_' . time() . '.docx') . '"');
            }

            $error = $response->json();
            return response()->json([
                'success' => false,
                'error' => $error['detail'] ?? 'Ошибка генерации файла'
            ], $response->status() ?: 500);
        } catch (\Exception $e) {
            Log::error('DOCX export proxy error', ['message' => $e->getMessage()]);
            return response()->json([
                'success' => false,
                'error' => 'Не удалось сгенерировать DOCX файл'
            ], 500);
        }
    }

    /**
     * Прокси-экспорт в Excel (через Python API)
     */
    public function exportExcel(Request $request)
    {
        try {
            $response = Http::timeout(60)
                ->withHeaders([
                    'Content-Type' => 'application/json',
                    'Accept' => 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                ])
                ->post($this->apiBaseUrl . '/export/excel', [
                    'content' => $request->input('content'),
                    'filename' => $request->input('filename', 'export.xlsx')
                ]);

            if ($response->successful()) {
                return response($response->body(), 200)
                    ->header('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    ->header('Content-Disposition', 'attachment; filename="' .
                        ($request->input('filename') ?? 'export_' . time() . '.xlsx') . '"');
            }

            $error = $response->json();
            return response()->json([
                'success' => false,
                'error' => $error['detail'] ?? 'Ошибка генерации файла'
            ], $response->status() ?: 500);
        } catch (\Exception $e) {
            Log::error('Excel export proxy error', ['message' => $e->getMessage()]);
            return response()->json([
                'success' => false,
                'error' => 'Не удалось сгенерировать Excel файл'
            ], 500);
        }
    }
}
