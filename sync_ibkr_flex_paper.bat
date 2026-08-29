@echo off
cd /d "C:\Users\favio\Desktop\TRADING"
python sync_ibkr_flex.py --paper >> data\sync_ibkr_flex_paper.log 2>&1
