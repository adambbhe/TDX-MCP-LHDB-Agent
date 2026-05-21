# -*- coding: utf-8 -*-
"""
自动连接并扫描 - 无需手动输入
"""

import sys
import os
import time
from datetime import datetime
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

print("\n" + "="*90)
print("  🔄 自动连接与扫描")
print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*90)

# 导入模块
print("\n[1/5] 导入TQ模块...")
try:
    from tqcenter import tq, dll
    print("  ✅ 成功")
except Exception as e:
    print(f"  ❌ 失败: {e}")
    sys.exit(1)

# 重置状态
print("\n[2/5] 重置连接状态...")
tq._initialized = False
tq.run_id = -1
if tq._finalizer is not None:
    try:
        tq._finalizer()
    except:
        pass
    tq._finalizer = None
try:
    dll.CloseConnect(tq.run_id, tq.run_mode)
except:
    pass
time.sleep(1)
print("  ✅ 完成")

# 多次尝试连接
print("\n[3/5] 连接TQ接口 (最多3次)...")

for attempt in range(1, 4):
    print(f"\n  第{attempt}次尝试...")
    tq._initialized = False
    tq.run_id = -1

    try:
        tq.initialize(path=str(script_dir))
        if tq._initialized and tq.run_id >= 0:
            print(f"  ✅ 成功! run_id={tq.run_id}")
            break
        else:
            print(f"  ❌ 未成功")
    except Exception as e:
        print(f"  ❌ 异常: {str(e)[:60]}")

    if attempt < 3:
        time.sleep(attempt * 2)
else:
    print("\n❌ 连接失败，退出")
    sys.exit(1)

# 测试数据获取
print("\n[4/5] 测试数据获取...")
test_ok = True
for stock in ['600519.SH', '000001.SZ']:
    try:
        data = tq.get_market_snapshot(stock)
        if data and data.get('ErrorId') == '0':
            print(f"  ✅ {stock} 价格={data.get('Now', 'N/A')}")
        else:
            test_ok = False
    except Exception as e:
        print(f"  ⚠️ {stock}: {str(e)[:40]}")
        test_ok = False

# 获取股票列表
print("\n[5/5] 扫描市场...")
try:
    stocks = tq.get_stock_list()
    if isinstance(stocks, list):
        stock_list = [s for s in stocks if s and '.' in str(s)][:500]
    elif hasattr(stocks, 'iterrows'):
        stock_list = [row['code'] for _, row in stocks.iterrows()
                     if row.get('code') and '.' in str(row['code'])][:500]
    else:
        stock_list = []
    print(f"  扫描{len(stock_list)}只...")
except Exception as e:
    print(f"  ❌ {e}")
    stock_list = []

# 扫描行情
results = []
limit_ups = []
strong_stocks = []
start_time = time.time()

total = len(stock_list)
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

    if i % 200 == 0 or i == total:
        print(f"  进度: {i}/{total} 有效:{len(results)} 涨停:{len(limit_ups)}")

scan_time = time.time() - start_time

# 排序
results.sort(key=lambda x: x['pct'], reverse=True)
limit_ups.sort(key=lambda x: x['amount'], reverse=True)

# 输出结果
print(f"\n{'='*90}")
print(f"  📊 扫描完成! 耗时:{scan_time:.1f}s")
print(f"{'='*90}")

print(f"\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"\n统计:")
print(f"  总计: {len(results)}只 | 涨停:{len(limit_ups)}只 | 强势:{len(strong_stocks)}只")

if limit_ups:
    print(f"\n{'🔴 涨停股':=^60}")
    print(f"{'代码':<12} {'现价':>8} {'涨幅%':>8} {'高开%':>8} {'成交额(万)':>10}")
    print("-"*56)
    for s in limit_ups[:15]:
        print(f"{s['code']:<12} {s['price']:>8.2f} {s['pct']:>8.2f} "
              f"{s['high_open']:>8.2f} {s['amount']/10000:>10.1f}")

if strong_stocks:
    print(f"\n{'🟡 强势TOP10':=^60}")
    print(f"{'排名':<4} {'代码':<12} {'现价':>8} {'涨幅%':>8}")
    print("-"*40)
    for i, s in enumerate(strong_stocks[:10], 1):
        print(f"{i:<4} {s['code']:<12} {s['price']:>8.2f} {s['pct']:>8.2f}")

print(f"\n{'⭐ TOP20':=^60}")
print(f"{'排名':<4} {'代码':<12} {'现价':>8} {'涨幅%':>8} {'状态':<8}")
print("-*" * 24)
for i, s in enumerate(results[:20], 1):
    status = "涨停" if s['pct'] >= 9.8 else "强势" if s['pct'] >= 3 else "其他"
    print(f"{i:<4} {s['code']:<12} {s['price']:>8.2f} {s['pct']:>8.2f} {status:<8}")

if limit_ups:
    best = limit_ups[0]
    print(f"\n💡 推荐: {best['code']} 涨幅{best['pct']:.2f}% 成交额{best['amount']/10000:.1f}万")

print(f"\n⚠️ 风险提示:")
print(f"  • 涨停风险高，需谨慎操作")
print(f"  • 控制仓位≤15%，止损-5%")

# 保存报告
report_dir = script_dir / 'reports'
report_dir.mkdir(exist_ok=True)
ts = datetime.now().strftime('%Y%m%d_%H%M%S')
report_file = report_dir / f'auto_scan_{ts}.txt'

with open(report_file, 'w', encoding='utf-8') as f:
    f.write(f"自动扫描报告 {datetime.now()}\n\n")
    f.write(f"扫描数:{total} 有效:{len(results)} 涨停:{len(limit_ups)}\n\n")
    if limit_ups:
        f.write("涨停:\n")
        for s in limit_ups:
            f.write(f"{s['code']} {s['price']:.2f} {s['pct']:.2f}%\n")

print(f"\n📄 报告: {report_file.name}")

# 关闭
tq.close()

print(f"\n{'='*90}")
print("  ✅ 完成!")
print("="*90 + "\n")
