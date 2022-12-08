import os
from datetime import datetime, time, timedelta
import argparse
import sys
import shutil
from typing import List, Dict
from collections import defaultdict

PATH_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.append(PATH_ROOT)

from pyptools.common import Product, Ticker, BarData, GeneralTickerInfoFile, TickerInfoData
from pyptools.pyptools_ds import DSManager
from helper.simpleLogger import MyLogger

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('-i', '--input', help='DS路径')
# arg_parser.add_argument('-o', '--output', default=os.path.join(PATH_ROOT, 'Output'))
# arg_parser.add_argument('--mostactivateN', help='检查各品种第几个活跃的品种', default=1)
arg_parser.add_argument('--daysoffset', help='日期推后多少天', default=0)
arg_parser.add_argument('--tickerinfo', help='GeneralTickerInfo文件路径', default=None)
args = arg_parser.parse_args()
PATH_DS_ROOT = os.path.abspath(args.input)
# PATH_OUTPUT = os.path.abspath(args.output)
# MOST_ACTIVATE_N = int(args.mostactivateN)
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

# =========== #
PATH_OUTPUT_1 = os.path.join(PATH_ROOT, 'Output_MostActTicker')
PATH_OUTPUT_2 = os.path.join(PATH_ROOT, 'Output_SecondActTicker')
if not os.path.isdir(PATH_OUTPUT_1):
    os.makedirs(PATH_OUTPUT_1)
if not os.path.isdir(PATH_OUTPUT_2):
    os.makedirs(PATH_OUTPUT_2)


# ** ============= **
# 用于简单地判断是否交易日。当天有多少个ticker的数据文件。
MIN_TICKERS_IN_TRADING_DAYS = 500


