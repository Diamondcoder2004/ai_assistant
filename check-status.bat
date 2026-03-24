@echo off
REM ============================================
REM Скрипт проверки состояния сервисов
REM ============================================

echo ============================================
echo Проверка состояния сервисов
echo ============================================
echo.

REM Проверка Docker
echo [1] Проверка Docker...
docker --version
if %errorlevel% neq 0 (
    echo [ERROR] Docker не найден!
) else (
    echo [OK] Docker установлен
)
echo.

REM Проверка запущенных контейнеров
echo [2] Запущенные контейнеры...
docker-compose ps
echo.

REM Проверка доступности сервисов
echo [3] Проверка доступности сервисов...
echo.

REM Проверка фронтенда
echo Проверка фронтенда (port 80)...
curl -s -o nul http://localhost && (echo [OK] Фронтенд доступен) || (echo [ERROR] Фронтенд недоступен)

REM Проверка бэкенда
echo.
echo Проверка бэкенда (port 8880)...
curl -s http://localhost:8880/health >nul 2>&1 && (echo [OK] Бэкенд доступен) || (echo [ERROR] Бэкенд недоступен)

REM Проверка Qdrant
echo.
echo Проверка Qdrant (port 6333)...
curl -s http://localhost:6333/healthz >nul 2>&1 && (echo [OK] Qdrant доступен) || (echo [ERROR] Qdrant недоступен)

echo.
echo ============================================
echo Проверка завершена
echo ============================================
pause
