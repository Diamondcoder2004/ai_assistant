@echo off
REM ============================================
REM Скрипт запуска ИИ-ассистента (Windows)
REM ============================================

echo ============================================
echo ИИ-ассистент Башкирэнерго - Запуск
echo ============================================
echo.

REM Проверка наличия Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker не найден! Установите Docker Desktop.
    pause
    exit /b 1
)

echo [OK] Docker найден
echo.

REM Проверка наличия .env файла
if not exist .env (
    echo [WARNING] Файл .env не найден!
    echo Создайте файл .env на основе .env.example
    echo.
    pause
    exit /b 1
)

echo [OK] Файл .env найден
echo.

REM Остановка старых контейнеров
echo [INFO] Остановка старых контейнеров...
docker-compose down >nul 2>&1

REM Запуск всех сервисов
echo [INFO] Запуск сервисов...
echo.
docker-compose up -d --build

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Ошибка при запуске!
    pause
    exit /b 1
)

echo.
echo ============================================
echo [OK] Все сервисы запущены!
echo ============================================
echo.
echo Доступные сервисы:
echo   - Фронтенд: http://localhost
echo   - Бэкенд API: http://localhost:8880
echo   - Qdrant: http://localhost:6333
echo.
echo Для просмотра логов: docker-compose logs -f
echo Для остановки: docker-compose down
echo.
pause
