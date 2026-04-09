Создаем user

```sql
CREATE ROLE service_role NOINHERIT;
GRANT INSERT, SELECT ON TABLE chats TO service_role;
```