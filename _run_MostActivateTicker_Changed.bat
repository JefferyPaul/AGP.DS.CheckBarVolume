echo off
chcp 65001

cd %~dp0
python checkTickerChanged.py -i "./Output_MostActTicker" -o "./Output_MostActTicker_Changed"


cd %~dp0
python GenFileLinesDiff.py -i "./Output_MostActTicker_Changed/ChangedTicker.csv" -o "./Output_MostActTicker_Changed/ChangedTicker_Result.csv" --dline "./Output_MostActTicker_Changed/_SkipLineList.csv" --dstr "./Output_MostActTicker_Changed/_SkipStrList.csv"


cd %~dp0
python checkTickerChanged.py -i "./Output_SecondActTicker" -o "./Output_SecondActTicker_Changed"


cd %~dp0
python GenFileLinesDiff.py -i "./Output_SecondActTicker_Changed/ChangedTicker.csv" -o "./Output_SecondActTicker_Changed/ChangedTicker_Result.csv" --dline "./Output_SecondActTicker_Changed/_SkipLineList.csv" --dstr "./Output_SecondActTicker_Changed/_SkipStrList.csv"




exit