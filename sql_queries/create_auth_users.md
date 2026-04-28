1. Создаём схему auth и выдаем права
```powershell
docker exec -it supabase-db psql -U postgres -d postgres
```
```sql
-- Создаем схему auth
CREATE SCHEMA IF NOT EXISTS auth;

-- Даем все права postgres на эту схему
GRANT ALL ON SCHEMA auth TO postgres;

-- Даем права на создание таблиц в этой схеме
ALTER DEFAULT PRIVILEGES IN SCHEMA auth GRANT ALL ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA auth GRANT ALL ON SEQUENCES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA auth GRANT ALL ON FUNCTIONS TO postgres;

-- Выходим
\q
```
2. Теперь создадим таблицы вручную (скопируй и вставь одной командой)
```powershell
docker exec -it supabase-db psql -U postgres -d postgres
```
```sql
-- Таблица users
CREATE TABLE IF NOT EXISTS auth.users (
    instance_id uuid NULL,
    id uuid NOT NULL UNIQUE,
    aud varchar(255) NULL,
    "role" varchar(255) NULL,
    email varchar(255) NULL UNIQUE,
    encrypted_password varchar(255) NULL,
    confirmed_at timestamptz NULL,
    invited_at timestamptz NULL,
    confirmation_token varchar(255) NULL,
    confirmation_sent_at timestamptz NULL,
    recovery_token varchar(255) NULL,
    recovery_sent_at timestamptz NULL,
    email_change_token varchar(255) NULL,
    email_change varchar(255) NULL,
    email_change_sent_at timestamptz NULL,
    last_sign_in_at timestamptz NULL,
    raw_app_meta_data jsonb NULL,
    raw_user_meta_data jsonb NULL,
    is_super_admin bool NULL,
    created_at timestamptz NULL,
    updated_at timestamptz NULL,
    CONSTRAINT users_pkey PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS users_instance_id_email_idx ON auth.users USING btree (instance_id, email);
CREATE INDEX IF NOT EXISTS users_instance_id_idx ON auth.users USING btree (instance_id);

-- Таблица refresh_tokens
CREATE TABLE IF NOT EXISTS auth.refresh_tokens (
    instance_id uuid NULL,
    id bigserial NOT NULL,
    "token" varchar(255) NULL,
    user_id varchar(255) NULL,
    revoked bool NULL,
    created_at timestamptz NULL,
    updated_at timestamptz NULL,
    CONSTRAINT refresh_tokens_pkey PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS refresh_tokens_instance_id_idx ON auth.refresh_tokens USING btree (instance_id);
CREATE INDEX IF NOT EXISTS refresh_tokens_instance_id_user_id_idx ON auth.refresh_tokens USING btree (instance_id, user_id);
CREATE INDEX IF NOT EXISTS refresh_tokens_token_idx ON auth.refresh_tokens USING btree (token);

-- Таблица instances
CREATE TABLE IF NOT EXISTS auth.instances (
    id uuid NOT NULL,
    uuid uuid NULL,
    raw_base_config text NULL,
    created_at timestamptz NULL,
    updated_at timestamptz NULL,
    CONSTRAINT instances_pkey PRIMARY KEY (id)
);

-- Таблица audit_log_entries
CREATE TABLE IF NOT EXISTS auth.audit_log_entries (
    instance_id uuid NULL,
    id uuid NOT NULL,
    payload json NULL,
    created_at timestamptz NULL,
    CONSTRAINT audit_log_entries_pkey PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS audit_logs_instance_id_idx ON auth.audit_log_entries USING btree (instance_id);

-- Таблица schema_migrations (для отслеживания миграций)
CREATE TABLE IF NOT EXISTS auth.schema_migrations (
    "version" varchar(255) NOT NULL,
    CONSTRAINT schema_migrations_pkey PRIMARY KEY ("version")
);

-- Функции для JWT
CREATE OR REPLACE FUNCTION auth.uid() RETURNS uuid AS $$
  SELECT nullif(current_setting('request.jwt.claim.sub', true), '')::uuid;
$$ LANGUAGE sql STABLE;

CREATE OR REPLACE FUNCTION auth.role() RETURNS text AS $$
  SELECT nullif(current_setting('request.jwt.claim.role', true), '')::text;
$$ LANGUAGE sql STABLE;

-- Добавляем запись о выполненной миграции 00
INSERT INTO auth.schema_migrations (version) VALUES ('00')
ON CONFLICT (version) DO NOTHING;

\q
```

