# -*- coding: utf-8 -*-
"""
今日涨停实时选股分析系统
功能:
1. 连接通达信TQ接口获取实时行情
2. 全市场扫描筛选高开/涨停股票
3. 多维度评分排序
4. 生成详细选股报告
5. 可视化展示结果

使用方法:
    python today_limitup_selector.py
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    import numpy as np
    import pandas as pd
except ImportError:
    print("请先安装依赖: pip install numpy pandas")
    sys.exit(1)

script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

try:
    from tqcenter import tq as TQCenter
except ImportError as e:
    print(f"错误: 无法导入TQCenter - {e}")
    print("请确保tqcenter.py文件存在")
    sys.exit(1)


class TodayLimitUpSelector:
    """今日涨停选股器"""

    def __init__(self):
        self.tq = None
        self.connected = False

        import tqcenter
        self.tq = tqcenter.tq

        self.params = {
            'min_high_open': 0.01,      # 最小高开比例 1%
            'max_high_open': 0.07,      # 最大高开比例 7%
            'near_limit': 0.08,         # 接近阈值 8%
            'limit_up_threshold': 0.099, # 涨停阈值 9.9%
            'strong_rise': 0.03,        # 强势上涨 3%
            'volume_ratio_min': 0.8,    # 最小量比
            'score_threshold': 60,      # 评分门槛
            'max_results': 20,          # 最大显示数量
        }

        self.stocks_data = []
        self.limit_up_stocks = []
        self.near_limit_stocks = []
        self.high_open_stocks = []
        self.scored_stocks = []

    def connect_tq(self):
        """连接通达信"""
        print("\n" + "="*90)
        print("  📡 正在连接通达信TQ接口...")
        print("="*90)

        try:
            # 先尝试关闭旧连接
            try:
                self.tq.close()
            except:
                pass

            import time
            time.sleep(1)

            self.tq.initialize(path=str(script_dir))

            print(f"\n✅ 通达信连接成功!")
            print(f"   run_id: {self.tq.run_id}")
            self.connected = True
            return True

        except Exception as e:
            print(f"\n❌ 连接异常: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_all_stocks(self):
        """获取全市场股票列表"""
        print("\n" + "="*90)
        print("  📋 获取全市场股票列表...")
        print("="*90)

        try:
            stocks = self.tq.get_stock_list()

            if not stocks:
                print("⚠️  未获取到股票列表")
                return []

            if isinstance(stocks, list):
                stock_list = [s for s in stocks if s and '.' in str(s)]
            elif hasattr(stocks, 'iterrows'):
                stock_list = [row['code'] for _, row in stocks.iterrows()
                             if row.get('code') and '.' in str(row['code'])]
            else:
                stock_list = list(stocks)

            print(f"\n✅ 成功获取 {len(stock_list)} 只股票")

            # 为了演示，先扫描前500只（实际使用时可以去掉这个限制）
            if len(stock_list) > 500:
                print(f"\n⚠️  演示模式: 仅扫描前500只股票")
                stock_list = stock_list[:500]

            return stock_list

        except Exception as e:
            print(f"❌ 获取股票列表失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_realtime_quotes(self, stock_list):
        """获取实时行情"""
        print("\n" + "="*90)
        print("  ⏱️  获取实时行情数据...")
        print("="*90)

        all_quotes = []
        total = len(stock_list)

        for i, stock_code in enumerate(stock_list, 1):
            try:
                data = self.tq.get_market_snapshot(stock_code)

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
                            quote = {
                                'code': stock_code,
                                'name': '',
                                'price': now_price,
                                'open': open_price,
                                'high': high_price,
                                'low': low_price,
                                'preclose': last_close,
                                'volume': volume,
                                'amount': amount * 10000,  # 转换为元
                            }
                            all_quotes.append(quote)
                    except (ValueError, TypeError) as e:
                        pass

            except Exception as e:
                pass

            if i % 100 == 0 or i == total:
                print(f"   进度: {i}/{total} ({len(all_quotes)} 只有效数据)")

        print(f"\n✅ 成功获取 {len(all_quotes)} 只股票的实时行情")
        return all_quotes

    def analyze_stocks(self, quotes):
        """分析股票数据"""
        print("\n" + "="*90)
        print("  🔍 分析股票数据...")
        print("="*90)

        analyzed = []

        for quote in quotes:
            try:
                code = quote.get('code', '')
                name = quote.get('name', '')
                price = quote.get('price', 0)
                open_price = quote.get('open', 0)
                high = quote.get('high', 0)
                low = quote.get('low', 0)
                preclose = quote.get('preclose', 0)
                volume = quote.get('volume', 0)
                amount = quote.get('amount', 0)

                if not code or preclose <= 0 or price <= 0:
                    continue

                pct_change = (price - preclose) / preclose * 100
                high_open_pct = (open_price - preclose) / preclose * 100 if open_price > 0 else 0

                limit_up_price = round(preclose * 1.1, 2) if 'SZ' in code or 'SH' in code else round(preclose * 1.2, 2)

                is_limit_up = abs(price - limit_up_price) < 0.02 and pct_change >= 9.8
                is_near_limit = pct_change >= self.params['near_limit'] * 100 and not is_limit_up
                is_strong = pct_change >= self.params['strong_rise'] * 100
                is_high_open = high_open_pct >= self.params['min_high_open'] * 100

                score = self._calculate_score({
                    'code': code,
                    'name': name,
                    'price': price,
                    'open_price': open_price,
                    'high': high,
                    'low': low,
                    'preclose': preclose,
                    'pct_change': pct_change,
                    'high_open_pct': high_open_pct,
                    'limit_up_price': limit_up_price,
                    'is_limit_up': is_limit_up,
                    'is_near_limit': is_near_limit,
                    'is_strong': is_strong,
                    'is_high_open': is_high_open,
                    'volume': volume,
                    'amount': amount,
                })

                analyzed.append({
                    'code': code,
                    'name': name,
                    'price': price,
                    'open_price': open_price,
                    'high': high,
                    'low': low,
                    'preclose': preclose,
                    'volume': volume,
                    'amount': amount,
                    'pct_change': pct_change,
                    'high_open_pct': high_open_pct,
                    'limit_up_price': limit_up_price,
                    'is_limit_up': is_limit_up,
                    'is_near_limit': is_near_limit,
                    'is_strong': is_strong,
                    'is_high_open': is_high_open,
                    'score': score,
                })

            except Exception as e:
                continue

        analyzed.sort(key=lambda x: x['score'], reverse=True)

        self.limit_up_stocks = [s for s in analyzed if s['is_limit_up']]
        self.near_limit_stocks = [s for s in analyzed if s['is_near_limit']]
        self.high_open_stocks = [s for s in analyzed if s['is_high_open']]
        self.scored_stocks = analyzed[:self.params['max_results']]

        print(f"\n📊 分析完成:")
        print(f"   涨停股票: {len(self.limit_up_stocks)} 只")
        print(f"   接近涨停: {len(self.near_limit_stocks)} 只")
        print(f"   强势上涨: {len([s for s in analyzed if s['is_strong']])} 只")
        print(f"   高开股票: {len(self.high_open_stocks)} 只")
        print(f"   总计分析: {len(analyzed)} 只")

        return analyzed

    def _calculate_score(self, stock):
        """计算综合评分"""
        score = 0

        pct_change = stock['pct_change']

        if stock['is_limit_up']:
            score += 40
        elif stock['is_near_limit']:
            score += 30
        elif stock['is_strong']:
            score += 15
        elif stock['is_high_open']:
            score += 5

        high_open_pct = stock['high_open_pct']
        if high_open_pct >= 5:
            score += 10
        elif high_open_pct >= 3:
            score += 7
        elif high_open_pct >= 1:
            score += 5

        if stock['price'] > stock['preclose'] * 1.05:
            score += 5
        elif stock['price'] > stock['preclose']:
            score += 3

        volume = stock.get('volume', 0)
        if volume > 0:
            score += min(10, int(volume / 10000))

        amount = stock.get('amount', 0)
        if amount > 100000000:
            score += 10
        elif amount > 50000000:
            score += 7
        elif amount > 10000000:
            score += 5

        if stock['high'] > stock['low'] * 1.03:
            score += 3

        return min(score, 100)

    def generate_report(self):
        """生成详细报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_dir = script_dir / 'reports'
        report_dir.mkdir(exist_ok=True)
        report_file = report_dir / f'today_limitup_{timestamp}.txt'

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 90 + "\n")
            f.write("  今日涨停选股分析报告\n")
            f.write(f"  生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 90 + "\n\n")

            f.write("-" * 90 + "\n")
            f.write("一、市场概况\n")
            f.write("-" * 90 + "\n")
            f.write(f"  分析股票总数: {len(self.scored_stocks)}\n")
            f.write(f"  涨停股票数量: {len(self.limit_up_stocks)}\n")
            f.write(f"  接近涨停数量: {len(self.near_limit_stocks)}\n")
            f.write(f"  高开股票数量: {len(self.high_open_stocks)}\n\n")

            if self.limit_up_stocks:
                f.write("-" * 90 + "\n")
                f.write("二、涨停股票详情\n")
                f.write("-" * 90 + "\n")
                f.write(f"{'序号':<4} {'代码':<12} {'名称':<10} {'现价':>8} "
                       f"{'涨幅%':>8} {'高开%':>8} {'金额(万)':>10} {'评分':>6}\n")
                f.write("-" * 90 + "\n")

                for i, stock in enumerate(self.limit_up_stocks[:20], 1):
                    amount_wan = stock['amount'] / 10000 if stock['amount'] else 0
                    f.write(f"{i:<4} {stock['code']:<12} {stock['name']:<10} "
                           f"{stock['price']:>8.2f} {stock['pct_change']:>8.2f} "
                           f"{stock['high_open_pct']:>8.2f} {amount_wan:>10.1f} "
                           f"{stock['score']:>6}\n")
                f.write("\n")

            if self.near_limit_stocks:
                f.write("-" * 90 + "\n")
                f.write("三、接近涨停股票 (关注)\n")
                f.write("-" * 90 + "\n")
                f.write(f"{'序号':<4} {'代码':<12} {'名称':<10} {'现价':>8} "
                       f"{'涨幅%':>8} {'高开%':>8} {'金额(万)':>10} {'评分':>6}\n")
                f.write("-" * 90 + "\n")

                for i, stock in enumerate(self.near_limit_stocks[:15], 1):
                    amount_wan = stock['amount'] / 10000 if stock['amount'] else 0
                    f.write(f"{i:<4} {stock['code']:<12} {stock['name']:<10} "
                           f"{stock['price']:>8.2f} {stock['pct_change']:>8.2f} "
                           f"{stock['high_open_pct']:>8.2f} {amount_wan:>10.1f} "
                           f"{stock['score']:>6}\n")
                f.write("\n")

            if self.scored_stocks:
                f.write("-" * 90 + "\n")
                f.write("四、综合评分 TOP20\n")
                f.write("-" * 90 + "\n")
                f.write(f"{'排名':<4} {'代码':<12} {'名称':<10} {'现价':>8} "
                       f"{'涨幅%':>8} {'高开%':>8} {'状态':<8} {'评分':>6}\n")
                f.write("-" * 90 + "\n")

                for i, stock in enumerate(self.scored_stocks[:20], 1):
                    status = "涨停" if stock['is_limit_up'] else \
                            "近涨" if stock['is_near_limit'] else \
                            "强势" if stock['is_strong'] else \
                            "高开" if stock['is_high_open'] else "普通"
                    f.write(f"{i:<4} {stock['code']:<12} {stock['name']:<10} "
                           f"{stock['price']:>8.2f} {stock['pct_change']:>8.2f} "
                           f"{stock['high_open_pct']:>8.2f} {status:<8} "
                           f"{stock['score']:>6}\n")
                f.write("\n")

            f.write("-" * 90 + "\n")
            f.write("五、操作建议\n")
            f.write("-" * 90 + "\n")

            if self.limit_up_stocks:
                top3 = self.limit_up_stocks[:3]
                f.write("  【重点关注】已涨停股票:\n")
                for s in top3:
                    f.write(f"    ★ {s['code']} {s['name']} - "
                           f"涨幅{s['pct_change']:.2f}% - 评分{s['score']}\n")
                f.write("\n")

            if self.near_limit_stocks:
                near_top3 = self.near_limit_stocks[:3]
                f.write("  【密切关注】接近涨停:\n")
                for s in near_top3:
                    f.write(f"    ◆ {s['code']} {s['name']} - "
                           f"涨幅{s['pct_change']:.2f}% - 可能即将涨停\n")
                f.write("\n")

            f.write("  【风险提示】:\n")
            f.write("    • 涨停股票风险较高，注意封板强度\n")
            f.write("    • 关注成交量变化和资金流向\n")
            f.write("    • 严格执行止损策略\n")
            f.write("    • 不要盲目追高，控制仓位\n\n")

            f.write("=" * 90 + "\n")
            f.write("  报告结束\n")
            f.write("=" * 90 + "\n")

        print(f"\n📄 报告已保存: {report_file.name}")

        return report_file

    def print_summary(self):
        """打印摘要"""
        print("\n" + "="*90)
        print("  📊 今日选股结果摘要")
        print("="*90)

        print(f"\n⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        print(f"\n🎯 核心统计:")
        print(f"   涨停: {len(self.limit_up_stocks)} 只 | "
              f"近涨: {len(self.near_limit_stocks)} 只 | "
              f"高开: {len(self.high_open_stocks)} 只")

        if self.limit_up_stocks:
            print(f"\n🔴 今日涨停 TOP5:")
            print(f"   {'序号':<4} {'代码':<12} {'名称':<10} {'涨幅%':>8} {'金额(万)':>10}")
            print(f"   " + "-"*50)
            for i, s in enumerate(self.limit_up_stocks[:5], 1):
                amount = s.get('amount', 0) / 10000
                print(f"   {i:<4} {s['code']:<12} {s['name']:<10} "
                      f"{s['pct_change']:>8.2f} {amount:>10.1f}")

        if self.near_limit_stocks:
            print(f"\n🟡 接近涨停 TOP5:")
            print(f"   {'序号':<4} {'代码':<12} {'名称':<10} {'涨幅%':>8} {'评分':>6}")
            print(f"   " + "-"*46)
            for i, s in enumerate(self.near_limit_stocks[:5], 1):
                print(f"   {i:<4} {s['code']:<12} {s['name']:<10} "
                      f"{s['pct_change']:>8.2f} {s['score']:>6}")

        if self.scored_stocks:
            print(f"\n⭐ 综合评分 TOP10:")
            print(f"   {'排名':<4} {'代码':<12} {'名称':<10} {'涨幅%':>8} {'状态':<8} {'评分':>6}")
            print(f"   " + "-"*54)
            for i, s in enumerate(self.scored_stocks[:10], 1):
                status = "涨停" if s['is_limit_up'] else "近涨" if s['is_near_limit'] else "其他"
                print(f"   {i:<4} {s['code']:<12} {s['name']:<10} "
                      f"{s['pct_change']:>8.2f} {status:<8} {s['score']:>6}")

        print(f"\n💡 操作建议:")
        if self.limit_up_stocks:
            best = self.limit_up_stocks[0]
            print(f"   最强涨停: {best['code']} {best['name']} "
                  f"(涨幅{best['pct_change']:.2f}%)")
        if self.near_limit_stocks:
            watch = self.near_limit_stocks[0]
            print(f"   密切关注: {watch['code']} {watch['name']} "
                  f"(涨幅{watch['pct_change']:.2f}%,可能涨停)")

        print(f"\n⚠️ 风险提醒:")
        print(f"   • 涨停板追入风险极大，需谨慎操作")
        print(f"   • 建议优先观察，等待回封或二波机会")
        print(f"   • 严格控制仓位，单只不超过15%")
        print(f"   • 设置好止损线(-5%),避免大幅亏损")

    def run(self):
        """主运行流程"""
        start_time = datetime.now()

        print("\n" + "="*90)
        print("  🚀 今日涨停实时选股分析系统启动")
        print(f"  启动时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*90)

        if not self.connect_tq():
            return False

        stock_list = self.get_all_stocks()
        if not stock_list:
            print("❌ 无法获取股票列表")
            return False

        quotes = self.get_realtime_quotes(stock_list)
        if not quotes:
            print("❌ 无法获取行情数据")
            return False

        self.analyze_stocks(quotes)

        self.print_summary()

        report_file = self.generate_report()

        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        print(f"\n" + "="*90)
        print(f"  ✅ 选股分析完成!")
        print(f"  总耗时: {elapsed:.2f} 秒")
        print(f"  报告文件: {report_file.name}")
        print("="*90)

        return True


def main():
    """主函数"""
    selector = TodayLimitUpSelector()
    success = selector.run()

    if success:
        print("\n🎉 今日选股任务执行完毕!")

        input("\n按回车键退出...")
    else:
        print("\n❌ 选股任务执行失败")
        print("   请检查:")
        print("   1. 通达信软件是否已打开并登录?")
        print("   2. TQ接口是否正常工作?")
        print("   3. 网络连接是否正常?")


if __name__ == '__main__':
    main()
