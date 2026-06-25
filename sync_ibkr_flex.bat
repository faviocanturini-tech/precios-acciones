@echo off
cd /d "C:\Users\favio\Desktop\TRADING"
python sync_ibkr_flex.py >> data\sync_ibkr_flex.log 2>&1
