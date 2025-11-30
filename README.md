# Чат-бот для анализа постов

AI-powered чат-бот для анализа данных постов из базы данных MWS Tables.

##### Команда:

## Ссылка на рабочий прототип

http://89.169.189.6:8501

Ссылка на видеообзор: https://youtu.be/YourVideoLink

## Быстрый старт

```bash
make install   # Установка
make run       # Запуск
```

- **Frontend:** http://localhost:8501
- **Backend:** http://localhost:8000

## Команды

| Команда | Описание |
|---------|----------|
| `make install` | Установка Python, venv и зависимостей |
| `make run` | Запуск сервера и фронтенда |
| `make stop` | Остановка приложения |
| `make server` | Запуск только сервера |
| `make frontend` | Запуск только фронтенда |
| `make check` | Проверка установки |
| `make clean` | Удаление venv |

## Структура

```
├── app/chat.py          # Streamlit фронтенд
├── server/
│   ├── backend.py       # FastAPI сервер
│   ├── model.py         # AI модель
│   ├── fetch_data.py    # Получение данных
│   └── insert_data.py   # Загрузка данных
└── Makefile
```

## Примеры запросов

- "Покажи топ-5 постов по лайкам"
- "Сравни эффективность постов утром и вечером"
- "Найди посты с более чем 1000 просмотров"

## Технологии

FastAPI, Streamlit, OpenRouter API, LangChain, MWS Tables API
