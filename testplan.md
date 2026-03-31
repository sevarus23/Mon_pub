# Тест-план для проекта Mon_pub

## Контекст

Mon_pub -- платформа агрегации научных статей Университета Иннополис. Собирает публикации из CrossRef и OpenAlex API, хранит в PostgreSQL с нечётким поиском (pg_trgm), обогащает квартилями SJR из CSV, предоставляет веб-интерфейс на Next.js для поиска/фильтрации. **Тестов сейчас нет вообще.** Цель -- создать набор тестов для защиты от регрессии при изменениях кода.

---

## Уровень 1: Unit-тесты (чистые функции, без инфраструктуры)

### 1.1 `type_mapping.py` -- нормализация типов статей
**Приоритет: Высокий** | Файл: `backend/app/utils/type_mapping.py`

| # | Тест-кейс | Вход | Ожидание |
|---|-----------|------|----------|
| 1 | Известный тип CrossRef | `"journal-article"` | `"Articles"` |
| 2 | Известный тип OpenAlex | `"proceedings-article"` | `"Conference materials"` |
| 3 | Неизвестный тип -> "Other" | `"grant"` | `"Other"` |
| 4 | None на входе | `None` | `None` |
| 5 | Пустая строка | `""` | `None` |
| 6 | Все 26 записей TYPE_MAPPING дают одну из 8 категорий | итерация | Корректные значения |

### 1.2 `crossref.py` -- парсинг данных
**Приоритет: Критический** | Файл: `backend/app/services/crossref.py`

**`_parse_date()`** (9 кейсов):
- Полная дата из `published-online` -> `date(2024, 3, 15)`
- Год+месяц (день=1) | Год только (месяц+день=1)
- Fallback: `published-print` -> `created` -> `None`
- Невалидная дата (month=13) -> fallback
- Пустой `date-parts` -> `None`

**`_parse_authors()`** (6 кейсов):
- Стандартный список -> `"John Doe, Jane Smith"`
- Отсутствие `given`/`family` поля
- Пустой/отсутствующий список -> `"Unknown"`

**`_doi_hash()`**: детерминированность, длина 16, уникальность

**`_is_ignored()`**: известный DOI -> True, обычный -> False

### 1.3 `openalex.py` -- парсинг данных
**Приоритет: Критический** | Файл: `backend/app/services/openalex.py`

**`_has_innopolis_affiliation()`** (6 кейсов):
- Совпадение в raw_affiliation_strings -> True
- Регистронезависимость ("INNOPOLIS") -> True
- Нет совпадения | Пустой список | Отсутствие ключа -> False

**`_parse_date()`**: ISO дата, None, невалидная строка
**`_parse_authors()`**: стандартный список, пустой -> "Unknown"
**`_extract_openalex_id()`**: URL -> ID

### 1.4 `sjr.py` -- парсинг CSV
**Приоритет: Высокий** | Файл: `backend/app/services/sjr.py`

| # | Тест-кейс | Ожидание |
|---|-----------|----------|
| 1 | ISSN 8 символов -> добавление дефиса | `"14726483"` -> `"1472-6483"` |
| 2 | Несколько ISSN через запятую | Оба замаплены |
| 3 | Невалидный квартиль (Q5, пустой) | Пропускается |
| 4 | Только Q1-Q4 принимаются | Корректная фильтрация |
| 5 | Разделитель -- точка с запятой | Парсится корректно |

### 1.5 `schemas/article.py` -- валидация Pydantic
**Приоритет: Средний** | Файл: `backend/app/schemas/article.py`

- `ArticleFilters`: дефолты (page=1, per_page=20), отклонение page=0, per_page=101
- `ArticleCreate`: обязательные поля (num_id, title, authors, source)
- `SortBy` enum: отклонение невалидных значений

### 1.6 Frontend утилиты
**Приоритет: Средний** | Файл: `frontend/types/index.ts`

- `getTypeLabel()`: известный/неизвестный/null тип
- `getQuartileClass()`: Q1 -> класс, null -> пусто
- `isNewToday()`: сегодня -> true, вчера -> false, null -> false
- `formatDate()`: ISO дата -> русский формат, null -> "—"

---

