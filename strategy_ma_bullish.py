# -*- coding: utf-8 -*-
"""
均线多头排列筛选策略
策略逻辑:
1. MA5 > MA10 > MA20 (均线完全多头排列)
2. 收盘价在MA5上方 (强势特征)
3. 近5日涨幅适中 (避免追高)
4. 成交量配合放大
"""

import sys
import os
import time
from datetime import datetime
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tqcenter import tq


class MABullishAlignmentStrategy:
    """均线多头排列筛选策略"""

    def __init__(self):
        self.params = {
            'ma_short': 5,      # 短期均线周期
            'ma_mid': 10,       # 中期均线周期
            'ma_long': 20,      # 长期均线周期
            'min_rise_5d': 0,   # 最小5日涨幅(%)
            'max_rise_5d': 15,  # 最大5日涨幅(%)
            'min_volume_ratio': 0.8,  # 最小量比(相对5日均量)
        }

        self.results = []
        self.stats = {
            'total_scanned': 0,
            'passed_filter': 0,
            'failed_reasons': {}
        }

    def calculate_ma(self, close_prices, period):
        """计算移动平均线"""
        if len(close_prices) < period:
            return None
        return close_prices.rolling(window=period).mean().iloc[-1]

    def check_ma_alignment(self, stock_code):
        """
        检查均线多头排列条件

        返回:
        - (bool, dict): 是否通过, 详细信息字典
        """
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
                info['reasons'].append('无法获取K线数据')
                return False, info

            df = kline[stock_code]

            if len(df) < 22:
                info['reasons'].append(f'K线数据不足({len(df)}天)')
                return False, info

            close_series = df['close']
            volume_series = df['volume']

            info['close'] = close_series.iloc[-1]

            ma5 = self.calculate_ma(close_series, self.params['ma_short'])
            ma10 = self.calculate_ma(close_series, self.params['ma_mid'])
            ma20 = self.calculate_ma(close_series, self.params['ma_long'])

            if ma5 is None or ma10 is None or ma20 is None:
                info['reasons'].append('均线计算失败')
                return False, info

            info['ma5'] = round(ma5, 2)
            info['ma10'] = round(ma10, 2)
            info['ma20'] = round(ma20, 2)

            score = 0

            condition1 = ma5 > ma10 > ma20
            if condition1:
                score += 40
                info['reasons'].append(f'✓ 均线多头排列(MA5={ma5:.2f}>MA10={ma10:.2f}>MA20={ma20:.2f})')
            else:
                info['reasons'].append(f'✗ 非多头排列(MA5={ma5:.2f}, MA10={ma10:.2f}, MA20={ma20:.2f})')
                return False, info

            condition2 = info['close'] > ma5
            if condition2:
                score += 25
                info['reasons'].append(f'✓ 收盘价{info["close"]:.2f}在MA5上方')
            else:
                info['reasons'].append(f'✗ 收盘价{info["close"]:.2f}低于MA5={ma5:.2f}')
                return False, info

            if len(close_series) >= 6:
                close_5d_ago = close_series.iloc[-6]
                rise_5d = (info['close'] / close_5d_ago - 1) * 100
                info['rise_5d'] = round(rise_5d, 2)

                if self.params['min_rise_5d'] <= rise_5d <= self.params['max_rise_5d']:
                    score += 15
                    info['reasons'].append(f'✓ 5日涨幅{rise_5d:.1f}%合理')
                elif rise_5d > self.params['max_rise_5d']:
                    info['reasons'].append(f'✗ 5日涨幅过大:{rise_5d:.1f}%>{self.params["max_rise_5d"]}%')
                    return False, info

            avg_volume_5d = volume_series.iloc[-6:-1].mean()
            current_volume = volume_series.iloc[-1]
            if avg_volume_5d > 0:
                volume_ratio = current_volume / avg_volume_5d
                info['volume_ratio'] = round(volume_ratio, 2)

                if volume_ratio >= self.params['min_volume_ratio']:
                    score += 20
                    info['reasons'].append(f'✓ 量比{volume_ratio:.2f}正常')
                else:
                    info['reasons'].append(f'⚠ 量比偏低:{volume_ratio:.2f}')

            info['score'] = score
            return True, info

        except Exception as e:
            info['reasons'].append(f'异常:{str(e)[:50]}')
            return False, info

    def get_stock_name(self, stock_code):
        """获取股票名称"""
        try:
            info = tq.get_stock_info(stock_code)
            return info.get('Name', '') if info else ''
        except:
            return ''

    def run_strategy(self, stock_list=None, max_stocks=30):
        """
        运行策略

        参数:
        - stock_list: 股票代码列表(如果为None则获取全市场)
        - max_stocks: 最大测试数量(用于控制测试时间)
        """
        print("=" * 80)
        print("  均线多头排列筛选策略")
        print(f"  策略参数:")
        print(f"    - 均线组合: MA{self.params['ma_short']} > MA{self.params['ma_mid']} > MA{self.params['ma_long']}")
        print(f"    - 5日涨幅范围: {self.params['min_rise_5d']}% ~ {self.params['max_rise_5d']}%")
        print(f"    - 最小量比: {self.params['min_volume_ratio']}")
        print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        if stock_list is None:
            print("\n[步骤1] 获取股票列表...")
            try:
                all_stocks = tq.get_stock_list()
                if all_stocks and 'code' in all_stocks.columns:
                    stock_list = all_stocks['code'].tolist()[:max_stocks]
                    print(f"  -> 获取到 {len(stock_list)} 只股票(限制前{max_stocks}只)")
                else:
                    print("  -> [ERROR] 无法获取股票列表")
                    return
            except Exception as e:
                print(f"  -> [ERROR] 获取股票列表失败: {e}")
                return

        print(f"\n[步骤2] 开始筛选 ({len(stock_list)}只股票)...")

        passed_stocks = []

        for i, stock in enumerate(stock_list):
            self.stats['total_scanned'] += 1

            if (i + 1) % 10 == 0 or i == 0:
                print(f"  进度: [{i+1}/{len(stock_list)}] ({(i+1)/len(stock_list)*100:.1f}%)", end='\r')

            is_pass, info = self.check_ma_alignment(stock)

            if is_pass:
                info['name'] = self.get_stock_name(stock)
                passed_stocks.append(info)
                self.stats['passed_filter'] += 1
            else:
                for reason in info['reasons']:
                    if reason.startswith('✗'):
                        key = reason[:30]
                        self.stats['failed_reasons'][key] = self.stats['failed_reasons'].get(key, 0) + 1

            time.sleep(0.05)

        print(f"\n  进度: [{len(stock_list)}/{len(stock_list)}] (100.0%)")

        self.results = passed_stocks
        self._print_results(passed_stocks)

    def _print_results(self, passed_stocks):
        """输出筛选结果"""

        print(f"\n{'='*80}")
        print(f"【筛选结果统计】")
        print('='*80)

        total = self.stats['total_scanned']
        passed = self.stats['passed_filter']
        pass_rate = passed / max(total, 1) * 100

        print(f"\n  总扫描数: {total}")
        print(f"  通过数量: {passed}")
        print(f"  通过率: {pass_rate:.1f}%")

        if self.stats['failed_reasons']:
            print(f"\n  主要淘汰原因:")
            sorted_reasons = sorted(self.stats['failed_reasons'].items(), key=lambda x: x[1], reverse=True)[:5]
            for reason, count in sorted_reasons:
                pct = count / max(total, 1) * 100
                print(f"    - {reason}: {count}次 ({pct:.1f}%)")

        if passed_stocks:
            print(f"\n{'='*80}")
            print(f"【通过筛选的股票】(按评分排序)")
            print('='*80)

            passed_sorted = sorted(passed_stocks, key=lambda x: x['score'], reverse=True)

            print(f"\n{'序号':<4} {'代码':<12} {'名称':<10} {'收盘价':>8} {'MA5':>8} "
                  f"{'MA10':>8} {'MA20':>8} {'5日涨%':>7} {'量比':>6} {'评分':>5}")
            print('-' * 90)

            for i, stock_info in enumerate(passed_sorted, 1):
                name = stock_info.get('name', '')[:8]
                print(f"{i:<4} {stock_info['stock_code']:<12} {name:<10} "
                      f"{stock_info['close']:>8.2f} {stock_info['ma5']:>8.2f} "
                      f"{stock_info['ma10']:>8.2f} {stock_info['ma20']:>8.2f} "
                      f"{stock_info['rise_5d']:>7.1f} {stock_info['volume_ratio']:>6.2f} "
                      f"{stock_info['score']:>5}")

            print(f"\n  共 {len(passed_sorted)} 只股票通过均线多头排列筛选")

            avg_score = sum(s['score'] for s in passed_stocks) / len(passed_stocks)
            print(f"  平均评分: {avg_score:.1f}/100")

            top3 = passed_sorted[:3]
            if top3:
                print(f"\n  🏆 TOP 3 推荐:")
                for i, s in enumerate(top3, 1):
                    name = s.get('name', '')
                    print(f"    {i}. {s['stock_code']} {name}")
                    print(f"       收盘={s['close']:.2f}, MA5>{s['ma5']:.2f}>MA10>{s['ma10']:.2f}>MA20>{s['ma20']:.2f}")
                    print(f"       5日涨幅={s['rise_5d']:.1f}%, 量比={s['volume_ratio']:.2f}, 评分={s['score']}")
        else:
            print(f"\n  ⚠️  没有股票通过均线多头排列筛选")
            print(f"  建议:")
            print(f"    1. 当前市场可能处于调整期，均线未形成多头排列")
            print(f"    2. 可以适当放宽筛选条件(如减少均线数量或降低涨幅限制)")

        print(f"\n{'='*80}")


def main():
    """主函数"""
    strategy = MABullishAlignmentStrategy()

    test_stocks = [
        '600519.SH', '000001.SZ', '300750.SZ',
        '000002.SZ', '601318.SH', '600036.SH',
        '000858.SZ', '002594.SZ', '601012.SH',
        '300059.SZ', '600276.SH', '000333.SZ',
        '600900.SH', '601888.SH', '002475.SZ'
    ]

    try:
        tq.initialize(path=os.path.abspath(__file__))
        print(f"TQ连接成功! run_id={tq.run_id}\n")

        strategy.run_strategy(
            stock_list=test_stocks,
            max_stocks=len(test_stocks)
        )

    except Exception as e:
        print(f"\n[ERROR] 策略运行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            tq.close()
        except:
            pass


if __name__ == '__main__':
    main()
