# Mon_pub -- Мониторинг публикационной активности

![Tests](https://github.com/sevarus23/Mon_pub/actions/workflows/tests.yml/badge.svg)

Платформа агрегации научных публикаций Университета Иннополис. Собирает статьи из **CrossRef** и **OpenAlex**, обогащает квартилями из рейтинга **SJR**, предоставляет веб-интерфейс для поиска и фильтрации.

## Архитектура

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│  CrossRef   │────>│              │     │                │
│    API      │     │   Backend    │────>│  PostgreSQL    │
│             │     │  (FastAPI)   │     │  + pg_trgm     │
├─────────────┤     │              │     └────────────────┘
│  OpenAlex   │────>│  :8001       │
│    API      │     └──────┬───────┘
└─────────────┘            │
                           │ REST API
                    ┌──────┴───────┐
                    │   Frontend   │
                    │  (Next.js)   │
                    │  :3000       │
                    └──────────────┘
```

| Компонент | Стек |
|-----------|------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic, httpx, tenacity |
| Frontend | Next.js 14, React 18, Tailwind CSS, TypeScript |
| База данных | PostgreSQL 16 с расширением `pg_trgm` (нечёткий поиск) |
| Данные SJR | CSV из [SCImago Journal Rank](https://www.scimagojr.com/) |

## Быстрый старт

### Требования

- Docker и Docker Compose

### Запуск

```bash
# 1. Клонировать репозиторий
git clone https://github.com/sevarus23/Mon_pub.git
cd Mon_pub

# 2. Настроить переменные окружения
cp backend/.env.template backend/.env

# 3. Запустить backend + БД
cd backend
docker compose up -d

# 4. Запустить frontend (в отдельном терминале)
cd ../frontend
npm install
npm run dev
```

После запуска:
- **API**: http://localhost:8001
- **Swagger UI**: http://localhost:8001/docs
- **Frontend**: http://localhost:3000
- **PgAdmin**: http://localhost:5051

## API

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| GET | `/api/articles` | Список статей с фильтрами, поиском и пагинацией |
| GET | `/api/articles/{id}` | Статья по ID |
| GET | `/api/articles/stats` | Статистика: всего, по годам, по источникам, топ журналов |
| GET | `/api/articles/journals` | Список журналов (с fuzzy search) |
| GET | `/api/articles/authors` | Список авторов (с fuzzy search) |
| GET | `/api/articles/types` | Типы публикаций |
| GET | `/api/articles/quartiles` | Доступные квартили |
| POST | `/api/articles/parse` | Запуск парсинга CrossRef + OpenAlex |
| POST | `/api/articles/update-quartiles` | Обновление квартилей из SJR CSV |
| POST | `/api/articles/normalize-types` | Нормализация типов статей |
| GET | `/health` | Проверка состояния сервиса |

### Параметры фильтрации `GET /api/articles`

`search`, `journal_name`, `author`, `title`, `doi`, `issn`, `date_from`, `date_to`, `year`, `quartile`, `article_type`, `source`, `sort_by`, `sort_order`, `page`, `per_page`

## Тестирование

### Backend (119 тестов)

```bash
cd backend
pip install -r requirements-test.txt
pytest tests/ -v
```

| Уровень | Что проверяется | Кол-во |
|---------|----------------|--------|
| `tests/unit/` | Чистые функции: парсинг дат, авторов, маппинг типов, SJR CSV, Pydantic-схемы | 84 |
| `tests/api/` | Контракт HTTP-эндпоинтов (статус-коды, валидация, формат ответа) | 18 |
| `tests/service/` | Логика сервисов с мокированием HTTP через respx | 17 |

### Frontend (22 теста)

```bash
cd frontend
npm install
npm test
```

Тестируются утилитные функции: `getTypeLabel`, `getQuartileClass`, `isNewToday`, `formatDate`, `buildQuery`.

## CI/CD

GitHub Actions автоматически запускает все тесты на каждый push и pull request в `main`.

Branch Protection настроен так, что **мерж в main невозможен**, если хотя бы один тест не проходит.

## Структура проекта

```
Mon_pub/
├── backend/
│   ├── app/
│   │   ├── config.py          # Настройки (Pydantic Settings)
│   │   ├── database.py        # Async SQLAlchemy engine
│   │   ├── main.py            # FastAPI app + scheduler
│   │   ├── models/            # SQLAlchemy модель Article
│   │   ├── repositories/      # Слой доступа к данным
│   │   ├── routers/           # HTTP-эндпоинты
│   │   ├── schemas/           # Pydantic-схемы
│   │   ├── services/          # Бизнес-логика (CrossRef, OpenAlex, SJR, Scheduler)
│   │   └── utils/             # Маппинг типов публикаций
│   ├── data/                  # SJR CSV файл
│   ├── tests/                 # Тесты (unit, api, service)
│   ├── docker-compose.yml
│   └── requirements.txt
├── frontend/
│   ├── app/                   # Next.js страницы
│   ├── components/            # React-компоненты
│   ├── lib/                   # API-клиент
│   ├── types/                 # TypeScript типы + утилиты
│   └── __tests__/             # Jest тесты
├── .github/workflows/         # CI/CD пайплайн
└── testplan.md                # Полный тест-план проекта
```
