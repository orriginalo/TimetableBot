# 📅 Telegram-бот для просмотра расписания и изменений

Этот телеграм-бот предназначен для студентов КЭИ | УлГТУ, чтобы быстро и удобно получать **расписание** и **изменения** по своей учебной группе.

Бот поддерживает:

- 📆 Скриншоты расписания:

  - на **сегодня**
  - на **завтра**
  - на **текущую неделю**
  - на **следующую неделю**

- 📝 **Изменения в расписании**
- ⚙️ Гибкие **настройки рассылки**:

  - Выбор группы
  - Получение изменений при появлении новых
  - Уведомления только при наличии изменений для своей группы
  - Отправка только нужной страницы с изменениями

> **Внимание:** для корректной работы бота необходимо запустить отдельный API-сервер, который отвечает за генерацию скриншотов.

🔗 API-репозиторий: **[ссылка](https://github.com/orriginalo/MyBotsAPI)**

---

## 🛠️ Технологии

- Python 3.12 + [Aiogram 3](https://github.com/aiogram/aiogram)
- PostgreSQL
- Docker / Docker Compose
- Скриншоты генерируются через внешний API
- Асинхронные задачи — через планировщик

---

## 📂 Структура проекта

```
├── main.py                 # Точка входа
├── .env.template           # Пример переменных окружения
├── bot/
│   ├── handlers.py         # Хэндлеры Telegram-команд
│   ├── keyboards.py        # Кнопки Telegram-интерфейса
│   ├── middlewares.py      # Middleware для Aiogram
│   ├── config.py           # Загрузка конфигурации
│   ├── scheduler.py        # Отправка расписания по расписанию
│   ├── service/            # Бизнес-логика
│   ├── database/           # Работа с БД (SQLAlchemy)
│   └── requests/           # Работа с API скриншотов
├── utils/                  # Логгеры, парсеры и т.п.
├── docker-compose.yml      # Контейнеризация
├── Dockerfile
└── requirements.txt
```

---

## ⚙️ Переменные окружения (`.env`)

Скопируйте `.env.template` → `.env` и заполните значения:

```env
# Токен вашего Telegram-бота
BOT_TOKEN=...

# Адрес API для получения расписания
API_HOST=...
API_PORT=...

# Путь к данным
DATA_PATH=...

# Логирование
LOG_LEVEL=INFO

# Настройки PostgreSQL
POSTGRES_HOST=...
POSTGRES_PORT=5432
POSTGRES_USER=...
POSTGRES_DB=...
POSTGRES_PASSWORD=...

# Параметры проверок изменений (пока не используются)
ENABLE_CHANGES_CHECK=True
ENABLE_CHANGES_CHECK_INTERVAL=
```

---

## 🚀 Запуск

1. Склонируйте репозиторий

```bash
git clone https://github.com/orriginalo/TimetableBot.git
cd TimetableBot
```

2. Убедитесь, что запущен API
3. Соберите и запустите контейнер:

```bash
cp .env.template .env
docker-compose up --build
```

Бот автоматически подключится к Telegram, PostgreSQL и API.

---

## 🧩 Планируемые улучшения

- Админ-панель
