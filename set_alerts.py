# -*- coding: utf-8 -*-
"""
修复版 - 设置价格预警
"""

import sys
import time
from datetime import datetime
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from tqcenter import tq

print(f"\n{'='*80}")
print(f"  重新设置价格预警")
print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*80}")

# 股票列表
limit_up_stocks = [
    '000417.SZ',   # 合肥百货
    '000600.SZ',   # 建发股份
    '000586.SZ',
    '000636.SZ',   # 风华高科
    '001259.SZ',
    '000910.SZ',   # 大亚圣象
]

strong_stocks = [
    '000026.SZ',
    '000404.SZ',
    '000899.SZ',
    '000811.SZ',
    '000821.SZ',
    '000609.SZ',
    '000669.SZ',
    '000909.SZ',
    '000903.SZ',
    '000993.SZ',
]

all_stocks = limit_up_stocks + strong_stocks

# 连接
print("\n[1/3] 连接TQ接口...")
tq._initialized = False
tq.run_id = -1

try:
    tq.initialize(path=str(script_dir))
    print(f"  成功! run_id={tq.run_id}")
except Exception as e:
    print(f"  失败: {e}")
    sys.exit(1)

# 获取价格
print("\n[2/3] 获取当前价格...")
stock_prices = {}

for code in all_stocks:
    try:
        data = tq.get_market_snapshot(code)
        if data and data.get('ErrorId') == '0':
            price = float(data.get('Now', 0))
            preclose = float(data.get('LastClose', 0))
            stock_prices[code] = {'price': price, 'preclose': preclose}
            print(f"  {code}: {price:.2f}")
    except:
        pass

time.sleep(0.5)

# 设置预警 (使用正确的时间格式 YYYYMMDDHHMMSS)
print(f"\n[3/3] 设置预警...")

now = datetime.now()
time_str = now.strftime("%Y%m%d%H%M%S")  # 正确格式!

warn_ok = 0
warn_fail = 0

for code in all_stocks:
    if code not in stock_prices:
        continue

    price_info = stock_prices[code]
    current_price = price_info['price']
    preclose = price_info['preclose']

    if current_price <= 0 or preclose <= 0:
        continue

    alert_up = round(preclose * 1.03, 2)
    alert_down = round(preclose * 0.97, 2)

    try:
        result = tq.send_warn(
            stock_list=[code],
            time_list=[time_str],
            price_list=[str(current_price)],
            close_list=[str(preclose)],
            volum_list=['0'],
            bs_flag_list=['1'],
            warn_type_list=['0'],
            reason_list=[f'关注 {code} 现价{current_price:.2f} 涨幅{(current_price-preclose)/preclose*100:+.2f}%'],
            count=1
        )

        if result and result.get('ErrorId') == '0':
            warn_ok += 1
            print(f"  ✓ {code} ({current_price:.2f}) 预警设置成功")
        else:
            warn_fail += 1
            error = result.get('Error', '?') if result else '空'
            print(f"  ✗ {code}: {error}")

    except Exception as e:
        warn_fail += 1
        print(f"  ✗ {code}: {str(e)[:50]}")

    time.sleep(0.3)

# 结果
print(f"\n{'='*80}")
print(f"  预警设置完成!")
print(f"{'='*80}")

print(f"\n统计:")
print(f"  成功: {warn_ok} 只")
print(f"  失败: {warn_fail} 只")

if warn_ok > 0:
    print(f"\n✅ 已为 {warn_ok} 只股票设置预警")
    print(f"   请在通达信客户端查看预警提示")

print(f"\n📋 所有股票汇总:")
print(f"{'='*70}")
print(f"{'类型':<6} {'代码':<12} {'现价':>8} {'涨幅%':>8} {'+3%价':>8} {'-3%价':>8}")
print("-"*64)

for code in all_stocks:
    if code in stock_prices:
        p = stock_prices[code]['price']
        pc = stock_prices[code]['preclose']
        pct = (p - pc) / pc * 100 if pc > 0 else 0
        up = round(pc * 1.03, 2)
        down = round(pc * 0.97, 2)
        t = "涨停" if code in limit_up_stocks else "强势"
        print(f"{t:<6} {code:<12} {p:>8.2f} {pct:>+7.2f}% {up:>8.2f} {down:>8.2f}")

print("="*70)

# 关闭
tq.close()

print(f"\n✅ 完成!\n")
