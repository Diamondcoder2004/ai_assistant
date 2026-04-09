    CREATE TYPE feedback_type AS ENUM ('like', 'dislike', 'star');

    CREATE TABLE public.feedback (
        id BIGSERIAL PRIMARY KEY,
        chat_id BIGINT NOT NULL REFERENCES public.chats(id) ON DELETE CASCADE,
        user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
        feedback_type feedback_type NOT NULL,
        rating INT CHECK (rating >= 1 AND rating <= 5), -- для звёзд
        comment TEXT,                                   -- опционально
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW(),
        UNIQUE(chat_id, user_id)                        -- один пользователь – одна оценка на чат
    );

    CREATE INDEX idx_feedback_chat_id ON public.feedback(chat_id);
    CREATE INDEX idx_feedback_user_id ON public.feedback(user_id);

    ALTER TABLE public.feedback ENABLE ROW LEVEL SECURITY;

    -- Пользователь может видеть свои оценки
    CREATE POLICY "Users can view their own feedback" 
        ON public.feedback FOR SELECT USING (auth.uid() = user_id);
    -- Пользователь может создавать/обновлять свои оценки
    CREATE POLICY "Users can manage their own feedback" 
        ON public.feedback FOR INSERT WITH CHECK (auth.uid() = user_id);
    CREATE POLICY "Users can update their own feedback" 
        ON public.feedback FOR UPDATE USING (auth.uid() = user_id);