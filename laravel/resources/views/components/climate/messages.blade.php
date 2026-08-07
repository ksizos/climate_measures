<div class="chat-container h-100 d-none">
    <div id="chatMessages" class="chat-messages mb-4">
    </div>

    <div id="loading" class="text-center py-4 d-none">
        <div class="d-flex flex-column align-items-center">
            <div class="spinner-border text-primary mb-2" role="status">
                <span class="visually-hidden">Загрузка...</span>
            </div>
            <p class="text-muted mb-1">Обрабатываем запрос...</p>
            <small class="text-muted">Это может занять время</small>
        </div>
    </div>


    <div id="error" class="alert alert-danger mt-3 d-none">
        <div class="d-flex align-items-start">
            <i class="fas fa-exclamation-triangle me-3 mt-1"></i>
            <div class="flex-grow-1">
                <h6 class="alert-heading mb-2">Произошла ошибка</h6>
                <p id="errorMessage" class="mb-2"></p>
            </div>
        </div>
    </div>
</div>
