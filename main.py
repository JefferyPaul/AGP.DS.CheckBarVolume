import os
from datetime import datetime
import argparse
import sys
import shutil
from typing import List, Dict
from collections import defaultdict

PATH_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.append(PATH_ROOT)

from pyptools.common import Product, Ticker, BarData, GeneralTickerInfoFile, TickerInfoData
from pyptools.pyptools_ds import DSManager

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('-i', '--input', help='DS路径')
arg_parser.add_argument('-o', '--output', default=os.path.join(PATH_ROOT, 'Output'))
arg_parser.add_argument('--mostactivateN', help='检查各品种第几个活跃的品种', default=1)
arg_parser.add_argument('--daysoffset', help='日期推后多少天', default=0)
arg_parser.add_argument('--tickerinfo', help='GeneralTickerInfo文件路径', default=None)
args = arg_parser.parse_args()
PATH_DS_ROOT = os.path.abspath(args.input)
PATH_OUTPUT = os.path.abspath(args.output)
MOST_ACTIVATE_N = int(args.mostactivateN)
DAYS_OFFSET = int(args.daysoffset)       # 当天：0；前一交易日：-1
PATH_TICKER_INFO_FILE = args.tickerinfo

assert os.path.isdir(PATH_DS_ROOT)
if DAYS_OFFSET < 0:
    DAYS_OFFSET = - DAYS_OFFSET
if PATH_TICKER_INFO_FILE:
    PATH_TICKER_INFO_FILE = os.path.abspath(PATH_TICKER_INFO_FILE)
    D_TICKER_INFO: Dict[Product, TickerInfoData] = GeneralTickerInfoFile.read(PATH_TICKER_INFO_FILE)
else:
    D_TICKER_INFO = None
if not os.path.isdir(PATH_OUTPUT):
    os.makedirs(PATH_OUTPUT)


# ** ============= **
# 用于简单地判断是否交易日。当天有多少个ticker的数据文件。
MIN_TICKERS_IN_TRADING_DAYS = 500


if __name__ == '__main__':
    # 查找前一个 交易日。不使用当天
    PATH_DS_FUTURES_BAR_FOLDER = os.path.join(PATH_DS_ROOT, 'BarData', '60', 'Futures')
    assert os.path.isdir(PATH_DS_FUTURES_BAR_FOLDER)
    _satisfied_count = 0
    p_target_date_folder = ''
    for folder_name in sorted(os.listdir(PATH_DS_FUTURES_BAR_FOLDER))[::-1]:
        p_folder = os.path.join(PATH_DS_FUTURES_BAR_FOLDER, folder_name)
        if not os.path.isdir(p_folder):
            continue
        try:
            _date = datetime.strptime(folder_name, '%Y%m%d')
        except :
            continue
        # 检查数据文件数量
        if len(os.listdir(p_folder)) < MIN_TICKERS_IN_TRADING_DAYS:
            continue
        else:
            _satisfied_count += 1
        if _satisfied_count == DAYS_OFFSET + 1:
            p_target_date_folder = p_folder
            break
    print(p_target_date_folder)
    target_date = os.path.basename(p_target_date_folder)

    # 读取文件
    d_product_tickers_data = defaultdict(list)
    for file_name in os.listdir(p_target_date_folder):
        if file_name.split('.')[-1] != 'csv':
            continue
        p_file = os.path.join(p_target_date_folder, file_name)
        if not os.path.isfile(p_file):
            continue
        ticker: Ticker = Ticker.from_name(file_name[:-4])
        product: Product = ticker.product
        l_bar_data: List[BarData] = DSManager._read_a_bar_file(p_file)
        # 总成交量
        total_volume = sum([bar_data.volume for bar_data in l_bar_data])
        # 总成交额
        if D_TICKER_INFO:
            if product in D_TICKER_INFO:
                _point_value = D_TICKER_INFO[product].point_value
                total_value = sum([bar_data.volume * bar_data.price * _point_value for bar_data in l_bar_data])
            else:
                total_value = ''
        else:
            total_value = ''
        d_product_tickers_data[product].append([product.name, ticker.name, total_volume, total_value])
    # 筛选所需要的ticker。  最活跃？次活跃？还是？
    d_product_checking_ticker_data = {}
    for product, _data in d_product_tickers_data.items():
        _sorted_data = sorted(_data, key=lambda x: x[2])[::-1]
        if len(_sorted_data) < MOST_ACTIVATE_N:
            continue
        else:
            d_product_checking_ticker_data[product] = _sorted_data[MOST_ACTIVATE_N-1]

    # 输出
    p_output_file = os.path.join(PATH_OUTPUT, f'output_{target_date}.csv')
    l_data_keys: List[Product] = list(d_product_checking_ticker_data.keys())
    # 按照 exchange product排序
    l_data_keys.sort(key=lambda x: [x.exchange.lower(), x.name.lower()])
    output_string = [
        ','.join([str(_) for _ in d_product_checking_ticker_data[_key]])
        for _key in l_data_keys
    ]
    with open(p_output_file, 'w') as f:
        f.writelines('\n'.join(output_string))
