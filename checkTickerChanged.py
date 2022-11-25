import os
from datetime import datetime
import argparse
import shutil

PATH_ROOT = os.path.abspath(os.path.dirname(__file__))

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('-i', '--input')
arg_parser.add_argument('-o', '--output')
args = arg_parser.parse_args()
PATH_INPUT = os.path.abspath(args.input)
PATH_OUTPUT = os.path.abspath(args.output)
assert os.path.isdir(PATH_INPUT)
if not os.path.isdir(PATH_OUTPUT):
    os.makedirs(PATH_OUTPUT)


def _read_file(p):
    d_product_ticker = {}
    with open(p) as f:
        l_lines = f.readlines()
    for line in l_lines:
        line = line.strip()
        if line == '':
            continue
        _product = line.split(',')[0]
        _ticker = line.split(',')[1]
        d_product_ticker[_product] = _ticker
    return d_product_ticker


if __name__ == '__main__':
    #
    l_input_files_name = [i for i in os.listdir(PATH_INPUT) if os.path.isfile(os.path.join(PATH_INPUT, i))]
    for file_name in l_input_files_name.copy():
        try:
            _ = datetime.strptime(file_name.split('.')[0].split('_')[-1], "%Y%m%d")
        except :
            l_input_files_name.remove(file_name)
    if len(l_input_files_name) < 2:
        print("文件数少于2，无法执行")

    # 读取
    l_input_files_name.sort()
    new_file = os.path.join(PATH_INPUT, l_input_files_name[-1])
    old_file = os.path.join(PATH_INPUT, l_input_files_name[-2])
    d_new_product_ticker = _read_file(new_file)
    d_old_product_ticker = _read_file(old_file)
    print(new_file, '\n', old_file)
    new_file_date = l_input_files_name[-1].split('.')[0].split('_')[-1]

    # 对比
    l_changed_product_ticker = []
    for _product, _ticker in d_new_product_ticker.items():
        if _product not in d_old_product_ticker.keys():
            continue
        if _ticker != d_old_product_ticker[_product]:
            l_changed_product_ticker.append([_product, _ticker, d_old_product_ticker[_product]])

    # 输出
    p_output_file = os.path.join(PATH_OUTPUT, 'ChangedProductTicker.csv')
    p_output_file_bak = os.path.join(PATH_OUTPUT, 'ChangedProductTicker_%s.csv' % new_file_date)
    s_output = [','.join(_) for _ in l_changed_product_ticker]
    with open(p_output_file, 'w') as f:
        f.writelines('\n'.join(s_output))
    shutil.copyfile(p_output_file, p_output_file_bak)
    print('\n'.join(s_output))
