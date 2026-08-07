export async function checkServiceStatus() {
    const indicator = document.getElementById("statusIndicator");

    if (!indicator) {
        return;
    }

    try {
        const response = await fetch("/climate/health");

        const data = await response.json();

        if (data.status === "healthy") {
            indicator.innerHTML =
                '<span class="text-success">●</span> Сервис доступен';
        } else {
            indicator.innerHTML =
                '<span class="text-danger">●</span> Сервис недоступен';
        }
    } catch (error) {
        indicator.innerHTML =
            '<span class="text-danger">●</span> Ошибка подключения';
    }
}
