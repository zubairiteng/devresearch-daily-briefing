@echo off
title DevResearch Daily Briefing Dashboard
echo ===================================================
echo Starting DevResearch Daily Briefing Dashboard...
echo ===================================================
start "" "http://127.0.0.1:8000"
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
pause
