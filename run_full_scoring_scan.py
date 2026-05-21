# -*- coding: utf-8 -*-
"""
全市场评分扫描演示脚本
功能:
1. 扫描全市场股票
2. 使用统一评分系统进行评分
3. 展示评分结果和分布
4. 输出TOP股票清单
"""

import sys
import os
import time
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tqcenter import tq
from scoring_system import UnifiedScoringSystem, SignalType, StockSignal


def run_full_market_scoring_demo():
    """全市场评分扫描演示"""
    start_time = datetime.now()

    print("=" * 90)
    print("  🚀 全市场股票评分扫描 (使用统一评分系统)")
    print(f"  ⏰ 扫描开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 90)

    # 初始化TQ连接
    print("\n[步骤1] 初始化TQ接口...")
    try:
        tq.initialize(path=os.path.abspath(__file__))
        print(f"  ✅ TQ连接成功! run_id={tq.run_id}")
    except Exception as e:
        print(f"  ❌ TQ连接失败: {e}")
        return

    # 初始化统一评分系统
    print("\n[步骤2] 初始化统一评分系统...")
    scoring = UnifiedScoringSystem()
    print(f"  ✅ 评分系统就绪!")
    print(f"     权重配置:")
    for key, value in scoring.weights.items():
        print(f"       - {key}: {value}%")

    # 获取股票列表
    print("\n[步骤3] 获取全市场股票列表...")
    try:
        all_stocks = tq.get_stock_list()
        scan_count = min(500, len(all_stocks))  # 限制扫描数量以加快速度
        stock_list = all_stocks[:scan_count]
        print(f"  ✅ 获取成功!")
        print(f"     - 全市场总数: {len(all_stocks)} 只")
        print(f"     - 本次扫描: {scan_count} 只")
    except Exception as e:
        print(f"  ❌ 获取失败: {e}")
        tq.close()
        return

    # 开始扫描和评分
    print(f"\n{'='*90}")
    print(f"[步骤4] 开始扫描评分...")
    print('='*90)

    scored_stocks = []
    error_count = 0
    signal_type_stats = {}

    for i, stock_code in enumerate(stock_list):
        # 显示进度
        if (i + 1) % 50 == 0 or i == 0:
            elapsed = time.time() - start_time.timestamp()
            speed = (i + 1) / max(elapsed, 1)
            print(f"  📊 进度: [{i+1}/{scan_count}] ({speed:.1f}只/秒)", end='\r')

        try:
            # 获取实时快照
            snapshot = tq.get_market_snapshot(stock_code)
            if not snapshot or 'LastClose' not in snapshot:
                continue

            last_close = float(snapshot['LastClose'])
            now_price = float(snapshot['Now'])

            if last_close <= 0 or now_price <= 0:
                continue

            # 计算涨幅
            rise_pct = (now_price / last_close - 1) * 100
            open_price = float(snapshot.get('Open', now_price))
            high_open_ratio = (open_price / last_close - 1) * 100

            # 获取股票信息
            info = tq.get_stock_info(stock_code)
            name = info.get('Name', '') if info else stock_code

            # 确定信号类型
            signal_type = SignalType.NO_SIGNAL
            if rise_pct >= 9.9:
                signal_type = SignalType.LIMIT_UP
            elif rise_pct >= 8.0:
                signal_type = SignalType.NEAR_LIMIT_UP
            elif high_open_ratio >= 2.0:
                signal_type = SignalType.AUCTION_HIGH_OPEN
            elif rise_pct >= 3.0:
                signal_type = SignalType.RAPID_RISE
            elif rise_pct >= 1.5:
                signal_type = SignalType.STRONG_BREAKOUT

            # 如果没有有效信号，跳过（可选：可以保留所有股票）
            if signal_type == SignalType.NO_SIGNAL and rise_pct < 0:
                continue

            # 创建信号对象
            volume = float(snapshot.get('Volume', 0))
            amount = float(snapshot.get('Amount', 0))

            signal = StockSignal(
                code=stock_code,
                name=name,
                signal_type=signal_type,
                current_price=now_price,
                last_close=last_close,
                volume=volume,
                amount=amount,
                high_open_ratio=round(high_open_ratio, 2)
            )

            # 使用统一评分系统计算评分
            score = scoring.calculate_score(signal)

            # 统计信号类型
            signal_type_name = signal_type.value
            signal_type_stats[signal_type_name] = signal_type_stats.get(signal_type_name, 0) + 1

            # 保存评分结果
            scored_stocks.append({
                'code': stock_code,
                'name': name,
                'price': now_price,
                'rise_pct': round(rise_pct, 2),
                'high_open_ratio': round(high_open_ratio, 2),
                'score': score,
                'signal_type': signal_type_name,
                'amount': amount,
                'details': signal.details.get('评分明细', {})
            })

        except Exception as e:
            error_count += 1
            if error_count <= 3:  # 只显示前3个错误
                pass  # 静默处理错误以保持输出整洁

        # 控制请求频率
        time.sleep(0.01)

    print(f"\n\n  ✅ 扫描完成!")

    # 按评分排序
    scored_stocks.sort(key=lambda x: x['score'], reverse=True)

    # 输出统计信息
    print(f"\n{'='*90}")
    print(f"【📊 扫描结果统计】")
    print('='*90)
    elapsed = (datetime.now() - start_time).total_seconds()

    print(f"\n  ⏱️  总耗时: {elapsed:.1f}秒")
    print(f"  📈 扫描总数: {scan_count} 只")
    print(f"  ✅ 成功评分: {len(scored_stocks)} 只 ({len(scored_stocks)/scan_count*100:.1f}%)")
    print(f"  ❌ 错误/跳过: {error_count} 只")

    if scored_stocks:
        scores = [s['score'] for s in scored_stocks]
        print(f"\n  📊 评分分布:")
        print(f"     - 最高分: {max(scores):.1f}")
        print(f"     - 最低分: {min(scores):.1f}")
        print(f"     - 平均分: {sum(scores)/len(scores):.1f}")

        # 评分区间分布
        ranges = {
            '80-100分 (优秀)': 0,
            '60-79分 (良好)': 0,
            '40-59分 (一般)': 0,
            '20-39分 (较弱)': 0,
            '0-19分 (弱)': 0
        }
        for s in scored_stocks:
            if s['score'] >= 80:
                ranges['80-100分 (优秀)'] += 1
            elif s['score'] >= 60:
                ranges['60-79分 (良好)'] += 1
            elif s['score'] >= 40:
                ranges['40-59分 (一般)'] += 1
            elif s['score'] >= 20:
                ranges['20-39分 (较弱)'] += 1
            else:
                ranges['0-19分 (弱)'] += 1

        print(f"\n  📊 评分区间分布:")
        for range_name, count in sorted(ranges.items(), key=lambda x: -x[1]):
            pct = count / len(scored_stocks) * 100
            bar = '█' * int(pct / 2)
            print(f"     {range_name:<18}: {count:>4} 只 ({pct:>5.1f}%) {bar}")

    # 信号类型分布
    if signal_type_stats:
        print(f"\n  📊 信号类型分布:")
        for stype, count in sorted(signal_type_stats.items(), key=lambda x: -x[1]):
            pct = count / max(len(scored_stocks), 1) * 100
            bar = '█' * int(pct / 2)
            print(f"     {stype:<12}: {count:>4} 只 ({pct:>5.1f}%) {bar}")

    # 显示TOP股票
    top_count = min(20, len(scored_stocks))
    if top_count > 0:
        print(f"\n{'='*90}")
        print(f"【🏆 TOP {top_count} 高评分股票】(按评分排序)")
        print('='*90)

        print(f"\n  {'排名':<4} {'代码':<12} {'名称':<8} {'信号类型':<10} "
              f"{'现价':>7} {'涨幅%':>7} {'高开%':>6} {'评分':>5} {'成交额(万)':>10}")
        print('  ' + '-' * 95)

        for i, stock in enumerate(scored_stocks[:top_count], 1):
            name = stock['name'][:6]
            amount_wan = stock['amount'] / 10000
            print(f"  {i:<4} {stock['code']:<12} {name:<8} {stock['signal_type']:<10} "
                  f"{stock['price']:>7.2f} {stock['rise_pct']:>+7.2f}% {stock['high_open_ratio']:>+6.2f}% "
                  f"{stock['score']:>5.1f} {amount_wan:>10.0f}")

        # 显示前3名的详细评分明细
        print(f"\n{'='*90}")
        print(f"【🌟 TOP 3 详细评分分析】")
        print('='*90)

        for i, stock in enumerate(scored_stocks[:3], 1):
            print(f"\n  【第{i}名】{stock['code']} {stock['name']}")
            print(f"      💰 价格: {stock['price']:.2f}元 | 涨幅: {stock['rise_pct']:+.2f}%")
            print(f"      📊 信号类型: {stock['signal_type']}")
            print(f"      ⭐ 综合评分: {stock['score']:.1f}/100")

            if stock['details']:
                print(f"      📋 评分明细:")
                for dim, value in stock['details'].items():
                    if dim != '总分':
                        print(f"         • {dim}: {value}")

    # 保存结果到文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    result_file = os.path.join(os.path.dirname(__file__), f'scoring_results_{timestamp}.txt')

    try:
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write("=" * 90 + "\n")
            f.write(f"全市场评分扫描结果\n")
            f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"扫描数量: {scan_count} | 有效评分: {len(scored_stocks)}\n")
            f.write("=" * 90 + "\n\n")

            for i, stock in enumerate(scored_stocks[:50], 1):
                f.write(f"{i}. {stock['code']} {stock['name']}\n")
                f.write(f"   价格: {stock['price']:.2f} | 涨幅: {stock['rise_pct']:+.2f}%\n")
                f.write(f"   信号: {stock['signal_type']} | 评分: {stock['score']:.1f}\n")
                if stock['details']:
                    f.write(f"   明细: {stock['details']}\n")
                f.write("\n")

        print(f"\n💾 结果已保存至: {result_file}")

    except Exception as e:
        print(f"\n⚠️ 保存失败: {e}")

    # 关闭TQ连接
    try:
        tq.close()
        print(f"\n✅ TQ连接已关闭")
    except:
        pass

    print(f"\n{'='*90}")
    print(f"  🎉 全市场评分扫描完成!")
    print(f"  ⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print('='*90)


if __name__ == '__main__':
    try:
        run_full_market_scoring_demo()
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断扫描")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
