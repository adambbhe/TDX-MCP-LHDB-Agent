# -*- coding: utf-8 -*-
"""
全市场均线多头排列筛选策略 - 增强版
支持全市场扫描，带进度显示和性能优化
"""

import sys
import os
import time
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tqcenter import tq


class MABullishFullMarket:
    """全市场均线多头排列策略"""

    def __init__(self):
        self.params = {
            'ma_short': 5,
            'ma_mid': 10,
            'ma_long': 20,
            'min_rise_5d': 0,
            'max_rise_5d': 15,
            'min_volume_ratio': 0.8,
            'max_scan': 300,  # 最大扫描数量（控制运行时间）
        }

        self.results = []
        self.stats = {
            'total_scanned': 0,
            'passed_filter': 0,
            'failed_reasons': {},
            'start_time': None,
            'end_time': None,
        }

        self.lock = threading.Lock()

    def calculate_ma(self, close_prices, period):
        """计算移动平均线"""
        if len(close_prices) < period:
            return None
        return close_prices.rolling(window=period).mean().iloc[-1]

    def check_single_stock(self, stock_code):
        """检查单只股票的均线条件"""
        info = {
            'stock_code': stock_code,
            'name': '',
            'close': 0,
            'ma5': 0,
            'ma10': 0,
            'ma20': 0,
            'rise_5d': 0,
            'volume_ratio': 0,
            'reasons': [],
            'score': 0
        }

        try:
            kline = tq.get_market_data(
                stock_list=[stock_code],
                period='1d',
                count=25,
                dividend_type='none'
            )

            if not kline or stock_code not in kline:
                with self.lock:
                    self.stats['failed_reasons']['无法获取K线数据'] = \
                        self.stats['failed_reasons'].get('无法获取K线数据', 0) + 1
                return False, info

            df = kline[stock_code]

            if len(df) < 22:
                with self.lock:
                    key = f'K线不足({len(df)}天)'
                    self.stats['failed_reasons'][key] = \
                        self.stats['failed_reasons'].get(key, 0) + 1
                return False, info

            close_series = df['close']
            volume_series = df['volume']

            info['close'] = round(close_series.iloc[-1], 2)

            ma5 = self.calculate_ma(close_series, self.params['ma_short'])
            ma10 = self.calculate_ma(close_series, self.params['ma_mid'])
            ma20 = self.calculate_ma(close_series, self.params['ma_long'])

            if ma5 is None or ma10 is None or ma20 is None:
                with self.lock:
                    self.stats['failed_reasons']['均线计算失败'] = \
                        self.stats['failed_reasons'].get('均线计算失败', 0) + 1
                return False, info

            info['ma5'] = round(ma5, 2)
            info['ma10'] = round(ma10, 2)
            info['ma20'] = round(ma20, 2)

            score = 0

            condition1 = ma5 > ma10 > ma20
            if not condition1:
                with self.lock:
                    key = f'非多头排列(MA5<{ma5:.1f}<MA10)'
                    self.stats['failed_reasons'][key] = \
                        self.stats['failed_reasons'].get(key, 0) + 1
                return False, info
            score += 40

            condition2 = info['close'] > ma5
            if not condition2:
                with self.lock:
                    key = f'收盘价低于MA5'
                    self.stats['failed_reasons'][key] = \
                        self.stats['failed_reasons'].get(key, 0) + 1
                return False, info
            score += 25

            if len(close_series) >= 6:
                close_5d_ago = close_series.iloc[-6]
                rise_5d = (info['close'] / close_5d_ago - 1) * 100
                info['rise_5d'] = round(rise_5d, 2)

                if rise_5d > self.params['max_rise_5d']:
                    with self.lock:
                        key = f'涨幅过大:{rise_5d:.1f}%'
                        self.stats['failed_reasons'][key] = \
                            self.stats['failed_reasons'].get(key, 0) + 1
                    return False, info
                elif rise_5d >= self.params['min_rise_5d']:
                    score += 15

            avg_volume_5d = volume_series.iloc[-6:-1].mean()
            current_volume = volume_series.iloc[-1]
            if avg_volume_5d > 0:
                volume_ratio = current_volume / avg_volume_5d
                info['volume_ratio'] = round(volume_ratio, 2)
                if volume_ratio >= self.params['min_volume_ratio']:
                    score += 20

            info['score'] = score
            info['name'] = self._get_stock_name(stock_code)

            with self.lock:
                self.stats['passed_filter'] += 1

            return True, info

        except Exception as e:
            with self.lock:
                key = f'异常:{str(e)[:30]}'
                self.stats['failed_reasons'][key] = \
                    self.stats['failed_reasons'].get(key, 0) + 1
            return False, info

    def _get_stock_name(self, stock_code):
        """获取股票名称（带缓存）"""
        try:
            info = tq.get_stock_info(stock_code)
            return info.get('Name', '') if info else ''
        except:
            return ''

    def get_full_market_stocks(self):
        """获取全市场股票列表"""
        print("\n[步骤1] 获取全市场股票列表...")

        try:
            all_stocks = tq.get_stock_list()

            if isinstance(all_stocks, list) and len(all_stocks) > 0:
                stock_list = all_stocks

                print(f"  -> 全市场共 {len(stock_list)} 只股票")

                max_scan = self.params['max_scan']
                if len(stock_list) > max_scan:
                    stock_list = stock_list[:max_scan]
                    print(f"  -> 限制扫描前 {max_scan} 只 (控制运行时间)")

                return stock_list
            elif isinstance(all_stocks, dict) and 'code' in all_stocks:
                stock_list = all_stocks['code'].tolist()
                print(f"  -> 全市场共 {len(stock_list)} 只股票")
                return stock_list
            else:
                print(f"  -> [ERROR] 无法获取股票列表，返回类型: {type(all_stocks)}")
                return []

        except Exception as e:
            print(f"  -> [ERROR] 获取失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def run_full_scan(self):
        """执行全市场扫描"""

        print("=" * 90)
        print("  全市场均线多头排列筛选策略 (增强版)")
        print(f"  策略参数:")
        print(f"    - 均线组合: MA{self.params['ma_short']} > MA{self.params['ma_mid']} > MA{self.params['ma_long']}")
        print(f"    - 5日涨幅范围: {self.params['min_rise_5d']}% ~ {self.params['max_rise_5d']}%")
        print(f"    - 最小量比: {self.params['min_volume_ratio']}")
        print(f"    - 最大扫描数: {self.params['max_scan']}")
        print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 90)

        stock_list = self.get_full_market_stocks()

        if not stock_list:
            print("\n[ERROR] 无可扫描的股票，退出")
            return

        print(f"\n[步骤2] 开始全市场扫描 ({len(stock_list)}只股票)...")

        self.stats['start_time'] = time.time()
        passed_stocks = []

        for i, stock in enumerate(stock_list):
            with self.lock:
                self.stats['total_scanned'] += 1

            if (i + 1) % 50 == 0 or i == 0:
                elapsed = time.time() - self.stats['start_time']
                progress = (i + 1) / len(stock_list) * 100
                speed = (i + 1) / max(elapsed, 0.001)
                eta = (len(stock_list) - i - 1) / max(speed, 0.001)

                print(f"  进度: [{i+1}/{len(stock_list)}] ({progress:.1f}%) | "
                      f"速度: {speed:.1f}只/秒 | 预计剩余: {eta:.0f}秒", end='\r')

            is_pass, info = self.check_single_stock(stock)

            if is_pass:
                passed_stocks.append(info)

            time.sleep(0.02)  # 避免请求过快

        elapsed_total = time.time() - self.stats['start_time']
        self.stats['end_time'] = time.time()

        print(f"\n  进度: [{len(stock_list)}/{len(stock_list)}] (100.0%)")
        print(f"  总耗时: {elapsed_total:.1f}秒")

        self.results = passed_stocks
        self._print_comprehensive_results(passed_stocks)

    def _print_comprehensive_results(self, passed_stocks):
        """输出综合分析结果"""

        total = self.stats['total_scanned']
        passed = self.stats['passed_filter']
        pass_rate = passed / max(total, 1) * 100
        elapsed = self.stats['end_time'] - self.stats['start_time']

        print(f"\n{'='*90}")
        print(f"【全市场扫描结果统计】")
        print('='*90)

        print(f"\n  📊 基本信息:")
        print(f"     扫描总数: {total}")
        print(f"     通过数量: {passed}")
        print(f"     通过率: {pass_rate:.2f}%")
        print(f"     总耗时: {elapsed:.1f}秒")
        print(f"     平均速度: {total/max(elapsed,0.001):.1f}只/秒")

        if self.stats['failed_reasons']:
            print(f"\n  📉 主要淘汰原因 TOP 10:")
            sorted_reasons = sorted(
                self.stats['failed_reasons'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]

            for reason, count in sorted_reasons:
                pct = count / max(total, 1) * 100
                bar_len = int(pct / 2)
                bar = '█' * bar_len + '░' * (50 - bar_len)
                print(f"     {pct:5.1f}% |{bar}| {reason}: {count}次")

        if passed_stocks:
            print(f"\n{'='*90}")
            print(f"【🏆 通过均线多头排列筛选的股票】(按评分排序)")
            print('='*90)

            passed_sorted = sorted(passed_stocks, key=lambda x: x['score'], reverse=True)

            print(f"\n  {'排名':<4} {'代码':<12} {'名称':<8} {'收盘价':>8} "
                  f"{'MA5':>8} {'MA10':>8} {'MA20':>8} "
                  f"{'5日涨%':>7} {'量比':>6} {'评分':>5}")
            print('  ' + '-' * 95)

            for i, stock_info in enumerate(passed_sorted, 1):
                name = stock_info.get('name', '')[:6]
                print(f"  {i:<4} {stock_info['stock_code']:<12} {name:<8} "
                      f"{stock_info['close']:>8.2f} {stock_info['ma5']:>8.2f} "
                      f"{stock_info['ma10']:>8.2f} {stock_info['ma20']:>8.2f} "
                      f"{stock_info['rise_5d']:>7.1f} {stock_info['volume_ratio']:>6.2f} "
                      f"{stock_info['score']:>5}")

            print(f"\n  共 {len(passed_sorted)} 只股票通过筛选 (通过率: {pass_rate:.2f}%)")

            avg_score = sum(s['score'] for s in passed_stocks) / len(passed_stocks)
            max_score = max(s['score'] for s in passed_stocks)
            min_score = min(s['score'] for s in passed_stocks)

            print(f"\n  📈 评分分布:")
            print(f"     最高分: {max_score}")
            print(f"     最低分: {min_score}")
            print(f"     平均分: {avg_score:.1f}")

            high_score = [s for s in passed_stocks if s['score'] >= 80]
            mid_score = [s for s in passed_stocks if 60 <= s['score'] < 80]
            low_score = [s for s in passed_stocks if s['score'] < 60]

            print(f"     高分股(≥80): {len(high_score)}只 ({len(high_score)/max(len(passed_sorted),1)*100:.1f}%)")
            print(f"     中等分(60-79): {len(mid_score)}只 ({len(mid_score)/max(len(passed_sorted),1)*100:.1f}%)")
            print(f"     低分股(<60): {len(low_score)}只 ({len(low_score)/max(len(passed_sorted),1)*100:.1f}%)")

            top10 = passed_sorted[:10]
            if top10:
                print(f"\n  🌟 TOP 10 精选推荐:")
                print('  ' + '=' * 95)
                for i, s in enumerate(top10, 1):
                    name = s.get('name', '')
                    print(f"\n  {i}. {s['stock_code']} {name}")
                    print(f"     💰 价格信息: 收盘={s['close']:.2f}元")
                    print(f"     📊 均线状态: MA5={s['ma5']:.2f} > MA10={s['ma10']:.2f} > MA20={s['ma20']:.2f}")
                    print(f"     📈 涨幅情况: 近5日涨{s['rise_5d']:+.1f}%")
                    print(f"     📦 量能指标: 量比={s['volume_ratio']:.2f}")
                    print(f"     ⭐ 综合评分: {s['score']}/100")

                    if s['score'] >= 80:
                        print(f"     ✅ 强烈推荐 - 完美符合所有条件")
                    elif s['score'] >= 60:
                        print(f"     👍 可以关注 - 基本面良好")
                    else:
                        print(f"     ⚠️ 一般 - 部分条件未完全满足")

            self._generate_summary_report(passed_sorted)

        else:
            print(f"\n  ⚠️  没有股票通过均线多头排列筛选!")
            print(f"\n  可能原因:")
            print(f"     1. 当前市场整体处于调整或下跌趋势")
            print(f"     2. 大部分股票均线呈空头或纠缠状态")
            print(f"     3. 符合条件的强势股可能已经涨幅过大被过滤")
            print(f"\n  建议:")
            print(f"     • 放宽筛选条件 (如减少均线数量或提高涨幅上限)")
            print(f"     • 关注即将形成多头排列的股票 (MA5刚上穿MA10)")
            print(f"     • 等待市场企稳后再进行筛选")

        print(f"\n{'='*90}")

    def _generate_summary_report(self, passed_stocks):
        """生成汇总报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = Path(__file__).parent / f'ma_bullish_result_{timestamp}.txt'

        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(f"均线多头排列筛选结果报告\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"{'='*70}\n\n")

                f.write(f"【统计概览】\n")
                f.write(f"扫描总数: {self.stats['total_scanned']}\n")
                f.write(f"通过数量: {len(passed_stocks)}\n")
                f.write(f"通过率: {len(passed_stocks)/max(self.stats['total_scanned'],1)*100:.2f}%\n\n")

                f.write(f"【通过股票列表】\n")
                for i, s in enumerate(passed_stocks, 1):
                    name = s.get('name', '')
                    f.write(f"{i}. {s['stock_code']} {name}\n")
                    f.write(f"   收盘={s['close']}, MA5={s['ma5']}, MA10={s['ma10']}, MA20={s['ma20']}\n")
                    f.write(f"   5日涨幅={s['rise_5d']}%, 量比={s['volume_ratio']}, 评分={s['score']}\n\n")

            print(f"\n  📝 报告已保存至: {report_file.name}")

        except Exception as e:
            print(f"\n  ⚠️ 保存报告失败: {e}")


def main():
    """主函数"""
    strategy = MABullishFullMarket()

    try:
        print("\n[初始化] 连接TQ接口...")
        tq.initialize(path=os.path.abspath(__file__))
        print(f"  -> TQ连接成功! run_id={tq.run_id}")

        strategy.run_full_scan()

    except KeyboardInterrupt:
        print("\n\n[用户中断] 扫描已停止")
        if strategy.results:
            print(f"已完成 {strategy.stats['total_scanned']} 只股票的扫描")
            print(f"发现 {len(strategy.results)} 只符合条件的股票")
    except Exception as e:
        print(f"\n[ERROR] 策略运行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            tq.close()
            print("\n[TQ连接已关闭]")
        except:
            pass


if __name__ == '__main__':
    main()
