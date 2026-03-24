import os

import jwt
import time
from dotenv import load_dotenv
load_dotenv()
payload = {
    "role": "service_role",
    "iss": "supabase",
    "iat": int(time.time()),
    "exp": int(time.time()) + 315360000  # лет на 10
}
secret = os.getenv("SUPABASE_JWT_SECRET")
token = jwt.encode(payload, secret, algorithm="HS256")
print(token)