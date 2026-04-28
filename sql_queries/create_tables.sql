-- Таблица chats (без поля sources)
CREATE TABLE IF NOT EXISTS public.chats (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    parameters JSONB NOT NULL,
    context TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chats_user_id ON public.chats(user_id);
CREATE INDEX idx_chats_created_at ON public.chats(created_at);

ALTER TABLE public.chats ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own chats" ON public.chats
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own chats" ON public.chats
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Таблица sources (метаданные чанков)
CREATE TABLE IF NOT EXISTS public.sources (
    id TEXT PRIMARY KEY,                -- chunk_id из Qdrant
    filename TEXT NOT NULL,
    breadcrumbs TEXT,
    summary TEXT,
    category TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sources_filename ON public.sources(filename);

ALTER TABLE public.sources ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can view sources" ON public.sources FOR SELECT USING (true);

-- Таблица chat_sources (связь многие-ко-многим с оценками)
CREATE TABLE IF NOT EXISTS public.chat_sources (
    id BIGSERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL REFERENCES public.chats(id) ON DELETE CASCADE,
    source_id TEXT NOT NULL REFERENCES public.sources(id) ON DELETE CASCADE,
    position INT NOT NULL,
    score_hybrid FLOAT,
    score_rerank FLOAT,
    score_pref FLOAT,
    score_bm25 FLOAT,
    score_hype FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(chat_id, source_id)
);

CREATE INDEX idx_chat_sources_chat_id ON public.chat_sources(chat_id);
CREATE INDEX idx_chat_sources_source_id ON public.chat_sources(source_id);

ALTER TABLE public.chat_sources ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view their chat sources" ON public.chat_sources
    FOR SELECT USING (EXISTS (SELECT 1 FROM public.chats WHERE chats.id = chat_sources.chat_id AND chats.user_id = auth.uid()));

-- Тип для фидбека
DO $$ BEGIN
    CREATE TYPE feedback_type AS ENUM ('like', 'dislike', 'star');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Таблица feedback
CREATE TABLE IF NOT EXISTS public.feedback (
    id BIGSERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL REFERENCES public.chats(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    feedback_type feedback_type NOT NULL,
    rating INT CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(chat_id, user_id)
);

CREATE INDEX idx_feedback_chat_id ON public.feedback(chat_id);
CREATE INDEX idx_feedback_user_id ON public.feedback(user_id);

ALTER TABLE public.feedback ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own feedback" ON public.feedback
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own feedback" ON public.feedback
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own feedback" ON public.feedback
    FOR UPDATE USING (auth.uid() = user_id);

-- Триггер для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_feedback_updated_at
    BEFORE UPDATE ON public.feedback
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();