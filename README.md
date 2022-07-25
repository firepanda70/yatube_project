# YaTube

### Описание
Социальная сеть для малолетних блогеров-бездельников для имитации бурной деятельности

### Технологии
- Python 3
- Django
- SQLite3
- Gunicorn
- Nginx
- pytest

### Запуск проекта в dev-режиме
- Установите и активируйте виртуальное окружение
- Добавьте переменные среды в файл .env:
```
DJANGO_KEY=SECRET
ALLOWED_HOSTS=localhost,127.0.0.1
```
- Установите зависимости из файла requirements.txt
```
pip install -r requirements.txt
```
- Выполните миграции:
```
python manage.py migrate
```
- Загрузите тестовые данные:
```
python manage.py loaddata fixtures.json
# Суперюзер тестовых данных: firep
# Пароль: admin
```
- Запустите сервер:
```
python manage.py runserver
```
