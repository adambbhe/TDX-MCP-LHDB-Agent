# -*- coding: utf-8 -*-
"""
添加自选股并设置预警
将筛选出的6只涨停股和10只强势股加入自选列表
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
print(f"  添加自选股 & 设置预警")
print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*80}")

# 股票列表 (基于最新扫描结果)
limit_up_stocks = [
    '000417.SZ',   # 合肥百货 - 一字涨停 +10.04%
    '000600.SZ',   # 建发股份 - 涨停 +10.01%
    '000586.SZ',   # 涨停 +10.00%
    '000636.SZ',   # 风华高科 - 涨停 +9.99%
    '001259.SZ',   # 涨停 +10.01%
    '000910.SZ',   # 大亚圣象 - 涨停 +9.97%
]

strong_stocks = [
    '000026.SZ',   # 强势 +7.13%
    '000404.SZ',   # 强势 +6.33%
    '000899.SZ',   # 强势 +5.54%
    '000811.SZ',   # 强势 +5.46%
    '000821.SZ',   # 强势 +5.03%
    '000609.SZ',   # 强势 +5.03%
    '000669.SZ',   # 强势 +4.97%
    '000909.SZ',   # 强势 +4.94%
    '000903.SZ',   # 强势 +4.79%
    '000993.SZ',   # 强势 +4.29%
]

all_stocks = limit_up_stocks + strong_stocks

print(f"\n待添加股票:")
print(f"  涨停股: {len(limit_up_stocks)} 只")
print(f"  强势股: {len(strong_stocks)} 只")
print(f"  总计: {len(all_stocks)} 只")

# 步骤1: 连接TQ
print(f"\n{'='*80}")
print("[步骤1] 连接TQ接口...")
print('='*80)

tq._initialized = False
tq.run_id = -1

try:
    tq.initialize(path=str(script_dir))
    print(f"\n✅ 连接成功! run_id={tq.run_id}")
except Exception as e:
    print(f"\n❌ 连接失败: {e}")
    sys.exit(1)

# 步骤2: 获取当前价格用于设置预警
print(f"\n{'='*80}")
print("[步骤2] 获取股票当前价格...")
print('='*80)

stock_prices = {}

for code in all_stocks:
    try:
        data = tq.get_market_snapshot(code)
        if data and data.get('ErrorId') == '0':
            price = float(data.get('Now', 0))
            preclose = float(data.get('LastClose', 0))
            stock_prices[code] = {
                'price': price,
                'preclose': preclose,
            }
            print(f"  ✓ {code}: 现价{price:.2f}")
        else:
            print(f"  ⚠ {code}: 数据获取失败")
    except Exception as e:
        print(f"  ✗ {code}: 错误")

time.sleep(0.5)

# 步骤3: 添加到自选列表
print(f"\n{'='*80}")
print("[步骤3] 添加股票到自选列表...")
print('='*80)

block_name = "今日精选_涨停强势"
print(f"\n自定义板块名称: {block_name}")

try:
    result = tq.send_user_block(
        block_code=block_name,
        stocks=all_stocks,
        show=True
    )

    if result and result.get('ErrorId') == '0':
        print(f"\n✅ 成功! 已将 {len(all_stocks)} 只股票添加到自选列表")
        print(f"   请在通达信客户端查看 '{block_name}' 自定义板块")
    else:
        error_msg = result.get('Error', '未知错误') if result else '返回空'
        print(f"\n❌ 添加失败: {error_msg}")

except Exception as e:
    print(f"\n❌ 异常: {e}")

time.sleep(1)

# 步骤4: 设置价格预警
print(f"\n{'='*80}")
print("[步骤4] 设置价格预警...")
print('='*80)

now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

warn_success = 0
warn_failed = 0

for code in all_stocks:
    if code not in stock_prices:
        continue

    price_info = stock_prices[code]
    current_price = price_info['price']
    preclose = price_info['preclose']

    if current_price <= 0 or preclose <= 0:
        continue

    # 计算预警价格 (涨跌±3%)
    alert_up = round(preclose * 1.03, 2)
    alert_down = round(preclose * 0.97, 2)

    try:
        # 发送上涨预警
        result_up = tq.send_warn(
            stock_list=[code],
            time_list=[now_time],
            price_list=[str(alert_up)],
            close_list=[str(current_price)],
            volum_list=['0'],
            bs_flag_list=['1'],       # 买入信号
            warn_type_list=['0'],     # 价格预警
            reason_list=[f'涨幅达+3% 当前价:{current_price:.2f}'],
            count=1
        )

        time.sleep(0.3)

        # 发送下跌预警
        result_down = tq.send_warn(
            stock_list=[code],
            time_list=[now_time],
            price_list=[str(alert_down)],
            close_list=[str(current_price)],
            volum_list=['0'],
            bs_flag_list=['0'],       # 卖出信号
            warn_type_list=['0'],     # 价格预警
            reason_list=[f'跌幅达-3% 当前价:{current_price:.2f}'],
            count=1
        )

        if (result_up and result_up.get('ErrorId') == '0') or \
           (result_down and result_down.get('ErrorId') == '0'):
            warn_success += 1
            status = "✓"
        else:
            warn_failed += 1
            status = "✗"

        print(f"  {status} {code} 现价:{current_price:.2f} "
              f"预警:{alert_down:.2f}~{alert_up:.2f}")

    except Exception as e:
        warn_failed += 1
        print(f"  ✗ {code}: {str(e)[:40]}")

    time.sleep(0.2)

print(f"\n预警设置结果:")
print(f"  成功: {warn_success} 只")
print(f"  失败: {warn_failed} 只")

# 步骤5: 输出汇总
print(f"\n{'='*80}")
print("  操作完成汇总")
print('='*80)

print(f"\n📋 已添加到自选的股票 ({len(all_stocks)}只):")
print(f"\n{'='*60}")
print(f"{'类型':<8} {'代码':<12} {'现价':>8} {'涨跌幅':>8} {'预警区间':>16}")
print("-"*56)

for i, code in enumerate(all_stocks, 1):
    if code in stock_prices:
        price = stock_prices[code]['price']
        preclose = stock_prices[code]['preclose']
        pct = (price - preclose) / preclose * 100 if preclose > 0 else 0
        alert_up = round(preclose * 1.03, 2)
        alert_down = round(preclose * 0.97, 2)

        stock_type = "涨停" if code in limit_up_stocks else "强势"

        print(f"{stock_type:<8} {code:<12} {price:>8.2f} {pct:>+7.2f}% "
              f"{alert_down:.2f}~{alert_up:.2f}")
    else:
        stock_type = "涨停" if code in limit_up_stocks else "强势"
        print(f"{stock_type:<8} {code:<12} {'N/A':>8} {'N/A':>8} {'获取失败':>16}")

print(f"\n{'='*60}")

print(f"\n💡 提示:")
print(f"  • 请在通达信客户端查看自选板块: '{block_name}'")
print(f"  • 预警已设置为涨跌 ±3%")
print(f"  • 当股价触及预警线时，通达信会弹出提示")

print(f"\n⚠️ 注意事项:")
print(f"  • 涨停股风险较高，建议优先观察")
print(f"  • 严格执行止损纪律 (-5%)")
print(f"  • 控制仓位，单只不超过15%")

# 关闭连接
tq.close()

print(f"\n{'='*80}")
print(f"  ✅ 所有操作完成!")
print(f"{'='*80}\n")
