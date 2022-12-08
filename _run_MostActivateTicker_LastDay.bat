echo off
chcp 65001

cd %~dp0
python main.py -i "C:\D\_workspace\Platinum\Platinum.Ds" --daysoffset 1 --tickerinfo ".\Config\GeneralTickerInfo.csv" 

pause