# -*- coding: utf-8 -*-
"""
量化打板选股策略系统 - 优化版 (全市场扫描)
改进:
1. 优化参数适配当前市场
2. 增加多种选股模式
3. 全市场扫描能力
4. 更详细的报告输出
"""

import sys
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tqcenter import tq
from scoring_system import UnifiedScoringSystem


class SignalType(Enum):
    """信号类型"""
    NO_SIGNAL = "无信号"
    STRONG_RISE = "强势上涨"
    HIGH_OPEN = "竞价高开"
    VOLUME_SURGE = "放量突破"
    MA_BULLISH = "均线多头"
    NEAR_HIGH = "接近新高"
    LIMIT_UP = "涨停"


@dataclass
class StockSignal:
    """股票信号"""
    code: str
    name: str
    signal_type: SignalType
    current_price: float
    last_close: float
    open_price: float = 0
    high_price: float = 0
    low_price: float = 0
    volume: float = 0
    amount: float = 0
    rise_pct: float = 0
    high_open_ratio: float = 0
    turnover_rate: float = 0
    ma5: float = 0
    ma10: float = 0
    ma20: float = 0
    score: float = 0
    details: Dict = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class EnhancedLimitUpStrategy:
    """增强版量化打板策略"""

    def __init__(self):
        self.params = {
            # 竞价参数
            'min_high_open': 1.0,
            'max_high_open': 7.0,
            'min_auction_amount': 10000000,

            # 涨幅参数
            'strong_rise_min': 3.0,
            'near_limit_up': 8.0,

            # 成交量参数
            'volume_surge_ratio': 1.5,

            # 均线参数
            'ma_bullish_score_threshold': 70,

            # 风控参数
            'min_score': 60,
            'max_stocks_scan': 200,
            'max_results': 15,
        }

        self.signals = []
        self.results = []
        self.scoring_system = UnifiedScoringSystem()

    def run_full_market_scan(self):
        """全市场扫描"""
        start_time = datetime.now()

        print("=" * 95)
        print("  🚀 量化打板选股策略 - 全市场扫描 (优化版)")
        print(f"  时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 95)

        print("\n[步骤1] 获取股票列表...")
        try:
            all_stocks = tq.get_stock_list()
            if isinstance(all_stocks, list) and len(all_stocks) > 0:
                stock_list = all_stocks[:self.params['max_stocks_scan']]
                print(f"  → 获取 {len(stock_list)} 只股票")
            else:
                print(f"  → [ERROR] 获取失败")
                return
        except Exception as e:
            print(f"  → [ERROR] {e}")
            return

        print(f"\n{'='*95}")
        print(f"[步骤2] 多维度筛选 (目标: {len(stock_list)}只)")
        print('='*95)

        candidates = []

        for i, stock in enumerate(stock_list):
            if (i + 1) % 50 == 0:
                elapsed = time.time() - start_time.timestamp()
                speed = (i + 1) / max(elapsed, 1)
                print(f"  进度: [{i+1}/{len(stock_list)}] ({speed:.1f}只/秒)", end='\r')

            signal = self._analyze_stock(stock)
            if signal and signal.score >= self.params['min_score']:
                candidates.append(signal)

            time.sleep(0.01)

        candidates.sort(key=lambda x: x.score, reverse=True)

        print(f"\n\n  ✅ 筛选完成!")
        print(f"  → 扫描总数: {len(stock_list)} 只")
        print(f"  → 通过数量: {len(candidates)} 只 ({len(candidates)/len(stock_list)*100:.1f}%)")

        if not candidates:
            print("\n⚠️ 无股票符合条件，尝试放宽参数...")
            self._print_no_results_advice()
            return

        self.results = candidates[:self.params['max_results']]

        self._print_detailed_report(start_time)
        self._save_results(start_time)

    def _analyze_stock(self, stock_code: str) -> Optional[StockSignal]:
        """分析单只股票"""
        try:
            snapshot = tq.get_market_snapshot(stock_code)
            if not snapshot or 'LastClose' not in snapshot:
                return None

            last_close = float(snapshot['LastClose'])
            now_price = float(snapshot['Now'])
            open_price = float(snapshot.get('Open', now_price))
            high_price = float(snapshot.get('Max', now_price))
            volume = float(snapshot.get('Volume', 0))
            amount = float(snapshot.get('Amount', 0))

            if last_close <= 0 or now_price <= 0:
                return None

            rise_pct = (now_price / last_close - 1) * 100
            high_open_ratio = (open_price / last_close - 1) * 100

            info = tq.get_stock_info(stock_code)
            name = info.get('Name', '') if info else ''

            signal_type = SignalType.NO_SIGNAL
            details = {}

            if rise_pct >= 9.9:
                signal_type = SignalType.LIMIT_UP
                details['状态'] = "封涨停"
            elif rise_pct >= self.params['near_limit_up']:
                signal_type = SignalType.NEAR_HIGH
                details['状态'] = f"接近涨停({rise_pct:.1f}%)"
            elif high_open_ratio >= self.params['min_high_open']:
                signal_type = SignalType.HIGH_OPEN
                details['状态'] = f"高开{high_open_ratio:.1f}%"
            elif rise_pct >= self.params['strong_rise_min']:
                signal_type = SignalType.STRONG_RISE
                details['状态'] = f"强势上涨(+{rise_pct:.1f}%)"

            if signal_type == SignalType.NO_SIGNAL:
                kline_data = self._get_kline_data(stock_code)
                if kline_data is not None:
                    ma_bullish = self._check_ma_bullish(kline_data, now_price)
                    volume_ok = self._check_volume_surge(kline_data, volume)

                    if ma_bullish and volume_ok:
                        signal_type = SignalType.VOLUME_SURGE
                        details['状态'] = "放量突破+均线多头"
                    elif ma_bullish:
                        signal_type = SignalType.MA_BULLISH
                        details['状态'] = "均线多头排列"

            if signal_type == SignalType.NO_SIGNAL:
                return None

            signal = StockSignal(
                code=stock_code,
                name=name,
                signal_type=signal_type,
                current_price=now_price,
                last_close=last_close,
                open_price=open_price,
                high_price=high_price,
                volume=volume,
                amount=amount,
                rise_pct=round(rise_pct, 2),
                high_open_ratio=round(high_open_ratio, 2),
                details=details
            )

            kline_data = self._get_kline_data(stock_code)
            score = self.scoring_system.calculate_score(signal, kline_data)

            return signal

        except Exception as e:
            return None

    def _get_kline_data(self, stock_code: str):
        """获取K线数据"""
        try:
            kline = tq.get_market_data(
                stock_list=[stock_code],
                period='1d',
                count=25,
                dividend_type='none'
            )

            if kline and stock_code in kline:
                return kline[stock_code]
            return None
        except:
            return None

    def _check_ma_bullish(self, df, current_price: float) -> bool:
        """检查均线多头排列"""
        try:
            close_series = df['close']
            if len(close_series) < 21:
                return False

            ma5 = close_series.rolling(window=5).mean().iloc[-1]
            ma10 = close_series.rolling(window=10).mean().iloc[-1]
            ma20 = close_series.rolling(window=20).mean().iloc[-1]

            return ma5 > ma10 > ma20 and current_price > ma5
        except:
            return False

    def _check_volume_surge(self, df, current_volume: float) -> bool:
        """检查成交量放大"""
        try:
            vol_series = df['volume']
            if len(vol_series) < 6:
                return False

            avg_vol_5d = vol_series.iloc[-6:-1].mean()
            if avg_vol_5d > 0:
                ratio = current_volume / avg_vol_5d
                return ratio >= self.params['volume_surge_ratio']
            return False
        except:
            return False

    def _print_detailed_report(self, start_time):
        """打印详细报告"""
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        print(f"\n{'='*95}")
        print(f"【🏆 量化打板选股结果】按评分排序 (Top {len(self.results)})")
        print('='*95)

        print(f"\n  {'排名':<4} {'代码':<12} {'名称':<8} {'信号类型':<12} "
              f"{'现价':>7} {'涨幅%':>6} {'高开%':>6} {'评分':>5} {'成交额(万)':>10}")
        print('  ' + '-' * 98)

        for i, signal in enumerate(self.results, 1):
            name = signal.name[:6]
            amount_wan = signal.amount / 10000
            print(f"  {i:<4} {signal.code:<12} {name:<8} {signal.signal_type.value:<12} "
                  f"{signal.current_price:>7.2f} {signal.rise_pct:>6.2f}% {signal.high_open_ratio:>6.2f}% "
                  f"{signal.score:>5.1f} {amount_wan:>10.0f}")

        if len(self.results) >= 3:
            print(f"\n{'='*95}")
            print(f"  🌟 TOP 3 重点推荐:")
            print('='*95)

            for i, signal in enumerate(self.results[:3], 1):
                print(f"\n  【{i}】{signal.code} {signal.name}")
                print(f"      💰 当前价格: {signal.current_price:.2f}元 | 涨幅: {signal.rise_pct:+.2f}%")
                print(f"      📊 信号类型: {signal.signal_type.value}")

                if signal.high_open_ratio != 0:
                    print(f"      📈 高开幅度: {signal.high_open_ratio:+.2f}%")

                print(f"      💵 成交金额: {signal.amount/10000:.0f}万元")
                print(f"      ⭐ 综合评分: {signal.score}/100")

                advice = self._generate_advice(signal)
                print(f"      ⚡ 操作建议: {advice}")

        stats = self._calculate_statistics()
        print(f"\n{'='*95}")
        print(f"【📊 统计分析】")
        print('='*95)
        print(f"\n  总耗时: {elapsed:.1f}秒")
        print(f"  平均评分: {stats['avg_score']:.1f}")
        print(f"  最高评分: {stats['max_score']:.1f}")
        print(f"  最低评分: {stats['min_score']:.1f}")

        if stats['signal_types']:
            print(f"\n  信号类型分布:")
            for stype, count in sorted(stats['signal_types'].items(), key=lambda x: -x[1]):
                pct = count / len(self.results) * 100
                bar = '█' * int(pct / 5)
                print(f"    {stype.value:<12}: {count:>3}只 ({pct:>5.1f}%) {bar}")

        price_ranges = stats['price_ranges']
        if price_ranges:
            print(f"\n  价格区间分布:")
            for range_name, count in sorted(price_ranges.items()):
                pct = count / len(self.results) * 100
                print(f"    {range_name:<12}: {count:>3}只 ({pct:>5.1f}%)")

    def _calculate_statistics(self) -> dict:
        """计算统计信息"""
        if not self.results:
            return {}

        scores = [s.score for s in self.results]
        signal_types = {}
        price_ranges = {'<5元': 0, '5-10元': 0, '10-30元': 0, '30-50元': 0, '>50元': 0}

        for signal in self.results:
            stype = signal.signal_type
            signal_types[stype] = signal_types.get(stype, 0) + 1

            price = signal.current_price
            if price < 5:
                price_ranges['<5元'] += 1
            elif price < 10:
                price_ranges['5-10元'] += 1
            elif price < 30:
                price_ranges['10-30元'] += 1
            elif price < 50:
                price_ranges['30-50元'] += 1
            else:
                price_ranges['>50元'] += 1

        return {
            'avg_score': sum(scores) / len(scores),
            'max_score': max(scores),
            'min_score': min(scores),
            'signal_types': signal_types,
            'price_ranges': price_ranges,
        }

    def _generate_advice(self, signal: StockSignal) -> str:
        """生成操作建议"""
        if signal.score >= 85:
            if signal.signal_type == SignalType.LIMIT_UP:
                return "⭐⭐⭐ 强势涨停! 关注明日连板机会"
            else:
                return "⭐⭐⭐ 强烈关注，可逢低布局"
        elif signal.score >= 75:
            if signal.signal_type in [SignalType.NEAR_HIGH, SignalType.HIGH_OPEN]:
                return "⭐⭐ 积极跟踪，准备介入"
            else:
                return "⭐⭐ 可以关注，适当参与"
        elif signal.score >= 65:
            return "⭐ 一般关注，轻仓试探"
        else:
            return "⚠️ 观望为主，等待更好时机"

    def _save_results(self, start_time):
        """保存结果到文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = Path(__file__).parent / f'limitup_fullmarket_{timestamp}.txt'

        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("=" * 90 + "\n")
                f.write(f"量化打板选股策略 - 全市场扫描结果\n")
                f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"候选数量: {len(self.results)}\n")
                f.write("=" * 90 + "\n\n")

                for i, signal in enumerate(self.results, 1):
                    f.write(f"{i}. {signal.code} {signal.name}\n")
                    f.write(f"   价格: {signal.current_price:.2f} | 涨幅: {signal.rise_pct:+.2f}%\n")
                    f.write(f"   信号: {signal.signal_type.value} | 评分: {signal.score}\n")
                    f.write(f"   建议: {self._generate_advice(signal)}\n\n")

            print(f"\n💾 报告已保存: {report_file.name}")
        except Exception as e:
            print(f"\n⚠️ 保存失败: {e}")

    def _print_no_results_advice(self):
        """打印无结果的调整建议"""
        print("\n" + "=" * 80)
        print("【建议调整参数】")
        print("=" * 80)
        print("""
  方案1: 降低评分门槛
    将 min_score 从 60 降至 50 或更低

  方案2: 放宽涨幅要求
    将 strong_rise_min 从 3.0 降至 1.5 或 2.0

  方案3: 扩大扫描范围
    将 max_stocks_scan 从 200 提升至 500 或更高

  方案4: 仅使用均线筛选
    注释掉其他条件，仅保留 MA_BULLISH 信号类型
""")


def main():
    strategy = EnhancedLimitUpStrategy()

    try:
        print("\n[初始化] 连接TQ接口...")
        tq.initialize(path=os.path.abspath(__file__))
        print(f"  → TQ连接成功! run_id={tq.run_id}")

        strategy.run_full_market_scan()

    except KeyboardInterrupt:
        print("\n\n[用户中断]")
    except Exception as e:
        print(f"\n[ERROR] {e}")
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
