# Система рекомендации адаптационных мероприятий к изменениям климата

## Описание

Информационная система для оперативного подбора адаптационных мероприятий, направленных на снижение последствий климатических рисков в Тюменской области. Система использует мультиагентный подход на базе LLM-моделей и векторную базу знаний для предоставления персонализированных рекомендаций.

## Запуск

### Создать базу данных postgres на порту 5432 под названием "climate"

### Python RAG

```bash
cd python
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python scripts/loadcsv.py
python scripts/load_xlsx.py
python scripts/createvector.py
uvicorn main:app --host 0.0.0.0 --port 8001
```

### Laravel

```bash
cd laravel
php artisan migrate
php artisan tinker
use App\Models\User;
User::create([
    'name' => 'имя',
    'email' => 'почта',
    'password' => bcrypt('пароль')
]);
exit
php artisan serve
```
