CREATE TABLE public.sources (
    id TEXT PRIMARY KEY,                -- chunk_id из Qdrant (например "3260a9178187_p5")
    filename TEXT NOT NULL,              -- имя файла
    breadcrumbs TEXT,                    -- раздел
    summary TEXT,                        -- краткое содержание
    category TEXT,                       -- legal/instructions/etc.
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индекс для поиска по файлу (опционально)
CREATE INDEX idx_sources_filename ON public.sources(filename);

ALTER TABLE public.sources ENABLE ROW LEVEL SECURITY;
-- Разрешаем чтение всем аутентифицированным (или публично)
CREATE POLICY "Anyone can view sources" 
    ON public.sources FOR SELECT USING (true);
-- Запись только через сервисную роль (бэкенд)