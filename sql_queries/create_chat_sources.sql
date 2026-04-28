CREATE TABLE public.chat_sources (
    id BIGSERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL REFERENCES public.chats(id) ON DELETE CASCADE,
    source_id TEXT NOT NULL REFERENCES public.sources(id) ON DELETE CASCADE,
    position INT NOT NULL,                -- порядок в ответе (1,2,3...)
    score_hybrid FLOAT,                   -- гибридная оценка
    score_rerank FLOAT,                    -- оценка после реранкера
    score_pref FLOAT,
    score_bm25 FLOAT,
    score_hype FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(chat_id, source_id)            -- чтобы случайно не задвоить
);

CREATE INDEX idx_chat_sources_chat_id ON public.chat_sources(chat_id);
CREATE INDEX idx_chat_sources_source_id ON public.chat_sources(source_id);

ALTER TABLE public.chat_sources ENABLE ROW LEVEL SECURITY;
-- Пользователь видит источники только своих чатов (через chat_id)
CREATE POLICY "Users can view their chat sources" 
    ON public.chat_sources FOR SELECT 
    USING (EXISTS (SELECT 1 FROM public.chats WHERE chats.id = chat_sources.chat_id AND chats.user_id = auth.uid()));
-- Вставка только через сервисную роль