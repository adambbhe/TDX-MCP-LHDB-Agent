# -*- coding: utf-8 -*-
"""
实时竞价数据分析系统
获取自选股的最新竞价/开盘数据并进行分析
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

print(f"\n{'='*90}")
print(f"  🚀 实时竞价数据分析系统")
print(f"  启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*90}")

# 自选股列表 (之前添加的16只)
limit_up_stocks = [
    ('000417.SZ', '合肥百货', 8.66, 10.04),
    ('000600.SZ', '建发股份', 10.88, 10.01),
    ('000586.SZ', '', 20.57, 10.00),
    ('000636.SZ', '风华高科', 32.37, 9.99),
    ('001259.SZ', '', 73.21, 10.01),
    ('000910.SZ', '大亚圣象', 7.06, 9.97),
]

strong_stocks = [
    ('000026.SZ', '', 21.64, 7.13),
    ('000404.SZ', '', 9.41, 6.33),
    ('000899.SZ', '', 13.72, 5.54),
    ('000811.SZ', '', 36.49, 5.46),
    ('000821.SZ', '', 10.02, 5.03),
    ('000609.SZ', '', 15.45, 5.03),
    ('000669.SZ', '', 4.86, 4.97),
    ('000909.SZ', '', 5.10, 4.94),
    ('000903.SZ', '', 1.97, 4.79),
    ('000993.SZ', '', 14.10, 4.29),
]

all_stocks = limit_up_stocks + strong_stocks

print(f"\n📋 待分析股票: {len(all_stocks)} 只")
print(f"   涨停股: {len(limit_up_stocks)} 只")
print(f"   强势股: {len(strong_stocks)} 只")

# 步骤1: 连接TQ接口
print(f"\n{'='*90}")
print("[步骤1] 连接TQ接口...")
print('='*90)

tq._initialized = False
tq.run_id = -1

try:
    tq.initialize(path=str(script_dir))
    print(f"\n✅ 连接成功! run_id={tq.run_id}")
    print(f"   数据时间: {datetime.now().strftime('%H:%M:%S')}")
except Exception as e:
    print(f"\n❌ 连接失败: {e}")
    sys.exit(1)

# 步骤2: 获取最新行情数据
print(f"\n{'='*90}")
print("[步骤2] 获取最新实时行情...")
print('='*90)

market_data = []
success_count = 0

for code, name, last_price, last_pct in all_stocks:
    try:
        data = tq.get_market_snapshot(code)

        if data and data.get('ErrorId') == '0':
            now_price = float(data.get('Now', 0))
            open_price = float(data.get('Open', 0))
            high_price = float(data.get('Max', 0))
            low_price = float(data.get('Min', 0))
            preclose = float(data.get('LastClose', 0))
            volume = int(float(data.get('Volume', 0)))
            amount = float(data.get('Amount', 0)) * 10000

            if now_price > 0 and preclose > 0:
                pct_change = (now_price - preclose) / preclose * 100
                high_open_pct = (open_price - preclose) / preclose * 100 if open_price > 0 else 0

                stock_info = {
                    'code': code,
                    'name': name,
                    'price': now_price,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'preclose': preclose,
                    'pct_change': pct_change,
                    'high_open_pct': high_open_pct,
                    'last_pct': last_pct,
                    'volume': volume,
                    'amount': amount,
                }

                market_data.append(stock_info)
                success_count += 1

                status = "✓"
            else:
                status = "⚠"
        else:
            status = "✗"
    except Exception as e:
        status = f"✗({str(e)[:15]})"

    print(f"  {status} {code:<12} {name if name else '':<10}")

    time.sleep(0.1)

print(f"\n✅ 成功获取 {success_count}/{len(all_stocks)} 只股票数据")

# 步骤3: 竞价数据分析
print(f"\n{'='*90}")
print("[步骤3] 竞价数据分析...")
print('='*90)

# 分类统计
very_high_open = []  # 高开 > 5%
high_open = []       # 高开 2%~5%
flat_open = []       # 平开 ±2%
low_open = []        # 低开 > -2%
very_low_open = []   # 低开 < -2%

for stock in market_data:
    ho = stock['high_open_pct']
    
    if ho >= 5:
        very_high_open.append(stock)
    elif ho >= 2:
        high_open.append(stock)
    elif ho >= -2:
        flat_open.append(stock)
    elif ho >= -5:
        low_open.append(stock)
    else:
        very_low_open.append(stock)

print(f"\n📊 开盘情况分布:")
print(f"   🔴 大幅高开 (≥+5%): {len(very_high_open)} 只")
print(f"   🟠 高开 (+2%~+5%): {len(high_open)} 只")
print(f"   🟢 平开 (±2%):      {len(flat_open)} 只")
print(f"   🔵 低开 (-2%~-5%):  {len(low_open)} 只")
print(f"   ⚫ 大幅低开 (<-5%): {len(very_low_open)} 只")

# 步骤4: 输出详细分析报告
print(f"\n{'='*90}")
print("  📈 详细分析报告")
print('='*90)

current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
print(f"\n⏰ 分析时间: {current_time}")

# 4.1 涨停股表现
if limit_up_stocks:
    print(f"\n{'='*70}")
    print(f"  🔴 昨日涨停股今日表现 ({len(limit_up_stocks)}只)")
    print(f"{'='*70}")
    
    limitup_today = [s for s in market_data if s['code'] in [x[0] for x in limit_up_stocks]]
    
    if limitup_today:
        print(f"\n{'代码':<12} {'名称':<10} {'现价':>8} {'开盘价':>8} {'涨幅%':>8} "
              f"{'高开%':>8} {'昨涨%':>8} {'成交额(万)':>10} {'状态'}")
        print("-"*90)
        
        for s in sorted(limitup_today, key=lambda x: x['pct_change'], reverse=True):
            # 判断状态
            if s['pct_change'] >= 9.8:
                status = "🔴再次涨停"
            elif s['pct_change'] >= 5:
                status = "🟢强势上涨"
            elif s['pct_change'] >= 0:
                status = "🟡小幅上涨"
            else:
                status = "🔵下跌"
            
            print(f"{s['code']:<12} {(s['name'] or ''):<10} {s['price']:>8.2f} "
                  f"{s['open']:>8.2f} {s['pct_change']:>+8.2f} "
                  f"{s['high_open_pct']:>+8.2f} {s['last_pct']:>+7.2f} "
                  f"{s['amount']/10000:>10.1f} {status}")

# 4.2 强势股表现
if strong_stocks:
    print(f"\n{'='*70}")
    print(f"  🟡 昨日强势股今日表现 ({len(strong_stocks)}只)")
    print(f"{'='*70}")
    
    strong_today = [s for s in market_data if s['code'] in [x[0] for x in strong_stocks]]
    
    if strong_today:
        print(f"\n{'代码':<12} {'名称':<10} {'现价':>8} {'开盘价':>8} {'涨幅%':>8} "
              f"{'高开%':>8} {'昨涨%':>8} {'成交额(万)':>10} {'状态'}")
        print("-"*90)
        
        for s in sorted(strong_today, key=lambda x: x['pct_change'], reverse=True):
            if s['pct_change'] >= 9.8:
                status = "🔴涨停"
            elif s['pct_change'] >= 5:
                status = "🟢强势"
            elif s['pct_change'] >= 3:
                status = "🟡上涨"
            elif s['pct_change'] >= 0:
                status = "⚪微涨"
            else:
                status = "🔵下跌"
            
            print(f"{s['code']:<12} {(s['name'] or ''):<10} {s['price']:>8.2f} "
                  f"{s['open']:>8.2f} {s['pct_change']:>+8.2f} "
                  f"{s['high_open_pct']:>+8.2f} {s['last_pct']:>+7.2f} "
                  f"{s['amount']/10000:>10.1f} {status}")

# 4.3 高开股票重点关注
if very_high_open or high_open:
    print(f"\n{'='*70}")
    print(f"  ⭐ 高开股票重点关注 (可能有机会)")
    print(f"{'='*70}")
    
    focus_stocks = very_high_open + high_open
    
    if focus_stocks:
        print(f"\n{'代码':<12} {'现价':>8} {'涨幅%':>8} {'高开%':>8} "
              f"{'成交额(万)':>10} {'建议'}")
        print("-"*65)
        
        for s in sorted(focus_stocks, key=lambda x: x['high_open_pct'], reverse=True):
            if s['high_open_pct'] >= 5:
                advice = "超强势，观察能否封板"
            else:
                advice = "强势，可关注回调机会"
            
            print(f"{s['code']:<12} {s['price']:>8.2f} {s['pct_change']:>+8.2f} "
                  f"{s['high_open_pct']:>+8.2f} {s['amount']/10000:>10.1f} {advice}")

# 4.4 低开股票预警
if very_low_open or low_open:
    print(f"\n{'='*70}")
    print(f"  ⚠️ 低开股票风险预警")
    print(f"{'='*70}")
    
    risk_stocks = very_low_open + low_open
    
    if risk_stocks:
        print(f"\n{'代码':<12} {'现价':>8} {'跌幅%':>8} {'低开%':>8} "
              f"{'成交额(万)':>10} {'建议'}")
        print("-"*65)
        
        for s in sorted(risk_stocks, key=lambda x: x['high_open_pct']):
            if s['high_open_pct'] <= -5:
                advice = "⛔ 大幅低开，回避!"
            else:
                advice = "⚠️ 观望，等企稳"
            
            print(f"{s['code']:<12} {s['price']:>8.2f} {s['pct_change']:>+8.2f} "
                  f"{s['high_open_pct']:>+8.2f} {s['amount']/10000:>10.1f} {advice}")

# 步骤5: 综合评估与操作建议
print(f"\n{'='*90}")
print("  💡 综合评估与操作建议")
print('='*90)

# 计算整体表现
if market_data:
    avg_pct = sum(s['pct_change'] for s in market_data) / len(market_data)
    up_count = len([s for s in market_data if s['pct_change'] > 0])
    down_count = len([s for s in market_data if s['pct_change'] < 0])
    
    print(f"\n📊 整体表现:")
    print(f"   平均涨幅: {avg_pct:+.2f}%")
    print(f"   上涨数量: {up_count} 只 ({up_count/len(market_data)*100:.1f}%)")
    print(f"   下跌数量: {down_count} 只 ({down_count/len(market_data)*100:.1f}%)")

# 操作建议
print(f"\n🎯 操作建议:")

if very_high_open:
    best = max(very_high_open, key=lambda x: x['amount'])
    print(f"\n  ★ 超强势股 (高开≥5%):")
    print(f"     {best['code']} 高开{best['high_open_pct']:+.2f}% 涨幅{best['pct_change']:+.2f}%")
    print(f"     建议: 观察前30分钟，若能站稳可轻仓跟进")

if high_open:
    print(f"\n  ● 强势股 (高开2%~5%):")
    print(f"     共{len(high_open)}只，可关注回调至均线附近的机会")

if flat_open:
    print(f"\n  ○ 平开股 (±2%):")
    print(f"     共{len(flat_open)}只，等待方向选择后再决定")

if low_open or very_low_open:
    print(f"\n  ⚠️ 低开股:")
    total_low = len(low_open) + len(very_low_open)
    print(f"     共{total_low}只低开，建议暂时回避或等企稳信号")

# 风险提示
print(f"\n⚠️ 风险提示:")
print(f"  • 竞价数据会变化，请以开盘后实际走势为准")
print(f"  • 高开不等于能涨停，需观察成交量配合")
print(f"  • 严格控制仓位，单只不超过15%")
print(f"  • 设置止损线 (-5%)，避免大幅亏损")

# 步骤6: 保存报告
report_dir = script_dir / 'reports'
report_dir.mkdir(exist_ok=True)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
report_file = report_dir / f'auction_analysis_{timestamp}.txt'

with open(report_file, 'w', encoding='utf-8') as f:
    f.write("="*90 + "\n")
    f.write("竞价数据分析报告\n")
    f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("="*90 + "\n\n")
    
    f.write(f"分析股票数: {len(all_stocks)}\n")
    f.write(f"成功获取: {success_count}\n\n")
    
    f.write("开盘分布:\n")
    f.write(f"  大幅高开(≥5%): {len(very_high_open)}\n")
    f.write(f"  高开(2%~5%): {len(high_open)}\n")
    f.write(f"  平开(±2%): {len(flat_open)}\n")
    f.write(f"  低开(-2%~-5%): {len(low_open)}\n")
    f.write(f"  大幅低开(<-5%): {len(very_low_open)}\n\n")
    
    if market_data:
        f.write("详细数据:\n")
        for s in sorted(market_data, key=lambda x: x['pct_change'], reverse=True):
            f.write(f"  {s['code']} 现价{s['price']:.2f} 涨幅{s['pct_change']:+.2f}% "
                   f"高开{s['high_open_pct']:+.2f}%\n")
    
    f.write("\n" + "="*90 + "\n")

print(f"\n📄 报告已保存: {report_file.name}")

# 关闭连接
tq.close()

print(f"\n{'='*90}")
print(f"  ✅ 竞价分析完成!")
print(f"{'='*90}\n")
