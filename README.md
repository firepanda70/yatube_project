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
- Создайте в корневой директоории файл .env c переменной DJANGO_KEY:
```
DJANGO_KEY=SECRET
```
- Установите зависимости из файла requirements.txt
```
pip install -r requirements.txt
```
- Выполните миграции:
```
python manage.py migrate
```
- В папке с файлом manage.py выполните команду:
```
python manage.py runserver
```
