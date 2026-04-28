---
name: supabase
description: Supabase database safety rules. Use when working with self-hosted Supabase via MCP. Enforces safe database operations and prevents destructive actions.
---

## 🔴 CRITICAL RULES — MUST FOLLOW ALWAYS

### 1. NEVER DELETE OR DROP TABLES
- **ЗАПРЕЩЕНО** выполнять `DROP TABLE`, `DROP SCHEMA`, или любые команды, удаляющие таблицы
- **ЗАПРЕЩЕНО** выполнять миграции, содержащие `DROP TABLE` или `DROP COLUMN`
- Если пользователь просит удалить таблицу — **ОБЯЗАТЕЛЬНО** предупреди о рисках и предложи альтернативу:
  - Переименовать таблицу (`ALTER TABLE old_name RENAME TO old_name_backup`)
  - Добавить флаг `is_deleted` / `archived_at` для мягкой deletion
  - Создать миграцию с комментарием о депрекации

### 2. NEVER DROP COLUMNS
- **ЗАПРЕЩЕНО** выполнять `ALTER TABLE ... DROP COLUMN` без явного подтверждения и бэкапа
- Вместо удаления колонки пометь её как неиспользуемую через комментарий:
  ```sql
  COMMENT ON COLUMN users.old_field IS 'DEPRECATED: Do not use. Migrated to new_field';
  ```

### 3. ALWAYS BACKUP BEFORE STRUCTURAL CHANGES
- Перед любыми изменениями структуры (`ALTER TABLE`, добавление/изменение колонок) предложи сделать бэкап:
  ```sql
  -- Через pg_dump в командной строке
  pg_dump -U postgres -h localhost -d postgres > backup_YYYYMMDD.sql
  ```

### 4. SAFE MIGRATION PRACTICES
- Все миграции должны быть **обратимыми** (reversible)
- Добавляй `IF NOT EXISTS` / `IF EXISTS` где возможно:
  ```sql
  ALTER TABLE users ADD COLUMN IF NOT EXISTS phone TEXT;
  ```
- Никогда не изменяй тип данных существующей колонки напрямую — создай новую, перенеси данные, затем удали старую (отдельной миграцией)

### 5. ROW LEVEL SECURITY (RLS)
- Никогда не отключай RLS на таблицах без веской причины
- При создании новых таблиц всегда добавляй RLS политики:
  ```sql
  ALTER TABLE new_table ENABLE ROW LEVEL SECURITY;
  CREATE POLICY "Users can view their own data" ON new_table
    FOR SELECT USING (auth.uid() = user_id);
  ```

### 6. NEVER MODIFY AUTH SYSTEM TABLES DIRECTLY
- Не изменяй напрямую таблицы `auth.users`, `auth.sessions` и другие системные таблицы auth
- Используй MCP инструменты: `create_auth_user`, `update_auth_user`, `delete_auth_user`

### 7. PROTECT PRODUCTION DATA
- Никогда не выполняй `TRUNCATE` на таблицах с данными
- Никогда не выполняй `DELETE FROM table` без `WHERE` clause
- При массовом обновлении данных всегда используй транзакции:
  ```sql
  BEGIN;
  -- операции
  COMMIT;
  ```

## ✅ SAFE OPERATIONS (Allowed)

Эти операции безопасны и разрешены:
- `SELECT` запросы (чтение данных)
- `INSERT` новых записей
- `UPDATE` существующих записей с `WHERE`
- Создание новых таблиц (`CREATE TABLE`)
- Добавление новых колонок (`ADD COLUMN`)
- Создание индексов (`CREATE INDEX`)
- Просмотр схемы (`list_tables`, `list_table_columns`)
- Просмотр миграций (`list_migrations`)
- Применение новых миграций (`apply_migration`) — если они безопасны

## ⚠️ DANGEROUS OPERATIONS (Require Explicit Confirmation)

Эти операции требуют **явного подтверждения** пользователя с объяснением последствий:
- `ALTER TABLE ... DROP COLUMN`
- `ALTER TABLE ... ALTER COLUMN ... TYPE` (изменение типа)
- `ALTER TABLE ... RENAME COLUMN`
- Отключение RLS (`ALTER TABLE ... DISABLE ROW LEVEL SECURITY`)
- Удаление индексов (`DROP INDEX`)
- Удаление ограничений (`DROP CONSTRAINT`)

## 📋 PRE-FLIGHT CHECKLIST

Перед выполнением любой DDL операции проверь:
1. [ ] Есть ли бэкап?
2. [ ] Обратима ли операция?
3. [ ] Не затронет ли это существующие данные?
4. [ ] Нужна ли транзакция?
5. [ ] Обновлена ли документация/комментарии?

Если хотя бы один пункт вызывает сомнения — **ОСТАНОВИСЬ** и уточни у пользователя.

## 🛠 MCP TOOLS USAGE

При работе с MCP сервером `selfhosted-supabase`:
- Используй `list_tables` для просмотра структуры
- Используй `list_table_columns` для изучения колонок
- Используй `apply_migration` для безопасных изменений
- Используй `execute_sql` с `read_only: true` для чтения
- Используй `get_advisors` type=`security` для проверки безопасности

## 🚨 VIOLATION CONSEQUENCES

Нарушение правил 1-3 (удаление таблиц/колонок без подтверждения) может привести к **необратимой потере данных**. Всегда перестраховывайся и уточняй у пользователя перед деструктивными действиями.
