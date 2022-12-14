import os
from typing import Dict, List


class HeaderCsvReader:
    """
    key, valueA, valueB,...
    读取有header的csv，返回 dict
        {
            key1: {valuesA: valuesA1, valuesB: valuesB1}, 
            key2: {}
        }    
    """
    def __init__(self, key: str, values: list, set_header=None):
        if (type(key) != str) or (type(values) != list):
            raise ValueError
        self.key = key
        self.values = values
        self.set_header = set_header
    
    def read(self, path) -> Dict[str, Dict[str, str]]:
        path = os.path.abspath(path)
        if not os.path.isfile(path):
            raise FileExistsError

        with open(path, encoding='utf-8') as f:
            l_lines = f.readlines()
        if len(l_lines) < 1:
            print('数据有误：%s' % path)
            raise Exception

        # 读取header，定位index
        if self.set_header:
            header = self.set_header
        else:
            header = l_lines[0].strip().replace(' ', '').split(',')
            l_lines = l_lines[1:]

        try:
            key_index = header.index(self.key)
        except:
            print('数据有误,不存在 key：%s' % self.key)
            raise Exception
        try:
            values_index = {
                value: header.index(value)
                for value in self.values
            }
        except:
            print('header:\t', header)
            print('数据有误,不存在value行：%s' % self.values)
            raise Exception

        # 读取信息
        d_data = {}
        for line in l_lines:
            line = line.strip()
            line_split = line.split(',')
            key_str = line_split[key_index]
            value_dict = {
                value: line_split[value_index]
                for value, value_index in values_index.items()
            }
            d_data[key_str] = value_dict
        return d_data
