<div class="chat-input-container position-relative">
    <div class="position-relative">
        <textarea
            id="question"
            name="question"
            class="form-control prompt-field"
            placeholder="Введите ваш запрос о климатических рисках..."
            rows="3"></textarea>

        <div class="prompt_buttons position-absolute">
            <button
                id="submitBtn"
                type="button"
                class="btn p-0 m-0"
                title="Отправить"
                disabled>
                <img src="{{ asset('icons/submit.png') }}" alt="Отправить" />
            </button>
        </div>
    </div>

</div>