## Уровень 2: Интеграционные тесты (требуют PostgreSQL)

### 2.1 `ArticleRepository` -- операции с БД
**Приоритет: Критический** | Файл: `backend/app/repositories/article.py`

**`bulk_upsert()`** (7 кейсов):
- Вставка с DOI -> rowcount=1
- Дубликат DOI -> без ошибки, count=0
- Вставка без DOI (по num_id) -> rowcount=1
- Дубликат num_id -> count=0
- Пустой список -> 0
- Микс DOI и не-DOI в одном батче

**`get_filtered()`** (18 кейсов):
- Пагинация: 25 записей, page=1/per_page=10 -> total=25, pages=3, items=10
- Фильтры: journal_name, date_from/to, quartile, source, year, article_type
- Нечёткий поиск по title с опечаткой -> находит (pg_trgm, threshold 0.3)
- Нечёткий поиск по author с опечаткой -> находит (word_similarity > 0.6)
- Сортировка: по дате (desc), по цитированиям (asc)
- Комбинация фильтров: journal + year
- Пустой результат для несуществующего фильтра

**`get_stats()`** (8 кейсов):
- Общее количество, уникальные авторы, new_today, new_this_week
- Агрегация by_year, by_source, top_journals (лимит 10)
- Пустая БД -> нули

**Справочные эндпоинты** (6 кейсов):
- `get_journals()`: distinct, сортировка, fuzzy search
- `get_authors()`: разделение запятой, исключение "Unknown", лимит 50
- `get_quartiles()`: только не-null
- `get_types()`: исключение null и пустых

**`normalize_all_types()`**: обновление типа, пропуск уже нормализованных, подсчёт

### 2.2 SJR Quartile Update
**Приоритет: Высокий** | Файл: `backend/app/services/sjr.py`

- Совпадение ISSN + null квартиль -> обновление
- Существующий квартиль -> не перезаписывается
- Отсутствие CSV -> возврат 0 + warning

---

## Уровень 3: API-тесты (контракт эндпоинтов)

**Приоритет: Критический** | Файл: `backend/app/routers/articles.py`

**`GET /api/articles`** (10 кейсов):
- Дефолтные параметры -> 200, PaginatedArticles
- Пагинация -> page/per_page в ответе
- page=0 -> 422 | per_page=101 -> 422
- Все фильтры вместе -> 200
- Невалидный sort_by -> 422

**`GET /api/articles/{id}`**: существующий -> 200, несуществующий -> 404, невалидный -> 422

**`GET .../journals, /types, /authors, /quartiles`**: 200, list[str], поддержка search

**`GET /api/articles/stats`**: 200, StatsOut, корректные типы

**`POST .../parse, /update-quartiles, /normalize-types`**: 200, ParseResponse

**`GET /health`**: 200, `{"status": "ok"}`

---

## Уровень 4: Тесты сервисов (мокирование HTTP)

### 4.1 CrossRef -- `parse_crossref()`
**Приоритет: Высокий** | Mock: respx | Файл: `backend/app/services/crossref.py`

- Одна страница, 2 статьи -> вставлено 2
- Мультистраничная пагинация (offset) -> все обработаны
- Пустой items -> возврат 0
- Игнорируемый DOI -> не вставлен
- HTTP 500 -> retry (tenacity), 3 неудачи -> graceful stop
- since_date -> корректный filter в запросе
- num_id формат: `cr_` + 16 символов

### 4.2 OpenAlex -- `parse_openalex()`
**Приоритет: Высокий** | Mock: respx | Файл: `backend/app/services/openalex.py`

- Cursor-пагинация (next_cursor)
- Фильтрация: нет Innopolis аффилиации -> пропуск
- Фильтрация: год < 2012 -> пропуск
- DOI URL -> чистый DOI (`https://doi.org/...` -> `10.1234/...`)
- num_id формат: `oa_` + OpenAlex ID
- ISSN fallback: issn_l -> issn[0]
- ROR ID в параметрах запроса

### 4.3 Scheduler -- `run_parse()`
**Приоритет: Средний** | Mock: patch сервисов | Файл: `backend/app/services/scheduler.py`

- since_date = last_date - 7 дней
- last_date=None -> since_date=None
- Параллельный вызов (asyncio.gather)
- Последовательность: parse -> quartiles -> types

