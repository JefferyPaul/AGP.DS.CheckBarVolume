"""
我们经常需要对某个初步结果进行类似于黑名单的筛选，从而得出最终结果。

此脚本，对输入的文件内容，按行，检查并剔除属于“黑名单”的内容，然后输出。
    “黑名单”内容认定方式有：
        1,“黑名单文件”按行识别，原文件中有一样的行，剔除；-l --dline
        2,“黑名单文件”按行识别，原文件行包含其中的字符，剔除；-s --dstr
"""

import os
import sys
import shutil
import argparse
from datetime import datetime

p_root = os.path.abspath(os.path.dirname(__file__))
sys.path.append(p_root)

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('-i', '--input')
# a 整行一致
arg_parser.add_argument('-l', '--dline')        
# b 行中存在相应字符
arg_parser.add_argument('-s', '--dstr')
arg_parser.add_argument('-o', '--output')

args = arg_parser.parse_args()
path_input = args.input
path_dline = args.dline
path_dstr = args.dstr
path_output = args.output


assert os.path.isfile(path_input)
if path_dline:
    assert os.path.isfile(path_dline)
if path_dstr:
    assert os.path.isfile(path_dstr)
with open(path_input) as f:
    l_lines_input = f.readlines()
l_lines_input = [_.strip() for _ in l_lines_input if _.strip()]
l_lines_output = l_lines_input.copy()

#
if path_dline:
    with open(path_dline) as f:
        l_lines_dline = f.readlines()
    l_lines_dline = [_.strip() for _ in l_lines_dline if _.strip()]
    l_new = []
    for _ in l_lines_output:
        if _ not in l_lines_dline:
            l_new.append(_)
    l_lines_output = l_new

# 
if path_dstr:
    with open(path_dstr) as f:
        l_lines_str = f.readlines()
    l_lines_str = [_.strip() for _ in l_lines_str if _.strip()]
    l_new = []
    for _ in l_lines_output:
        _error = False
        for dstr in l_lines_str:
            if dstr in _:
                _error = True
                break
        if _error:
            continue
        else:
            l_new.append(_)
    l_lines_output = l_new

# 输出
if not os.path.isdir(os.path.dirname(path_output)):
    os.makedirs(os.path.dirname(path_output))
with open(path_output, 'w') as f:
    f.writelines('\n'.join(l_lines_output))
shutil.copyfile(src=path_output, dst=path_output + '.%s.bak' % datetime.now().strftime('%Y%m%d%H%M%S'))