class ProductTickersDSBarVolumeChecker:
    def __init__(
            self, data_path, offset_days=0, min_ticker_file=500,
            trade_day_end_time=time(hour=23, minute=59, second=59),
            logger=MyLogger('ProductTickersDSBarVolumeChecker')
    ):
        assert os.path.isdir(data_path)
        self.ds_bar_data_folder = os.path.abspath(data_path)
        self.trading_day_min_ticker_file = min_ticker_file
        self.offset_days = offset_days
        self.trade_day_end_time = trade_day_end_time
        if trade_day_end_time == time(hour=23, minute=59, second=59):
            self.using_trade_day = False
        else:
            self.using_trade_day = True

        # 汇总数据
        # {Product: [[Product, Ticker, volume, value], [], ], }
        self.summary_data = dict()
        self.checking_date = ""

        #
        self.logger = logger

    def _find_target_date_folder(self) -> [str, str] or None:
        """查找目标数据日期
        检查文件夹是否正常，
        是否为交易日（数据文件数量满足规定）

        满足 offset_days。 “0” ：检查当天（最近一个交易日）；“1”：检查前一天（最近的第二个交易日）
        """
        _l_satisfied_folder = []
        if not self.using_trade_day:
            # 以自然日为交易日时间
            #   不分交易日，当天：1
            #   不分交易日，前一天：2
            _target_count = self.offset_days + 1
        else:
            # 按照某个时间点划分交易日的起始
            #   区分交易日，当天：2
            #   区分交易日，前一天：3
            _target_count = self.offset_days + 2

        l_folder_name = sorted(os.listdir(self.ds_bar_data_folder))[::-1]
        enum_n = 0
        while (len(_l_satisfied_folder) < _target_count) and (enum_n < len(l_folder_name)):
            enum_n += 1
            folder_name = l_folder_name[enum_n - 1]
            p_folder = os.path.join(self.ds_bar_data_folder, folder_name)

            # 判断是否为 正常的 交易日 数据目录
            if not os.path.isdir(p_folder):
                continue
            try:
                _date = datetime.strptime(folder_name, '%Y%m%d')
            except:
                continue
            # 检查数据文件数量
            if len(os.listdir(p_folder)) < self.trading_day_min_ticker_file:
                continue
            # 满足
            _l_satisfied_folder.append(p_folder)

        if len(_l_satisfied_folder) == _target_count:
            if self.using_trade_day:
                return [_l_satisfied_folder[-2], _l_satisfied_folder[-1]]
            else:
                return [_l_satisfied_folder[-1], ""]
        else:
            return None

    def _read_data(self, folder_a, folder_b) -> Dict[Product, List[list]]:
        def read(p, first=True):
            # 读取文件
            for file_name in os.listdir(p):
                if file_name.split('.')[-1] != 'csv':
                    continue
                p_file = os.path.join(p, file_name)
                if not os.path.isfile(p_file):
                    continue

                # 筛选数据 时间
                ticker: Ticker = Ticker.from_name(file_name[:-4])
                product: Product = ticker.product
                if division_time:
                    if first:
                        l_bar_data: List[BarData] = [
                            _bar_data for _bar_data in DSManager._read_a_bar_file(p_file)
                            if _bar_data.time <= division_time
                        ]
                    else:
                        l_bar_data: List[BarData] = [
                            _bar_data for _bar_data in DSManager._read_a_bar_file(p_file)
                            if _bar_data.time > division_time
                        ]
                else:
                    l_bar_data: List[BarData] = DSManager._read_a_bar_file(p_file)

                # 存放
                if not d_product_tickers_bar_data.get(product):
                    d_product_tickers_bar_data[product][ticker] = []
                elif not d_product_tickers_bar_data.get(product).get(ticker):
                    d_product_tickers_bar_data[product][ticker] = []
                d_product_tickers_bar_data[product][ticker] += l_bar_data

        def summary():
            for product in d_product_tickers_bar_data.keys():
                for ticker, l_bar_data in d_product_tickers_bar_data[product].items():
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
                    d_product_tickers_summary_data[product].append([product.name, ticker.name, total_volume, total_value])

        # 存放数据
        # {product: ticker: [BarData], }
        d_product_tickers_bar_data = defaultdict(dict)
        d_product_tickers_summary_data = defaultdict(list)
        # 读取文件
        if self.using_trade_day:
            division_time = self.trade_day_end_time
            self.logger.info(f"read first folder, {folder_a}")
            read(folder_a)
            self.logger.info(f"read second folder, {folder_b}")
            read(folder_b, first=False)
        else:
            division_time = None
            self.logger.info(f"read folder, {folder_a}")
            read(folder_a)
        # 汇总 bar 数据，计算总成交量和成交额
        summary()

        return d_product_tickers_summary_data

        #

    def read_data(self):
        # 查找所需要检查的交易日数据文件夹
        l_target_folder = self._find_target_date_folder()
        if not l_target_folder:
            self.logger.error('未找到目标日期文件夹')
            raise Exception

        # 检查的数据日期
        self.checking_date = os.path.basename(l_target_folder[0])
        if self.trade_day_end_time:
            assert os.path.isdir(l_target_folder[0])
            assert os.path.isdir(l_target_folder[1])
        else:
            assert os.path.isdir(l_target_folder[0])

        # 读取数据
        # {Product: [[Product, Ticker, volume, value], [], ], }
        self.summary_data = self._read_data(l_target_folder[0], l_target_folder[1])

    def get_activate_tickers(self, most_activate_n=1, output_root=''):
        d_activate_tickers_data = {}
        for product, _data in self.summary_data.items():
            _sorted_data = sorted(_data, key=lambda x: x[2])[::-1]
            if len(_sorted_data) < most_activate_n:
                continue
            else:
                d_activate_tickers_data[product] = _sorted_data[most_activate_n - 1]

        if output_root:
            p_output_file = os.path.join(output_root, f'output_{self.checking_date}.csv')
            l_data_keys: List[Product] = list(d_activate_tickers_data.keys())
            # 按照 exchange product排序
            l_data_keys.sort(key=lambda x: [x.exchange.lower(), x.name.lower()])
            output_string = [
                ','.join([str(_) for _ in d_activate_tickers_data[_key]])
                for _key in l_data_keys
            ]
            with open(p_output_file, 'w') as f:
                f.writelines('\n'.join(output_string))


if __name__ == '__main__':
    obj = ProductTickersDSBarVolumeChecker(
        data_path=os.path.join(PATH_DS_ROOT, 'BarData', '60', 'Futures'),
        offset_days=DAYS_OFFSET,
        min_ticker_file=MIN_TICKERS_IN_TRADING_DAYS,
        trade_day_end_time=time(hour=15, minute=2, second=0),
        logger=MyLogger('ProductTickersDSBarVolumeChecker', output_root=os.path.join(PATH_ROOT, 'logs'))
    )
    obj.read_data()
    obj.get_activate_tickers(most_activate_n=1, output_root=PATH_OUTPUT_1)
    obj.get_activate_tickers(most_activate_n=2, output_root=PATH_OUTPUT_2)
