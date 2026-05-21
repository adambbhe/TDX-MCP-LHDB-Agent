# -*- coding: utf-8 -*-
"""
今日涨停快速扫描
使用最简单的方式获取数据
"""

import sys
import os
from datetime import datetime
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

print("\n" + "="*90)
print("  🚀 今日涨停快速扫描")
print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*90)

# 导入TQ
try:
    from tqcenter import tq
    print("\n✅ TQ模块导入成功")
except Exception as e:
    print(f"\n❌ 导入失败: {e}")
    sys.exit(1)

# 初始化
print("\n📡 正在连接...")
try:
    tq.initialize(path=str(script_dir))
    print(f"✅ 连接成功! run_id={tq.run_id}")
except Exception as e:
    print(f"❌ 连接失败: {e}")
    print("\n可能的原因:")
    print("1. 通达信软件未打开")
    print("2. TQ接口未启动")
    print("3. 已有同名策略运行")
    input("\n按回车退出...")
    sys.exit(1)

# 获取股票列表
print("\n📋 获取股票列表...")
try:
    stocks = tq.get_stock_list()
    if isinstance(stocks, list):
        stock_list = [s for s in stocks if s and '.' in str(s)][:300]
    else:
        stock_list = []
    print(f"✅ 获取到 {len(stock_list)} 只股票 (演示模式)")
except Exception as e:
    print(f"❌ 失败: {e}")
    tq.close()
    sys.exit(1)

# 扫描行情
print("\n⏱️ 开始扫描...")

results = []
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

                results.append({
                    'code': code,
                    'price': price,
                    'pct': pct,
                    'high_open': high_open,
                    'amount': amount,
                })
    except:
        pass

    if i % 50 == 0 or i == total:
        limit_count = len([r for r in results if r['pct'] >= 9.8])
        strong_count = len([r for r in results if r['pct'] >= 3.0])
        print(f"   进度: {i}/{total} | 有效:{len(results)} "
              f"涨停:{limit_count} 强势:{strong_count}")

# 排序
results.sort(key=lambda x: x['pct'], reverse=True)

# 输出结果
limit_ups = [r for r in results if r['pct'] >= 9.8]
strong = [r for r in results if 3.0 <= r['pct'] < 9.8]

print(f"\n{'='*90}")
print(f"  📊 扫描结果")
print(f"{'='*90}")

print(f"\n✅ 扫描完成:")
print(f"   总计: {len(results)} 只有效数据")
print(f"   涨停: {len(limit_ups)} 只")
print(f"   强势: {len(strong)} 只")

if limit_ups:
    print(f"\n{'🔴 涨停股票':=^60}")
    print(f"{'代码':<12} {'现价':>8} {'涨幅%':>8} {'高开%':>8} {'成交额(万)':>10}")
    print("-"*56)

    for r in sorted(limit_ups, key=lambda x: x['amount'], reverse=True)[:10]:
        print(f"{r['code']:<12} {r['price']:>8.2f} {r['pct']:>8.2f} "
              f"{r['high_open']:>8.2f} {r['amount']/10000:>10.1f}")

if strong:
    print(f"\n{'🟡 强势上涨 TOP10':=^60}")
    print(f"{'排名':<4} {'代码':<12} {'现价':>8} {'涨幅%':>8} {'高开%':>8}")
    print("-"*48)

    for i, r in enumerate(strong[:10], 1):
        print(f"{i:<4} {r['code']:<12} {r['price']:>8.2f} "
              f"{r['pct']:>8.2f} {r['high_open']:>8.2f}")

print(f"\n{'⭐ 涨幅排行 TOP15':=^60}")
print(f"{'排名':<4} {'代码':<12} {'现价':>8} {'涨幅%':>8} {'状态':<8}")
print("-" * 46)

for i, r in enumerate(results[:15], 1):
    status = "涨停" if r['pct'] >= 9.8 else "强势" if r['pct'] >= 3 else "其他"
    print(f"{i:<4} {r['code']:<12} {r['price']:>8.2f} "
          f"{r['pct']:>8.2f} {status:<8}")

# 建议
print(f"\n💡 操作建议:")
if limit_ups:
    best = max(limit_ups, key=lambda x: x['amount'])
    print(f"   ★ 最强涨停: {best['code']} (涨幅{best['pct']:.2f}%)")
print(f"   ⚠️ 涨停风险高，建议观察封板强度后再决定")
print(f"   ⚠️ 严格控制仓位，设置止损(-5%)")

# 保存报告
report_dir = script_dir / 'reports'
report_dir.mkdir(exist_ok=True)
ts = datetime.now().strftime('%Y%m%d_%H%M%S')
report_file = report_dir / f'quick_scan_{ts}.txt'

with open(report_file, 'w', encoding='utf-8') as f:
    f.write(f"快速扫描报告 - {datetime.now()}\n\n")
    f.write(f"扫描数量: {total}\n")
    f.write(f"有效数据: {len(results)}\n")
    f.write(f"涨停: {len(limit_ups)}\n\n")

    if limit_ups:
        f.write("涨停股票:\n")
        for r in sorted(limit_ups, key=lambda x: x['amount'], reverse=True):
            f.write(f"  {r['code']} {r['price']:.2f} {r['pct']:.2f}%\n")

print(f"\n📄 报告已保存: {report_file.name}")

# 关闭
tq.close()

print(f"\n{'='*90}")
print(f"  ✅ 扫描完成!")
print(f"{'='*90}")

input("\n按回车键退出...")
