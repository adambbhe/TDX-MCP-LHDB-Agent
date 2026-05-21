# -*- coding: utf-8 -*-
"""
最新数据快速获取 - 基于成功连接
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
print(f"  最新涨停选股扫描")
print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*80}")

# 连接
print("\n[1/4] 连接TQ接口...")
tq._initialized = False
tq.run_id = -1

try:
    tq.initialize(path=str(script_dir))
    print(f"    成功! run_id={tq.run_id}")
except Exception as e:
    print(f"    失败: {e}")
    sys.exit(1)

# 获取股票列表
print("\n[2/4] 获取股票列表...")
try:
    stocks = tq.get_stock_list()
    if isinstance(stocks, list):
        stock_list = [s for s in stocks if s and '.' in str(s)][:500]
    else:
        stock_list = []
    print(f"    获取{len(stock_list)}只")
except Exception as e:
    print(f"    失败: {e}")
    tq.close()
    sys.exit(1)

# 扫描行情
print(f"\n[3/4] 扫描实时行情 ({len(stock_list)}只)...")

results = []
limit_ups = []
strong_stocks = []

start_time = time.time()

for i, code in enumerate(stock_list, 1):
    try:
        data = tq.get_market_snapshot(code)
        if data and data.get('ErrorId') == '0':
            price = float(data.get('Now', 0))
            preclose = float(data.get('LastClose', 0))
            open_price = float(data.get('Open', 0))

            if price > 0 and preclose > 0:
                pct = (price - preclose) / preclose * 100
                high_open = (open_price - preclose) / preclose * 100 if open_price > 0 else 0
                amount = float(data.get('Amount', 0)) * 10000

                info = {
                    'code': code,
                    'price': price,
                    'pct': pct,
                    'high_open': high_open,
                    'amount': amount,
                }
                results.append(info)

                if pct >= 9.8:
                    limit_ups.append(info)
                elif pct >= 3.0:
                    strong_stocks.append(info)
    except:
        pass

    if i % 100 == 0 or i == len(stock_list):
        print(f"    进度:{i}/{len(stock_list)} 有效:{len(results)} 涨停:{len(limit_ups)} 强势:{len(strong_stocks)}")

scan_time = time.time() - start_time

# 排序
results.sort(key=lambda x: x['pct'], reverse=True)
limit_ups.sort(key=lambda x: x['amount'], reverse=True)
strong_stocks.sort(key=lambda x: x['pct'], reverse=True)

# 输出结果
print(f"\n{'='*80}")
print(f"  扫描完成! 耗时:{scan_time:.1f}秒")
print(f"{'='*80}")

print(f"\n时间: {datetime.now().strftime('%H:%M:%S')}")
print(f"\n统计:")
print(f"  有效数据: {len(results)}只")
print(f"  涨停股: {len(limit_ups)}只")
print(f"  强势股(≥3%): {len(strong_stocks)}只")

if limit_ups:
    print(f"\n{'🔴 今日涨停':=^60}")
    print(f"{'代码':<12} {'现价':>8} {'涨幅%':>8} {'高开%':>8} {'成交额(万)':>10}")
    print("-"*56)
    for s in limit_ups[:15]:
        print(f"{s['code']:<12} {s['price']:>8.2f} {s['pct']:>8.2f} "
              f"{s['high_open']:>8.2f} {s['amount']/10000:>10.1f}")

if strong_stocks:
    print(f"\n{'🟡 强势上涨TOP10':=^60}")
    print(f"{'排名':<4} {'代码':<12} {'现价':>8} {'涨幅%':>8} {'高开%':>8}")
    print("-"*52)
    for i, s in enumerate(strong_stocks[:10], 1):
        print(f"{i:<4} {s['code']:<12} {s['price']:>8.2f} "
              f"{s['pct']:>8.2f} {s['high_open']:>8.2f}")

print(f"\n{'⭐ 涨幅TOP20':=^60}")
print(f"{'排名':<4} {'代码':<12} {'现价':>8} {'涨幅%':>8} {'状态':<8}")
print("-*" * 24)
for i, s in enumerate(results[:20], 1):
    status = "涨停" if s['pct'] >= 9.8 else "强势" if s['pct'] >= 3 else "其他"
    print(f"{i:<4} {s['code']:<12} {s['price']:>8.2f} {s['pct']:>8.2f} {status:<8}")

if limit_ups:
    best = limit_ups[0]
    print(f"\n💡 最强涨停: {best['code']} 涨幅{best['pct']:.2f}% 成交额{best['amount']/10000:.1f}万")

print(f"\n⚠️ 风险提示: 涨停风险高，控制仓位≤15%，止损-5%")

# 保存报告
report_dir = script_dir / 'reports'
report_dir.mkdir(exist_ok=True)
ts = datetime.now().strftime('%Y%m%d_%H%M%S')
report_file = report_dir / f'latest_{ts}.txt'

with open(report_file, 'w', encoding='utf-8') as f:
    f.write(f"最新扫描 {datetime.now()}\n\n")
    f.write(f"有效:{len(results)} 涨停:{len(limit_ups)}\n\n")
    if limit_ups:
        f.write("涨停:\n")
        for s in limit_ups:
            f.write(f"  {s['code']} {s['price']:.2f} {s['pct']:.2f}%\n")
    f.write(f"\n耗时:{scan_time:.1f}s\n")

print(f"\n📄 报告: {report_file.name}")

# 关闭
tq.close()

print(f"\n[4/4] 完成!")
print(f"{'='*80}\n")
