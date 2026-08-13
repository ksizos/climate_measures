<div class="chat-input-container d-flex flex-column">

    <div class="chat-input position-relative">

        <textarea
            id="question"
            name="question"
            class="form-control prompt-field"
            placeholder="Опишите климатический риск или задайте вопрос..."
            rows="3"></textarea>

        <div class="prompt_buttons position-absolute">

            <button
                id="submitBtn"
                type="button"
                class="btn p-0 m-0"
                title="Отправить"
                disabled>

                <img
                    class="submit-icon"
                    src="{{ asset('icons/submit.svg') }}"
                    alt="Отправить">

                <img
                    class="stop-icon"
                    src="{{ asset('icons/stop.svg') }}"
                    alt="Остановить">

            </button>

        </div>

    </div>

    <div class="muted_back"></div>

</div>
