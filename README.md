# Data Warehouse ETL (Data Vault 2.0)

## Описание технического задания

Проект реализует загрузку данных из REST API в корпоративное хранилище данных с использованием методологии Data Vault 2.0.

В качестве источника данных используется REST API:

https://jsonplaceholder.typicode.com/posts

Проект включает:

- слой STG (Staging)
- слой DDS (Detailed Data Store)
- ETL/ELT процессы

---

# Архитектура хранилища

## STG Layer

Слой временного хранения сырых данных.

Таблица:

- `stg.post_stg`

Содержит:
- данные из API
- hash записи
- дату загрузки
- источник данных

---

## DDS Layer (Data Vault 2.0)

### HUB таблицы

#### `dds.hub_user`

Хранит бизнес-ключ пользователей.

#### `dds.hub_post`

Хранит бизнес-ключ постов.

---

### LINK таблицы

#### `dds.link_user_post`

Хранит связи:
- пользователь ↔ пост

---

### SATELLITE таблицы

#### `dds.sat_post_details`

Хранит описательные атрибуты:
- title
- body

Использует:
- `hash_diff`
для отслеживания изменений атрибутов.

---

# Структура проекта

```text
Techinal_Task/
│
├── ETL/
│   ├── ETL1.py
│   └── ETL2.py
│
├── core/
│   └──session.py
│
├── models/
│   └── data_types.py
│
├── DDL/
│   ├── STG.sql
│   └── DDS.sql
│
├── .gitignore
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

# Установка проекта

## 1. Клонирование проекта

```bash
git clone <repository_url>
cd Techinal_Task
```

---

## 2. Создание виртуального окружения

```bash
python3 -m venv venv
```

Активация:

Linux/macOS:

```bash
source venv/bin/activate
```

Windows:

```bash
venv\Scripts\activate
```

---

## 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

---

# Настройка окружения

Создать `.env` файл:

```env
SOURCE_URL= ... - URL адрес на исходный источник данных

SOURCE_SYSTEM= ... - Система/Сайт/Хранилище откуда пришли исходные данные

DATABASE_URL=... - Строка подключения к базе данных.

POSTGRES_USER=... - Пользователь для входа в PostgreSQL
POSTGRES_PASSWORD=... - Пароль необходимый для входа
POSTGRES_DB=... - Название базы данных
```

---

# Запуск PostgreSQL

## Docker Compose

```bash
docker compose up -d
```

Проверка контейнера:

```bash
docker ps
```

---

# ETL Процессы

## ETL1 — загрузка в STG

Загружает данные из REST API в staging слой.

Запуск:

```bash
python ETL/ETL1.py
```

---

## ETL2 — загрузка в DDS

Загружает данные из STG в DDS по модели Data Vault 2.0.

Запуск:

```bash
python ETL/ETL2.py
```

---

# Особенности реализации

## Hash Keys

Для генерации hash-ключей используется:

- SHA-256

---

## Проверка существования таблиц

ETL автоматически:
- проверяет существование таблиц
- выполняет DDL-скрипты при отсутствии таблиц

---

## Защита от дубликатов

Используется конструкция:

```sql
WHERE NOT EXISTS (...)
```

---

# Data Vault 2.0

В проекте реализованы основные сущности Data Vault:

| Тип | Таблица |
|---|---|
| HUB | hub_user |
| HUB | hub_post |
| LINK | link_user_post |
| SATELLITE | sat_post_details |

---

# Автор

Воронков Кирилл Викторович