---

## Уровень 5: E2E-тесты (Playwright)

**Приоритет: Высокий** | Инфраструктура: полный стек через Docker Compose

| # | Сценарий | Проверка |
|---|----------|----------|
| 1 | Загрузка страницы | Список статей отображается |
| 2 | Поиск по ключевому слову | Результаты обновляются после debounce |
| 3 | Фильтр по журналу | Результаты отфильтрованы |
| 4 | Фильтр по квартилю | Только Q1/Q2/... статьи |
| 5 | Фильтр по типу статьи | Корректная фильтрация |
| 6 | Фильтр по диапазону лет | Только статьи заданных лет |
| 7 | Сброс фильтров ("Сбросить") | Все фильтры очищены |
| 8 | Пагинация вперёд/назад | Корректные страницы |
| 9 | Сортировка по цитированиям | Корректный порядок |
| 10 | DOI-ссылка на карточке | Ведёт на `doi.org` |
| 11 | Бейдж квартиля | Отображается с правильным цветом |
| 12 | Sidebar со статистикой | Графики загружены |
| 13 | URL отражает фильтры | Deep link работает |
| 14 | Пустой результат | "Результаты: 0" |

---

## Уровень 6: Нагрузочные тесты

**Приоритет: Низкий** | Инструмент: Locust или k6

| # | Сценарий | Порог |
|---|----------|-------|
| 1 | GET /api/articles (50 concurrent) | p95 < 500ms |
| 2 | Fuzzy search (20 concurrent) | p95 < 1000ms |
| 3 | GET /api/articles/stats (20 concurrent) | p95 < 1000ms |
| 4 | bulk_upsert 1000 статей | < 5s |

---

## Инфраструктура тестирования

### Backend
- **Фреймворк**: pytest + pytest-asyncio
- **Мокирование HTTP**: respx (для httpx)
- **БД для интеграционных тестов**: testcontainers-python (PostgreSQL с pg_trgm) или Docker Compose DB
- **Фикстуры**: conftest.py с AsyncSession + transaction rollback per test
- **Зависимости**: `pytest, pytest-asyncio, pytest-cov, respx, testcontainers[postgres]`

### Frontend
- **Unit**: Jest + ts-jest (или Vitest)
- **E2E**: Playwright
- **Зависимости**: `jest, @testing-library/react, @testing-library/jest-dom, @playwright/test`

### Структура каталогов

```
backend/tests/
  unit/
    test_type_mapping.py
    test_crossref_parsers.py
    test_openalex_parsers.py
    test_sjr_parser.py
    test_schemas.py
  integration/
    conftest.py
    test_article_repository.py
    test_sjr_update.py
  api/
    conftest.py
    test_articles_endpoints.py
    test_health.py
  service/
    test_crossref_service.py
    test_openalex_service.py
    test_scheduler.py

frontend/
  __tests__/
    unit/types.test.ts
    components/{ArticleCard,Pagination,Filters}.test.tsx
  e2e/
    search.spec.ts
    filters.spec.ts
    pagination.spec.ts
```

---

## Порядок реализации

| Фаза | Что | Почему |
|-------|-----|--------|
| **1. Немедленно** | Unit-тесты чистых функций (1.1-1.4) + Schema-тесты (1.5) | Быстро, без инфраструктуры, ловят логические ошибки |
| **2. Краткосрочно** | API-тесты (Уровень 3) + Repository интеграция (2.1) | Основная защита от регрессии при изменениях |
| **3. Среднесрочно** | Сервисные тесты с respx (4.1-4.2) + Frontend unit (1.6) | Защита интеграций с внешними API |
| **4. После стабилизации** | E2E Playwright (Уровень 5) | Полный user flow |
| **5. По необходимости** | Нагрузочные тесты (Уровень 6) | При росте данных |

---

## Найденный баг (ИСПРАВЛЕН в этом коммите)

`frontend/types/index.ts`: интерфейс `Article` объявлял `num_id: number | null`, но бэкенд отправляет `string` (значения вроде `"cr_abc123..."`, `"oa_W12345"`).
**Статус:** Исправлено — `num_id` изменён на `string`.
