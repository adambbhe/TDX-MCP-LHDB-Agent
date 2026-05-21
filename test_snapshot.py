# -*- coding: utf-8 -*-
"""
测试获取市场快照数据
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

test_stocks = ['600519.SH', '000001.SZ']

print("\n测试get_market_snapshot...")
for stock in test_stocks:
    print(f"\n获取 {stock} 的快照:")
    try:
        data = tq.get_market_snapshot(stock)
        print(f"  返回类型: {type(data)}")
        if data:
            print(f"  数据键: {list(data.keys())}")
            for key in list(data.keys())[:10]:
                value = data[key]
                value_str = str(value)[:50] if len(str(value)) > 50 else str(value)
                print(f"    {key}: {value_str}")
        else:
            print("  返回空数据")
    except Exception as e:
        print(f"  错误: {e}")

tq.close()
