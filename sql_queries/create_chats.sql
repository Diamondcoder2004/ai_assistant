CREATE TABLE public.chats (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    parameters JSONB NOT NULL,      -- {k, rerank_top_k, temperature, max_tokens, min_score}
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chats_user_id ON public.chats(user_id);
CREATE INDEX idx_chats_created_at ON public.chats(created_at);

ALTER TABLE public.chats ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own chats" 
    ON public.chats FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert their own chats" 
    ON public.chats FOR INSERT WITH CHECK (auth.uid() = user_id);