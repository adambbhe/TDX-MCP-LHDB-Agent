# -*- coding: utf-8 -*-
"""
增强版TQ连接测试与数据获取脚本
功能:
1. 强制清理旧连接状态
2. 多次重试机制
3. 详细的状态诊断
4. 成功后立即扫描市场数据
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
print("  🔄 增强版TQ接口连接测试")
print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*90)

# 步骤1: 导入模块
print("\n[步骤1] 导入TQ模块...")
try:
    import tqcenter
    from tqcenter import tq, dll
    print("  ✅ 模块导入成功")
except Exception as e:
    print(f"  ❌ 导入失败: {e}")
    sys.exit(1)

# 步骤2: 强制重置连接状态
print("\n[步骤2] 重置连接状态...")

def force_reset_connection():
    """强制重置所有连接状态"""
    try:
        # 重置类变量
        tq._initialized = False
        tq.run_id = -1
        tq.run_mode = -1

        # 清理finalizer
        if tq._finalizer is not None:
            try:
                tq._finalizer()
            except:
                pass
            tq._finalizer = None

        # 尝试关闭DLL连接
        try:
            dll.CloseConnect(tq.run_id, tq.run_mode)
        except:
            pass

        print("  ✅ 状态重置完成")
        return True

    except Exception as e:
        print(f"  ⚠️ 重置时出现异常: {e}")
        return False

force_reset_connection()

# 等待一下
time.sleep(2)

# 步骤3: 尝试多次连接
print("\n[步骤3] 尝试建立连接 (最多5次)...")

max_retries = 5
connected = False

for attempt in range(1, max_retries + 1):
    print(f"\n  📡 第 {attempt}/{max_retries} 次尝试...")

    # 再次确保状态干净
    tq._initialized = False
    tq.run_id = -1

    try:
        # 初始化连接
        tq.initialize(path=str(script_dir))

        # 检查结果
        if tq._initialized and tq.run_id >= 0:
            print(f"  ✅ 连接成功!")
            print(f"     run_id: {tq.run_id}")
            print(f"     run_mode: {tq.run_mode}")
            connected = True
            break
        else:
            print(f"  ❌ 初始化未成功")

    except Exception as e:
        error_msg = str(e)
        print(f"  ❌ 异常: {error_msg[:80]}")

    # 如果不是最后一次，等待后重试
    if attempt < max_retries:
        wait_time = attempt * 2
        print(f"  ⏳ 等待 {wait_time} 秒后重试...")
        time.sleep(wait_time)
        # 再次重置
        force_reset_connection()

if not connected:
    print("\n" + "="*90)
    print("  ❌ 所有尝试均失败")
    print("="*90)
    print("\n可能的原因:")
    print("  1. 通达信软件未启动或未登录")
    print("  2. TQ插件未正确加载")
    print("  3. DLL文件路径错误")
    print("  4. 网络连接问题")
    print("\n建议操作:")
    print("  • 确保通达信已打开且登录了账户")
    print("  • 在通达信中检查TQ策略是否启用")
    print("  • 重启通达信软件后再试")
    input("\n按回车键退出...")
    sys.exit(1)

# 步骤4: 测试数据获取
print("\n" + "="*90)
print("[步骤4] 验证数据获取能力...")
print("="*90)

test_stocks = ['600519.SH', '000001.SZ']
all_ok = True

for stock in test_stocks:
    print(f"\n  测试 {stock}:")
    try:
        data = tq.get_market_snapshot(stock)
        if data and data.get('ErrorId') == '0':
            price = data.get('Now', 'N/A')
            name = data.get('Name', stock)
            print(f"  ✅ 获取成功 - 价格: {price}")
        else:
            print(f"  ⚠️ 返回异常数据")
            all_ok = False
    except Exception as e:
        print(f"  ❌ 失败: {str(e)[:50]}")
        all_ok = False

if not all_ok:
    print("\n⚠️ 数据获取存在问题，但继续尝试完整扫描...")

# 步骤5: 完整市场扫描
print("\n" + "="*90)
print("[步骤5] 开始全市场扫描...")
print("="*90)

# 获取股票列表
print("\n📋 获取股票列表...")
try:
    stocks = tq.get_stock_list()
    if isinstance(stocks, list):
        stock_list = [s for s in stocks if s and '.' in str(s)]
    elif hasattr(stocks, 'iterrows'):
        stock_list = [row['code'] for _, row in stocks.iterrows()
                     if row.get('code') and '.' in str(row['code'])]
    else:
        stock_list = list(stocks) if stocks else []

    print(f"✅ 获取到 {len(stock_list)} 只股票")

    # 限制数量以加快速度（可调整）
    SCAN_LIMIT = 500
    if len(stock_list) > SCAN_LIMIT:
        stock_list = stock_list[:SCAN_LIMIT]
        print(f"⚠️ 演示模式: 扫描前 {SCAN_LIMIT} 只")

except Exception as e:
    print(f"❌ 获取失败: {e}")
    tq.close()
    sys.exit(1)

# 扫描实时行情
print(f"\n⏱️ 扫描实时行情 ({len(stock_list)} 只股票)...")

results = []
limit_up_stocks = []
strong_stocks = []
high_open_stocks = []

start_scan = time.time()
total = len(stock_list)

for i, code in enumerate(stock_list, 1):
    try:
        data = tq.get_market_snapshot(code)

        if data and data.get('ErrorId') == '0':
            try:
                now_price = float(data.get('Now', 0))
                open_price = float(data.get('Open', 0))
                high_price = float(data.get('Max', 0))
                low_price = float(data.get('Min', 0))
                last_close = float(data.get('LastClose', 0))
                volume = int(float(data.get('Volume', 0)))
                amount = float(data.get('Amount', 0))

                if now_price > 0 and last_close > 0:
                    pct_change = (now_price - last_close) / last_close * 100
                    high_open_pct = (open_price - last_close) / last_close * 100 if open_price > 0 else 0

                    # 判断分类
                    is_limit_up = pct_change >= 9.8
                    is_near_limit = 8.0 <= pct_change < 9.8
                    is_strong = 3.0 <= pct_change < 8.0
                    is_high_open = high_open_pct >= 1.0

                    stock_info = {
                        'code': code,
                        'price': now_price,
                        'open': open_price,
                        'high': high_price,
                        'low': low_price,
                        'preclose': last_close,
                        'pct_change': pct_change,
                        'high_open_pct': high_open_pct,
                        'volume': volume,
                        'amount': amount * 10000,  # 转为元
                    }

                    results.append(stock_info)

                    if is_limit_up:
                        limit_up_stocks.append(stock_info)
                    elif is_near_limit or is_strong:
                        strong_stocks.append(stock_info)
                    if is_high_open:
                        high_open_stocks.append(stock_info)

            except (ValueError, TypeError):
                pass

    except Exception:
        pass

    # 进度显示
    if i % 100 == 0 or i == total:
        elapsed = time.time() - start_scan
        speed = i / elapsed if elapsed > 0 else 0
        eta = (total - i) / speed if speed > 0 else 0

        print(f"  进度: {i}/{total} ({i/total*100:.1f}%) | "
              f"有效:{len(results)} 涨停:{len(limit_up_stocks)} "
              f"强势:{len(strong_stocks)} | "
              f"速度:{speed:.1f}/s 预计剩余:{eta:.0f}s")

scan_time = time.time() - start_scan

# 排序
results.sort(key=lambda x: x['pct_change'], reverse=True)
limit_up_stocks.sort(key=lambda x: x['amount'], reverse=True)
strong_stocks.sort(key=lambda x: x['pct_change'], reverse=True)

# 输出结果
print(f"\n{'='*90}")
print(f"  📊 扫描完成! (耗时: {scan_time:.2f} 秒)")
print(f"{'='*90}")

print(f"\n⏰ 扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"\n📈 统计摘要:")
print(f"   扫描总数: {total} 只")
print(f"   有效数据: {len(results)} 只 ({len(results)/total*100:.1f}%)")
print(f"   🔴 涨停: {len(limit_up_stocks)} 只")
print(f"   🟢 强势上涨(≥3%): {len(strong_stocks)} 只")
print(f"   🔵 高开(≥1%): {len(high_open_stocks)} 只")

if limit_up_stocks:
    print(f"\n{'🔴 今日涨停股票':=^70}")
    print(f"{'序号':<4} {'代码':<12} {'现价':>8} {'涨幅%':>8} {'高开%':>8} {'成交额(万)':>12}")
    print("-"*64)

    for i, s in enumerate(limit_up_stocks[:15], 1):
        amount_wan = s['amount'] / 10000
        print(f"{i:<4} {s['code']:<12} {s['price']:>8.2f} "
              f"{s['pct_change']:>8.2f} {s['high_open_pct']:>8.2f} "
              f"{amount_wan:>12.1f}")

if strong_stocks:
    print(f"\n{'🟡 强势上涨 TOP10':=^70}")
    print(f"{'排名':<4} {'代码':<12} {'现价':>8} {'涨幅%':>8} {'高开%':>8}")
    print("-"*52)

    for i, s in enumerate(strong_stocks[:10], 1):
        print(f"{i:<4} {s['code']:<12} {s['price']:>8.2f} "
              f"{s['pct_change']:>8.2f} {s['high_open_pct']:>8.2f}")

print(f"\n{'⭐ 涨幅排行榜 TOP20':=^70}")
print(f"{'排名':<4} {'代码':<12} {'现价':>8} {'涨幅%':>8} {'状态':<8}")
print("-*" * 28)

for i, s in enumerate(results[:20], 1):
    if s['pct_change'] >= 9.8:
        status = "涨停"
    elif s['pct_change'] >= 8.0:
        status = "近涨"
    elif s['pct_change'] >= 3.0:
        status = "强势"
    elif s['pct_change'] >= 1.0:
        status = "上涨"
    elif s['pct_change'] > 0:
        status = "微涨"
    else:
        status = "下跌"

    print(f"{i:<4} {s['code']:<12} {s['price']:>8.2f} "
          f"{s['pct_change']:>8.2f} {status:<8}")

# 操作建议
print(f"\n💡 操作建议:")

if limit_up_stocks:
    best = limit_up_stocks[0]
    print(f"\n  ★ 最强涨停:")
    print(f"    {best['code']} 现价{best['price']:.2f}元 "
          f"涨幅{best['pct_change']:.2f}% 成交额{best['amount']/10000:.1f}万")

    print(f"\n  📌 涨停股特征分析:")
    avg_pct = sum(s['pct_change'] for s in limit_up_stocks) / len(limit_up_stocks)
    avg_amount = sum(s['amount'] for s in limit_up_stocks) / len(limit_up_stocks)
    one_word_count = len([s for s in limit_up_stocks if s['high_open_pct'] >= 9.8])

    print(f"    平均涨幅: {avg_pct:.2f}%")
    print(f"    平均成交额: {avg_amount/10000:.1f}万")
    print(f"    一字涨停数: {one_word_count}只 ({one_word_count/len(limit_up_stocks)*100:.1f}%)")

print(f"\n⚠️ 风险提示:")
print(f"  • 涨停板追入风险极高，需谨慎决策")
print(f"  • 建议优先观察封板强度和成交量配合")
print(f"  • 严格控制仓位: 单只≤15%, 总仓≤70%")
print(f"  • 设置止损线: -5%，避免大幅亏损")

# 保存报告
report_dir = script_dir / 'reports'
report_dir.mkdir(exist_ok=True)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
report_file = report_dir / f'latest_scan_{timestamp}.txt'

with open(report_file, 'w', encoding='utf-8') as f:
    f.write("="*90 + "\n")
    f.write("最新涨停选股扫描报告\n")
    f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"扫描耗时: {scan_time:.2f}秒\n")
    f.write("="*90 + "\n\n")

    f.write("一、统计概览\n")
    f.write("-"*40 + "\n")
    f.write(f"扫描股票数: {total}\n")
    f.write(f"有效数据: {len(results)}\n")
    f.write(f"涨停股票: {len(limit_up_stocks)}\n")
    f.write(f"强势股票: {len(strong_stocks)}\n\n")

    if limit_up_stocks:
        f.write("二、涨停股票详情\n")
        f.write("-"*40 + "\n")
        for s in limit_up_stocks:
            f.write(f"  {s['code']} 现价{s['price']:.2f} 涨幅{s['pct_change']:.2f}% "
                   f"高开{s['high_open_pct']:.2f}% 成交额{s['amount']/10000:.1f}万\n")
        f.write("\n")

    f.write("三、涨幅TOP20\n")
    f.write("-"*40 + "\n")
    for i, s in enumerate(results[:20], 1):
        f.write(f"  {i:2d}. {s['code']:12s} {s['price']:8.2f} {s['pct_change']:8.2f}%\n")

    f.write("\n" + "="*90 + "\n")
    f.write("报告结束\n")

print(f"\n📄 报告已保存: {report_file.name}")
print(f"   路径: {report_file.parent}")

# 关闭连接
print(f"\n🔌 关闭连接...")
try:
    tq.close()
    print("  ✅ 连接已关闭")
except Exception as e:
    print(f"  ⚠️ 关闭时异常: {e}")

print(f"\n{'='*90}")
print(f"  ✅ 全部任务完成!")
print(f"{'='*90}")

input("\n按回车键退出...")