```sql
CREATE TABLE IF NOT EXISTS auth.identities (
    id text NOT NULL,
    user_id uuid NOT NULL,
    identity_data jsonb NOT NULL,
    provider text NOT NULL,
    last_sign_in_at timestamptz,
    created_at timestamptz,
    updated_at timestamptz,
    email text,
    CONSTRAINT identities_pkey PRIMARY KEY (provider, id),
    CONSTRAINT identities_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS identities_user_id_idx ON auth.identities (user_id);
CREATE INDEX IF NOT EXISTS identities_email_idx ON auth.identities (email);
``` 

3. Перезапускаем auth
docker-compose restart auth

4. Проверяем логи
docker logs supabase-auth --tail 50

 Финальное решение
1. Заходим в psql
docker exec -it supabase-db psql -U postgres -d postgres

2. Выполняем оставшиеся миграции вручную
```sql
-- Создаем enum тип для factor_type, если его нет
DO $$ BEGIN
    CREATE TYPE auth.factor_type AS ENUM ('totp', 'phone');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Создаем таблицу mfa_factors, если её нет
CREATE TABLE IF NOT EXISTS auth.mfa_factors (
    id uuid NOT NULL PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    friendly_name text,
    factor_type auth.factor_type NOT NULL,
    status text NOT NULL,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL,
    secret text,
    phone text UNIQUE
);

-- Добавляем колонку phone в mfa_factors (если ещё нет)
ALTER TABLE auth.mfa_factors ADD COLUMN IF NOT EXISTS phone text UNIQUE DEFAULT NULL;

-- Создаем таблицу mfa_challenges, если её нет
CREATE TABLE IF NOT EXISTS auth.mfa_challenges (
    id uuid NOT NULL PRIMARY KEY,
    factor_id uuid NOT NULL REFERENCES auth.mfa_factors(id) ON DELETE CASCADE,
    created_at timestamptz NOT NULL,
    verified_at timestamptz,
    ip_address inet,
    otp_code text
);

-- Добавляем колонку otp_code в mfa_challenges (если ещё нет)
ALTER TABLE auth.mfa_challenges ADD COLUMN IF NOT EXISTS otp_code text NULL;

-- Создаем уникальный индекс для verified phone factor
CREATE UNIQUE INDEX IF NOT EXISTS unique_verified_phone_factor 
    ON auth.mfa_factors (user_id, phone) 
    WHERE phone IS NOT NULL AND status = 'verified';

-- Добавляем запись о выполненной миграции
INSERT INTO auth.schema_migrations (version) VALUES ('20240729123726')
ON CONFLICT (version) DO NOTHING;

-- Проверяем, какие миграции ещё не выполнены
SELECT version FROM auth.schema_migrations ORDER BY version;
\q
```
3. Перезапускаем auth
```powershell
docker-compose restart auth
```
4. Проверяем логи

```powershell
docker logs supabase-auth --tail 50
```


