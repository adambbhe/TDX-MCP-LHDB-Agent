# -*- coding: utf-8 -*-
"""
测试获取市场数据
"""

import sys
import os
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from tqcenter import tq

print("初始化连接...")
tq.initialize(path=str(script_dir))
print(f"run_id: {tq.run_id}")

test_stocks = ['600519.SH', '000001.SZ', '300750.SZ']

print("\n测试获取市场数据...")
try:
    data = tq.get_market_data(
        stock_list=test_stocks,
        field_list=['code', 'name', 'price', 'open', 'high', 'low', 'preclose'],
        period='1d',
        count=1
    )

    print(f"\n返回类型: {type(data)}")
    print(f"返回内容: {data}")

    if isinstance(data, dict):
        print(f"\n字典键: {list(data.keys())}")
        for key, value in list(data.items())[:3]:
            print(f"\n键: {key}")
            print(f"值类型: {type(value)}")
            if isinstance(value, dict):
                print(f"值内容: {value}")
            elif hasattr(value, 'head'):
                print(f"DataFrame形状: {value.shape}")
                print(f"DataFrame列: {list(value.columns)}")
                print(f"前几行:\n{value.head()}")
    elif isinstance(data, list):
        print(f"\n列表长度: {len(data)}")
        if len(data) > 0:
            print(f"第一个元素类型: {type(data[0])}")
            print(f"第一个元素: {data[0]}")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

tq.close()
