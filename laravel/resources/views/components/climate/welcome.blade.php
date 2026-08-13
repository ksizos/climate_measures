@php
$examples = [
[
'text' => 'Последствия урагана на юге Тюменской области',
'icon' => 'icons/hurricane.svg',
],
[
'text' => 'Прогноз сильных ливней на территории Ишима',
'icon' => 'icons/thunder.svg',
],
[
'text' => 'Риск возникновения лесных пожаров в ХМАО',
'icon' => 'icons/wildfire.svg',
],
[
'text' => 'Адаптационные меры для высоких температур в ЯНАО',
'icon' => 'icons/heat.svg',
],
[
'text' => 'Риск весенних паводков в бассейне Иртыша',
'icon' => 'icons/flood.svg',
],
[
'text' => 'Вероятность учащения засух в Тобольске',
'icon' => 'icons/drought.svg',
],
];

$randomExamples = collect($examples)->shuffle()->take(4);
@endphp

<div id="welcomeMessage" class="welcome-message text-center">

    <h2 class="welcome_header mb-4">
        Информационная система для рекомендации адаптационных мероприятий к изменениям климата
    </h2>

    <p class="welcome_text mb-5">
        Опишите климатический риск или ситуацию — система проанализирует данные
        и предложит релевантные адаптационные мероприятия
    </p>

    <p class="welcome_suggestion mb-4">
        Попробуйте готовые примеры запросов
    </p>

    <div class="d-flex align-items-center justify-content-center gap-3">

        @foreach($randomExamples as $example)

        <div
            class="d-inline-flex align-items-end justify-content-between flex-row example_card shadow-sm gap-2 p-3"
            data-question="{{ $example['text'] }}" role="button">

            <div class="d-flex flex-column align-items-start justify-content-center example_info p-0 m-0">

                <img
                    class="mb-2"
                    src="{{ asset($example['icon']) }}"
                    alt="Иконка" />

                <p class="p-0 m-0 text-start example_text">
                    {{ $example['text'] }}
                </p>

            </div>

            <div class="p-0 m-0">
                <img
                    class="send_example"
                    src="{{ asset('icons/send.svg') }}"
                    alt="Отправить" />
            </div>

        </div>

        @endforeach

    </div>

</div>
