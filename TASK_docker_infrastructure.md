# Задача: Докеризация нескольких Django-проектов с общей инфраструктурой

## Контекст

Нужно создать с нуля инфраструктуру для запуска нескольких независимых Django-проектов
на одном сервере с одним доменом. Проекты не связаны между собой функционально,
но делят общие ресурсы: nginx, PostgreSQL, Redis.

---

## Архитектура

### Репозитории (создать все четыре)

```
mysite-infrastructure/   ← общий "клей": nginx, postgres, redis, сеть
mysite-groceries/        ← Django: список покупок
mysite-trading/          ← Django: торговля игровыми предметами
mysite-budget/           ← Django: домашняя бухгалтерия
```

### URL-структура

```
groceries.mysite.com  →  контейнер groceries_web:8000
trading.mysite.com    →  контейнер trading_web:8000
budget.mysite.com     →  контейнер budget_web:8000
```

### Сеть

Все контейнеры подключены к общей Docker-сети `shared_net`.
Сеть создаётся в infrastructure-репо, проекты подключаются через `external: true`.

### База данных

Один контейнер PostgreSQL в infrastructure.
У каждого проекта своя база внутри него: `groceries_db`, `trading_db`, `budget_db`.

---

## Что нужно создать

### 1. mysite-infrastructure/

```
mysite-infrastructure/
├── docker-compose.yml       # nginx + postgres + redis + shared_net
├── .env.example             # переменные для БД
└── nginx/
    └── nginx.conf           # роутинг по поддоменам
```

**docker-compose.yml** должен:
- Создавать сеть `shared_net` с явным именем
- Запускать postgres:15 с volume для данных
- Запускать redis:alpine
- Запускать nginx с роутингом к контейнерам проектов по имени

**nginx.conf** должен:
- Роутить `groceries.mysite.com` → `http://groceries_web:8000`
- Роутить `trading.mysite.com` → `http://trading_web:8000`
- Роутить `budget.mysite.com` → `http://budget_web:8000`

---

### 2. Каждый Django-проект (groceries / trading / budget)

Структура одинаковая для всех трёх:

```
mysite-<name>/
├── Dockerfile                   # Python 3.11, gunicorn, без dev-зависимостей
├── docker-compose.yml           # локальная разработка: свой postgres
├── docker-compose.prod.yml      # продакшн: подключение к shared_net
├── .env.example                 # DATABASE_URL, SECRET_KEY, DEBUG
├── requirements.txt
└── <name>/                      # Django-проект
    ├── manage.py
    ├── settings.py              # конфиг через переменные окружения
    └── <name>/
        ├── settings.py
        ├── urls.py
        └── wsgi.py
```

**docker-compose.yml** (локальная разработка):
- Сервис `web`: билдится из Dockerfile, порт 8000:8000
- Сервис `db`: postgres:15, своя база, только для локальной разработки
- Переменные из `.env`

**docker-compose.prod.yml** (продакшн):
- Только сервис `web`
- `expose: ["8000"]` (не `ports`)
- Подключение к `shared_net` через `external: true`
- Имя контейнера явно: `container_name: groceries_web` (или trading_web / budget_web)

**Dockerfile**:
- `FROM python:3.11-slim`
- Копирует requirements.txt, устанавливает зависимости
- Запускает через gunicorn, не dev-сервер

**settings.py**:
- `SECRET_KEY` из переменной окружения
- `DEBUG` из переменной окружения
- `DATABASE_URL` через django-environ или dj-database-url
- `ALLOWED_HOSTS` включает поддомен проекта

---

## Порядок выполнения

Делай строго по шагам, после каждого шага жди подтверждения.

**Шаг 1** — mysite-infrastructure: docker-compose.yml + nginx.conf + .env.example

**Шаг 2** — mysite-groceries: Dockerfile + оба docker-compose + Django-проект + settings

**Шаг 3** — mysite-trading: аналогично groceries

**Шаг 4** — mysite-budget: аналогично groceries

**Шаг 5** — README.md в infrastructure с инструкцией по деплою:
```bash
# Первый запуск
cd mysite-infrastructure && docker compose up -d

# Деплой проекта
cd mysite-groceries
docker compose -f docker-compose.prod.yml up -d

# Обновление проекта
git pull && docker compose -f docker-compose.prod.yml up -d --build
```

---

## Ограничения

- Не создавай сложный бизнес-код внутри Django-проектов — только базовая структура, главная страница с текстом названия проекта
- Не настраивай SSL (это отдельная задача)
- Не используй docker swarm или kubernetes
- Имена контейнеров должны совпадать с тем что прописано в nginx.conf

---

## Проверка результата

После выполнения я должен уметь:

```bash
# Поднять инфраструктуру
cd mysite-infrastructure && docker compose up -d

# Поднять один проект локально (без инфраструктуры)
cd mysite-groceries && docker compose up -d
# открыть localhost:8000 — видна страница "Groceries"

# Поднять проект на продакшне
cd mysite-groceries
docker compose -f docker-compose.prod.yml up -d
# nginx роутит groceries.mysite.com на этот контейнер
```