```sql
-- Таблица identities
CREATE TABLE IF NOT EXISTS auth.identities (
    id text NOT NULL,
    user_id uuid NOT NULL,
    identity_data jsonb NOT NULL,
    provider text NOT NULL,
    last_sign_in_at timestamptz,
    created_at timestamptz,
    updated_at timestamptz,
    email text,
    CONSTRAINT identities_pkey PRIMARY KEY (provider, id)
);

CREATE INDEX IF NOT EXISTS identities_user_id_idx ON auth.identities (user_id);
CREATE INDEX IF NOT EXISTS identities_email_idx ON auth.identities (email);

-- Таблица sessions
CREATE TABLE IF NOT EXISTS auth.sessions (
    id uuid NOT NULL PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at timestamptz,
    updated_at timestamptz,
    factor_id uuid,
    aal text,
    not_after timestamptz
);

CREATE INDEX IF NOT EXISTS sessions_user_id_idx ON auth.sessions (user_id);
CREATE INDEX IF NOT EXISTS sessions_not_after_idx ON auth.sessions (not_after);

-- Таблица mfa_factors
CREATE TYPE auth.factor_status AS ENUM ('unverified', 'verified');

CREATE TABLE IF NOT EXISTS auth.mfa_factors (
    id uuid NOT NULL PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    friendly_name text,
    factor_type auth.factor_type NOT NULL,
    status auth.factor_status NOT NULL,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL,
    secret text,
    phone text
);

CREATE INDEX IF NOT EXISTS mfa_factors_user_id_idx ON auth.mfa_factors (user_id);
CREATE UNIQUE INDEX IF NOT EXISTS unique_verified_phone_factor ON auth.mfa_factors (user_id, phone) WHERE phone IS NOT NULL AND status = 'verified';

-- Таблица mfa_challenges
CREATE TABLE IF NOT EXISTS auth.mfa_challenges (
    id uuid NOT NULL PRIMARY KEY,
    factor_id uuid NOT NULL REFERENCES auth.mfa_factors(id) ON DELETE CASCADE,
    created_at timestamptz NOT NULL,
    verified_at timestamptz,
    ip_address inet,
    otp_code text
);

-- Таблица flow_state
CREATE TABLE IF NOT EXISTS auth.flow_state (
    id uuid NOT NULL PRIMARY KEY,
    user_id uuid,
    auth_code text NOT NULL,
    code_challenge_method text NOT NULL,
    code_challenge text NOT NULL,
    provider_type text NOT NULL,
    provider_access_token text,
    provider_refresh_token text,
    created_at timestamptz,
    updated_at timestamptz,
    authentication_method text
);

-- Таблица saml_providers
CREATE TABLE IF NOT EXISTS auth.saml_providers (
    id uuid NOT NULL PRIMARY KEY,
    sso_provider_id uuid NOT NULL,
    entity_id text NOT NULL,
    metadata_xml text NOT NULL,
    metadata_url text,
    attribute_mapping jsonb,
    created_at timestamptz,
    updated_at timestamptz,
    name_id_format text
);

-- Таблица saml_relay_states
CREATE TABLE IF NOT EXISTS auth.saml_relay_states (
    id uuid NOT NULL PRIMARY KEY,
    sso_provider_id uuid NOT NULL,
    request_id text NOT NULL,
    for_email text,
    redirect_to text,
    created_at timestamptz,
    updated_at timestamptz,
    flow_state_id uuid REFERENCES auth.flow_state(id) ON DELETE CASCADE
);

-- Таблица one_time_tokens
CREATE TABLE IF NOT EXISTS auth.one_time_tokens (
    id uuid NOT NULL PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    token_type text NOT NULL,
    token_hash text NOT NULL UNIQUE,
    relates_to text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS one_time_tokens_user_id_idx ON auth.one_time_tokens (user_id);
CREATE INDEX IF NOT EXISTS one_time_tokens_token_hash_idx ON auth.one_time_tokens (token_hash);
```

```sql
ALTER ROLE postgres SET search_path TO public, auth;
```
```sql
UPDATE auth.identities
SET last_sign_in_at = '2022-11-25'
WHERE
    last_sign_in_at IS NULL
    AND created_at = '2022-11-25'
    AND updated_at = '2022-11-25'
    AND provider = 'email'
    AND id::text = user_id::text;
    ```