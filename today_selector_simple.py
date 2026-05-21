# -*- coding: utf-8 -*-
"""
今日涨停实时选股分析系统 (简化版)
直接获取市场快照数据进行分析
"""

import sys
import os
from datetime import datetime
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from tqcenter import tq


def main():
    """主函数"""
    start_time = datetime.now()

    print("\n" + "="*90)
    print("  🚀 今日涨停实时选股分析系统 (简化版)")
    print(f"  启动时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*90)

    # 初始化连接
    print("\n" + "="*90)
    print("  📡 连接通达信TQ接口...")
    print("="*90)

    try:
        tq.initialize(path=str(script_dir))
        print(f"\n✅ 连接成功! run_id: {tq.run_id}")
    except Exception as e:
        print(f"\n❌ 连接失败: {e}")
        return False

    # 获取股票列表
    print("\n" + "="*90)
    print("  📋 获取股票列表...")
    print("="*90)

    try:
        stock_list = tq.get_stock_list()

        if isinstance(stock_list, list):
            stock_list = [s for s in stock_list if s and '.' in str(s)]
        elif hasattr(stock_list, 'iterrows'):
            stock_list = [row['code'] for _, row in stock_list.iterrows()
                         if row.get('code') and '.' in str(row['code'])]
        else:
            stock_list = list(stock_list)

        print(f"✅ 获取到 {len(stock_list)} 只股票")

        # 限制数量以加快速度
        if len(stock_list) > 500:
            stock_list = stock_list[:500]
            print(f"⚠️ 演示模式: 扫描前{len(stock_list)}只")

    except Exception as e:
        print(f"❌ 获取失败: {e}")
        tq.close()
        return False

    # 获取实时行情并分析
    print("\n" + "="*90)
    print("  ⏱️ 扫描实时行情...")
    print("="*90)

    all_stocks = []
    limit_up_stocks = []
    near_limit_stocks = []
    strong_stocks = []

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

                        # 判断状态
                        is_limit_up = pct_change >= 9.8
                        is_near_limit = 8.0 <= pct_change < 9.8
                        is_strong = 3.0 <= pct_change < 8.0

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
                            'amount': amount * 10000,
                        }

                        all_stocks.append(stock_info)

                        if is_limit_up:
                            limit_up_stocks.append(stock_info)
                        elif is_near_limit:
                            near_limit_stocks.append(stock_info)
                        elif is_strong:
                            strong_stocks.append(stock_info)

                except (ValueError, TypeError):
                    pass

        except Exception:
            pass

        if i % 100 == 0 or i == total:
            print(f"   进度: {i}/{total} (有效:{len(all_stocks)} "
                  f"涨停:{len(limit_up_stocks)} 强势:{len(strong_stocks)})")

    # 排序
    all_stocks.sort(key=lambda x: x['pct_change'], reverse=True)

    print(f"\n✅ 扫描完成!")
    print(f"   有效数据: {len(all_stocks)} 只")
    print(f"   涨停股票: {len(limit_up_stocks)} 只")
    print(f"   接近涨停: {len(near_limit_stocks)} 只")
    print(f"   强势上涨: {len(strong_stocks)} 只")

    # 输出结果
    print("\n" + "="*90)
    print("  📊 今日选股结果")
    print("="*90)

    print(f"\n⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if limit_up_stocks:
        print(f"\n🔴 今日涨停 ({len(limit_up_stocks)}只):")
        print(f"   {'序号':<4} {'代码':<12} {'现价':>8} {'涨幅%':>8} {'高开%':>8} {'金额(万)':>10}")
        print(f"   " + "-"*56)

        for i, s in enumerate(sorted(limit_up_stocks, key=lambda x: x['amount'], reverse=True)[:10], 1):
            amount_wan = s['amount'] / 10000
            print(f"   {i:<4} {s['code']:<12} {s['price']:>8.2f} "
                  f"{s['pct_change']:>8.2f} {s['high_open_pct']:>8.2f} "
                  f"{amount_wan:>10.1f}")

    if strong_stocks:
        print(f"\n🟡 强势上涨 TOP10:")
        print(f"   {'排名':<4} {'代码':<12} {'现价':>8} {'涨幅%':>8} {'高开%':>8}")
        print(f"   " + "-"*48)

        for i, s in enumerate(strong_stocks[:10], 1):
            print(f"   {i:<4} {s['code']:<12} {s['price']:>8.2f} "
                  f"{s['pct_change']:>8.2f} {s['high_open_pct']:>8.2f}")

    # 综合TOP20
    print(f"\n⭐ 涨幅排行 TOP20:")
    print(f"   {'排名':<4} {'代码':<12} {'现价':>8} {'涨幅%':>8} {'状态':<8}")
    print(f"   " + "-"*46)

    for i, s in enumerate(all_stocks[:20], 1):
        status = "涨停" if s['pct_change'] >= 9.8 else \
                "近涨" if s['pct_change'] >= 8.0 else \
                "强势" if s['pct_change'] >= 3.0 else "其他"
        print(f"   {i:<4} {s['code']:<12} {s['price']:>8.2f} "
              f"{s['pct_change']:>8.2f} {status:<8}")

    # 操作建议
    print(f"\n💡 操作建议:")

    if limit_up_stocks:
        best = max(limit_up_stocks, key=lambda x: x['amount'])
        print(f"   最强涨停: {best['code']} "
              f"(涨幅{best['pct_change']:.2f}%, 成交额{best['amount']/10000:.1f}万)")

    print(f"\n⚠️ 风险提示:")
    print(f"   • 涨停板追入风险极大，需谨慎操作")
    print(f"   • 建议优先观察封板强度和成交量")
    print(f"   • 严格控制仓位，单只不超过15%")
    print(f"   • 设置止损线(-5%)，避免大幅亏损")

    # 保存报告
    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()

    report_dir = script_dir / 'reports'
    report_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = report_dir / f'today_limitup_{timestamp}.txt'

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("="*90 + "\n")
        f.write("今日涨停选股分析报告\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*90 + "\n\n")

        f.write(f"扫描股票数: {total}\n")
        f.write(f"有效数据: {len(all_stocks)}\n")
        f.write(f"涨停股票: {len(limit_up_stocks)}\n")
        f.write(f"强势股票: {len(strong_stocks)}\n\n")

        if limit_up_stocks:
            f.write("涨停股票详情:\n")
            for s in sorted(limit_up_stocks, key=lambda x: x['amount'], reverse=True):
                f.write(f"  {s['code']} 现价{s['price']:.2f} "
                       f"涨幅{s['pct_change']:.2f}% 高开{s['high_open_pct']:.2f}% "
                       f"成交额{s['amount']/10000:.1f}万\n")
            f.write("\n")

        f.write(f"耗时: {elapsed:.2f}秒\n")
        f.write("="*90 + "\n")

    print(f"\n" + "="*90)
    print(f"  ✅ 分析完成!")
    print(f"  总耗时: {elapsed:.2f} 秒")
    print(f"  报告已保存: {report_file.name}")
    print("="*90)

    # 关闭连接
    tq.close()

    return True


if __name__ == '__main__':
    success = main()

    if success:
        print("\n🎉 任务执行完毕!")

        input("\n按回车键退出...")
    else:
        print("\n❌ 任务执行失败")
