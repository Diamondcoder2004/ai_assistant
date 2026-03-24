-- Таблица настроек пользователя
CREATE TABLE IF NOT EXISTS user_settings (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    hotkeys JSONB DEFAULT '{}',
    theme TEXT DEFAULT 'light',
    language TEXT DEFAULT 'ru',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы
CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id);

-- RLS (Row Level Security)
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;

-- Политики
-- Пользователь может видеть только свои настройки
CREATE POLICY "Users can view own settings"
    ON user_settings
    FOR SELECT
    USING (auth.uid()::text = user_id);

-- Пользователь может обновлять только свои настройки
CREATE POLICY "Users can update own settings"
    ON user_settings
    FOR UPDATE
    USING (auth.uid()::text = user_id);

-- Пользователь может создавать свои настройки
CREATE POLICY "Users can insert own settings"
    ON user_settings
    FOR INSERT
    WITH CHECK (auth.uid()::text = user_id);

-- Триггер для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_settings_updated_at
    BEFORE UPDATE ON user_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
