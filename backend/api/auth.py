"""
Аутентификация через JWT токен
Согласно API_REQUIREMENTS.md
"""
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
import os
import config

security = HTTPBearer()

# Используем SUPABASE_JWT_SECRET или fallback на JWT_SECRET_KEY
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET") or config.JWT_SECRET_KEY


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    """
    Получение текущего пользователя из JWT токена.
    
    Returns:
        user_id (str): ID пользователя из токена (sub claim)
    
    Raises:
        HTTPException: 401 если токен невалиден
    """
    token = credentials.credentials
    
    import logging
    logger = logging.getLogger(__name__ + ".auth")
    logger.info(f"🔑 Получен токен: {token[:50]}...")
    
    try:
        # Декодируем токен с проверкой подписи
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False}  # Отключаем проверку audience для гибкости
        )
        
        logger.info(f"✅ Токен декодирован: {payload}")
        
        user_id = payload.get("sub")
        
        # Если нет sub claim (service_role токен), используем роль
        if not user_id:
            role = payload.get("role")
            if role == "service_role":
                # Для service_role токена используем фиксированный user_id
                user_id = "service_user"
                logger.info(f"🔧 service_role токен, используем user_id: {user_id}")
            elif role == "anon":
                # Для anon токена - ошибка
                raise HTTPException(
                    status_code=401,
                    detail="Anon token not allowed. Please login."
                )
            else:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token: no sub claim"
                )
        else:
            logger.info(f"✅ user_id из токена: {user_id}")
        
        return user_id
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        logger.error(f"❌ Invalid token: {e}")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Authentication error: {e}")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {e}")
