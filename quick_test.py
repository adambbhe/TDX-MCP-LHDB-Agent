# -*- coding: utf-8 -*-
"""
快速连接测试 - 简化版
"""

import sys
from pathlib import Path
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

print(f"\n{'='*70}")
print(f"  快速连接测试")
print(f"  时间: {datetime.now().strftime('%H:%M:%S')}")
print(f"{'='*70}")

# 导入
print("\n[1] 导入模块...")
try:
    from tqcenter import tq
    print("    OK")
except Exception as e:
    print(f"    失败: {e}")
    sys.exit(1)

# 重置
print("\n[2] 重置状态...")
tq._initialized = False
tq.run_id = -1
print("    OK")

# 连接
print("\n[3] 连接TQ...")
import time
time.sleep(0.5)

try:
    tq.initialize(path=str(script_dir))
    print(f"    成功! run_id={tq.run_id}")
except Exception as e:
    print(f"    失败: {e}")
    sys.exit(1)

# 测试数据
print("\n[4] 测试数据获取...")

for code in ['600519.SH', '000001.SZ']:
    try:
        data = tq.get_market_snapshot(code)
        if data and data.get('ErrorId') == '0':
            price = data.get('Now', 'N/A')
            print(f"    {code}: 价格={price} ✓")
        else:
            print(f"    {code}: 数据异常")
    except Exception as e:
        print(f"    {code}: 错误 {str(e)[:40]}")

# 关闭
tq.close()
print("\n[5] 完成!")
