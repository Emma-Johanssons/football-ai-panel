@echo off
set CURRENT_DIR=%cd%
docker run --rm -v "%CURRENT_DIR%\audio:/app/audio" -v "%CURRENT_DIR%\logs:/app/logs" football-ai-panel 