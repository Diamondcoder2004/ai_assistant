## Было принято решение поменять структуру БД supabase и источники добавлять в chats в виде jsonb

```sql
ALTER TABLE chats ADD COLUMN sources JSONB DEFAULT '[]'::jsonb;
```

