# -*- coding: utf-8 -*-
"""
量化打板选股策略系统 - 完整版
功能模块:
1. 竞价数据分析 (9:15-9:25)
2. 打板信号检测 (实时监控)
3. 综合评分系统 (多维度评估)
4. 风控与仓位管理 (风险控制)
5. 交易执行接口 (自动下单)

策略流程:
  股票池 → 竞价筛选 → 开盘确认 → 打板检测 → 评分排序 → 风控过滤 → 执行交易
"""

import sys
import os
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
import threading

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tqcenter import tq


class SignalType(Enum):
    """信号类型"""
    NO_SIGNAL = "无信号"
    AUCTION_HIGH_OPEN = "竞价高开"
    RAPID_RISE = "快速拉升"
    NEAR_LIMIT_UP = "接近涨停"
    LIMIT_UP = "封涨停"
    STRONG_BREAKOUT = "强势突破"


@dataclass
class StockSignal:
    """股票信号数据"""
    code: str
    name: str
    signal_type: SignalType
    signal_time: datetime
    current_price: float
    open_price: float
    last_close: float
    high_open_ratio: float  # 高开比例
    volume: float
    amount: float
    turnover_rate: float  # 换手率
    ma5: float = 0
    ma10: float = 0
    ma20: float = 0
    score: float = 0
    details: Dict = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class AuctionAnalyzer:
    """竞价数据分析器"""

    def __init__(self):
        self.params = {
            'min_high_open': 2.0,      # 最小高开比例(%)
            'max_high_open': 7.0,      # 最大高开比例(%)
            'min_auction_amount': 50000000,  # 最小竞价金额(元)
            'min_auction_volume_ratio': 0.3,  # 竞价量/昨日成交量
        }

    def analyze_auction(self, stock_code: str) -> Optional[StockSignal]:
        """
        分析竞价数据
        返回: StockSignal 或 None(不符合条件)
        """
        try:
            snapshot = tq.get_market_snapshot(stock_code)
            if not snapshot or 'LastClose' not in snapshot:
                return None

            last_close = float(snapshot.get('LastClose', 0))
            open_price = float(snapshot.get('Open', 0))
            now_price = float(snapshot.get('Now', 0))

            if last_close <= 0 or open_price <= 0:
                return None

            high_open_ratio = (open_price / last_close - 1) * 100

            if not (self.params['min_high_open'] <= high_open_ratio <= self.params['max_high_open']):
                return None

            amount = float(snapshot.get('Amount', 0))
            volume = float(snapshot.get('Volume', 0))

            if amount < self.params['min_auction_amount']:
                return None

            info = tq.get_stock_info(stock_code)
            name = info.get('Name', '') if info else ''

            signal = StockSignal(
                code=stock_code,
                name=name,
                signal_type=SignalType.AUCTION_HIGH_OPEN,
                signal_time=datetime.now(),
                current_price=now_price,
                open_price=open_price,
                last_close=last_close,
                high_open_ratio=round(high_open_ratio, 2),
                volume=volume,
                amount=amount,
                turnover_rate=0
            )

            signal.details['竞价分析'] = {
                '高开比例': f'{high_open_ratio:.2f}%',
                '竞价金额': f'{amount/10000:.0f}万',
                '符合条件': True
            }

            return signal

        except Exception as e:
            print(f"  [ERROR] 竞价分析失败 {stock_code}: {e}")
            return None


class LimitUpDetector:
    """打板信号检测器"""

    def __init__(self):
        self.params = {
            'limit_up_threshold': 9.9,     # 涨停阈值(%)
            'near_limit_up_threshold': 8.0, # 接近涨停阈值(%)
            'rapid_rise_threshold': 3.0,    # 快速拉升阈值(%/分钟)
            'min_breakout_volume': 1000000, # 突破最小成交量
        }

    def detect_signal(self, stock_code: str, base_signal: StockSignal = None) -> Optional[StockSignal]:
        """
        检测打板信号
        参数:
        - stock_code: 股票代码
        - base_signal: 基础信号(可选，用于叠加判断)
        """
        try:
            snapshot = tq.get_market_snapshot(stock_code)
            if not snapshot or 'LastClose' not in snapshot:
                return None

            last_close = float(snapshot['LastClose'])
            now_price = float(snapshot['Now'])
            high_price = float(snapshot.get('Max', now_price))
            volume = float(snapshot.get('Volume', 0))
            amount = float(snapshot.get('Amount', 0))

            if last_close <= 0:
                return None

            rise_pct = (now_price / last_close - 1) * 100
            high_rise_pct = (high_price / last_close - 1) * 100

            info = tq.get_stock_info(stock_code)
            name = info.get('Name', '') if info else ''

            signal_type = SignalType.NO_SIGNAL
            details = {}

            if rise_pct >= self.params['limit_up_threshold']:
                signal_type = SignalType.LIMIT_UP
                details['状态'] = "已封涨停"
                details['涨幅'] = f"{rise_pct:.2f}%"

            elif rise_pct >= self.params['near_limit_up_threshold']:
                signal_type = SignalType.NEAR_LIMIT_UP
                details['状态'] = "接近涨停"
                details['涨幅'] = f"{rise_pct:.2f}%"
                details['距离涨停'] = f"{self.params['limit_up_threshold'] - rise_pct:.2f}%"

            elif high_rise_pct > self.params['rapid_rise_threshold']:
                signal_type = SignalType.RAPID_RISE
                details['状态'] = "快速拉升中"
                details['当前涨幅'] = f"{rise_pct:.2f}%"
                details['最高涨幅'] = f"{high_rise_pct:.2f}%"

            elif base_signal and base_signal.signal_type == SignalType.AUCTION_HIGH_OPEN:
                signal_type = SignalType.STRONG_BREAKOUT
                details['状态'] = "竞价高开后强势"
                details['高开比例'] = f"{base_signal.high_open_ratio:.2f}%"
                details['当前涨幅'] = f"{rise_pct:.2f}%"

            else:
                return None

            signal = StockSignal(
                code=stock_code,
                name=name,
                signal_type=signal_type,
                signal_time=datetime.now(),
                current_price=now_price,
                open_price=float(snapshot.get('Open', now_price)),
                last_close=last_close,
                high_open_ratio=(float(snapshot.get('Open', now_price)) / last_close - 1) * 100,
                volume=volume,
                amount=amount,
                turnover_rate=0,
                details=details
            )

            return signal

        except Exception as e:
            print(f"  [ERROR] 信号检测失败 {stock_code}: {e}")
            return None


class ScoringSystem:
    """综合评分系统"""

    def __init__(self):
        self.weights = {
            'signal_strength': 30,    # 信号强度
            'price_position': 20,     # 价格位置(均线)
            'volume_quality': 20,     # 量能质量
            'momentum': 15,           # 动能指标
            'risk_control': 15,       # 风控指标
        }

    def calculate_score(self, signal: StockSignal, kline_data=None) -> float:
        """
        计算综合评分 (0-100分)
        """
        score = 0.0

        try:
            score += self._score_signal_strength(signal) * self.weights['signal_strength'] / 100
            score += self._score_price_position(signal, kline_data) * self.weights['price_position'] / 100
            score += self._score_volume_quality(signal) * self.weights['volume_quality'] / 100
            score += self._score_momentum(signal) * self.weights['momentum'] / 100
            score += self._score_risk_control(signal) * self.weights['risk_control'] / 100

            signal.score = round(score, 1)
            signal.details['评分明细'] = {
                '总分': f"{score:.1f}",
                '信号强度': f"{self._score_signal_strength(signal):.1f}",
                '价格位置': f"{self._score_price_position(signal, kline_data):.1f}",
                '量能质量': f"{self._score_volume_quality(signal):.1f}",
                '动能指标': f"{self._score_momentum(signal):.1f}",
                '风控指标': f"{self._score_risk_control(signal):.1f}"
            }

            return score

        except Exception as e:
            print(f"  [ERROR] 评分计算失败: {e}")
            return 0.0

    def _score_signal_strength(self, signal: StockSignal) -> float:
        """信号强度评分 (0-100)"""
        type_scores = {
            SignalType.LIMIT_UP: 100,
            SignalType.NEAR_LIMIT_UP: 85,
            SignalType.RAPID_RISE: 70,
            SignalType.AUCTION_HIGH_OPEN: 60,
            SignalType.STRONG_BREAKOUT: 75,
        }
        base_score = type_scores.get(signal.signal_type, 0)

        if signal.signal_type == SignalType.LIMIT_UP:
            rise = (signal.current_price / signal.last_close - 1) * 100
            if rise >= 9.98:
                base_score = 100  # 一字板或T字板
            elif rise >= 9.95:
                base_score = 95  # 强势封板

        elif signal.signal_type == SignalType.AUCTION_HIGH_OPEN:
            if signal.high_open_ratio >= 5:
                base_score = 70
            elif signal.high_open_ratio >= 3:
                base_score = 65

        return min(base_score, 100)

    def _score_price_position(self, signal: StockSignal, kline_data=None) -> float:
        """价格位置评分 (基于均线)"""
        if not kline_data or signal.code not in kline_data:
            if signal.current_price > signal.last_close:
                return 60
            return 40

        df = kline_data[signal.code]
        close_series = df['close']

        if len(close_series) < 21:
            return 50

        ma5 = close_series.rolling(window=5).mean().iloc[-1]
        ma10 = close_series.rolling(window=10).mean().iloc[-1]
        ma20 = close_series.rolling(window=20).mean().iloc[-1]

        signal.ma5 = round(ma5, 2)
        signal.ma10 = round(ma10, 2)
        signal.ma20 = round(ma20, 2)

        price = signal.current_price

        if price > ma5 > ma10 > ma20:
            return 100  # 完美多头排列
        elif price > ma5 > ma10:
            return 85   # 双均线多头
        elif price > ma5:
            return 70   # 站上MA5
        elif price > ma20:
            return 55   # 在MA20上方但短期偏弱
        else:
            return 35   # 弱势

    def _score_volume_quality(self, signal: StockSignal) -> float:
        """量能质量评分"""
        if signal.amount <= 0:
            return 50

        if signal.signal_type == SignalType.LIMIT_UP:
            if signal.amount > 100000000:  # 1亿以上
                return 95
            elif signal.amount > 50000000:  # 5000万以上
                return 85
            else:
                return 70

        else:
            ratio = signal.amount / max(signal.last_close * signal.volume, 1)
            if ratio > 1.5:
                return 85  # 放量明显
            elif ratio > 1.0:
                return 70  # 正常放量
            else:
                return 55  # 缩量

    def _score_momentum(self, signal: StockSignal) -> float:
        """动能指标评分"""
        rise = (signal.current_price / signal.last_close - 1) * 100

        if signal.signal_type == SignalType.LIMIT_UP:
            return 95

        elif rise >= 7:
            return 90
        elif rise >= 5:
            return 80
        elif rise >= 3:
            return 70
        elif rise >= 1:
            return 60
        elif rise >= 0:
            return 50
        else:
            return 30

    def _score_risk_control(self, signal: StockSignal) -> float:
        """风控指标评分"""
        score = 80  # 基础分

        if '*' in signal.name:
            score -= 30  # ST股扣分
        if signal.current_price < 5:
            score -= 10  # 低价股风险
        if signal.high_open_ratio > 6:
            score -= 15  # 高开过多风险
        if (signal.current_price / signal.last_close - 1) > 0.095:
            score -= 10  # 接近涨停追高风险

        return max(score, 0)


class RiskManager:
    """风控与仓位管理"""

    def __init__(self):
        self.params = {
            'max_total_position': 0.7,      # 最大总仓位(70%)
            'single_stock_max': 0.15,        # 单只股票最大仓位(15%)
            'max_holdings': 5,              # 最大持仓数量
            'stop_loss_pct': 5.0,           # 止损比例(%)
            'take_profit_pct': 15.0,         # 止盈比例(%)
            'daily_loss_limit': 3.0,         # 日亏损限制(%)
            'min_score_threshold': 60,       # 最低评分门槛
        }

        self.current_positions = {}
        self.daily_pnl = 0.0
        self.total_capital = 1000000.0  # 假设本金100万

    def check_entry_conditions(self, signal: StockSignal) -> Tuple[bool, str]:
        """检查入场条件"""
        reasons = []

        if signal.score < self.params['min_score_threshold']:
            reasons.append(f"评分不足({signal.score}<{self.params['min_score_threshold']})")

        if len(self.current_positions) >= self.params['max_holdings']:
            reasons.append(f"持仓已达上限({len(self.current_positions)}只)")

        current_total = sum(pos['value'] for pos in self.current_positions.values())
        if current_total / self.total_capital >= self.params['max_total_position']:
            reasons.append(f"总仓位已满({current_total/self.total_capital*100:.0f}%)")

        if signal.signal_type == SignalType.NO_SIGNAL:
            reasons.append("无有效交易信号")

        is_valid = len(reasons) == 0
        message = "✅ 符合入场条件" if is_valid else f"❌ {'; '.join(reasons)}"

        return is_valid, message

    def calculate_position_size(self, signal: StockSignal) -> float:
        """计算建议仓位大小"""
        base_size = self.total_capital * 0.1  # 基础10%仓位

        score_factor = signal.score / 100
        risk_factor = 1.0

        if signal.score >= 90:
            risk_factor = 1.5  # 高分可加仓
        elif signal.score >= 80:
            risk_factor = 1.2
        elif signal.score < 70:
            risk_factor = 0.8  # 低分减仓

        position_value = base_size * score_factor * risk_factor

        max_single = self.total_capital * self.params['single_stock_max']
        position_value = min(position_value, max_single)

        available = self.total_capital * self.params['max_total_position']
        used = sum(pos['value'] for pos in self.current_positions.values())
        remaining = available - used
        position_value = min(position_value, remaining)

        return round(position_value, 2)

    def check_exit_conditions(self, stock_code: str, current_price: float,
                            entry_price: float) -> Tuple[bool, str, str]:
        """检查出场条件"""
        if stock_code not in self.current_positions:
            return False, "", ""

        pnl_pct = (current_price / entry_price - 1) * 100
        action = ""
        reason = ""

        if pnl_pct <= -self.params['stop_loss_pct']:
            action = "SELL"
            reason = f"触发止损 ({pnl_pct:.2f}%)"

        elif pnl_pct >= self.params['take_profit_pct']:
            action = "SELL"
            reason = f"触发止盈 ({pnl_pct:.2f}%)"

        elif abs(pnl_pct) > 0.01 and self.daily_pnl / self.total_capital * 100 <= -self.params['daily_loss_limit']:
            action = "REDUCE"
            reason = f"触及日亏限制 (日亏{self.daily_pnl/self.total_capital*100:.2f}%)"

        should_exit = action == "SELL"
        return should_exit, action, reason


class QuantLimitUpStrategy:
    """量化打板选股策略主类"""

    def __init__(self):
        self.auction_analyzer = AuctionAnalyzer()
        self.limit_up_detector = LimitUpDetector()
        self.scoring_system = ScoringSystem()
        self.risk_manager = RiskManager()

        self.signals = []
        self.filtered_signals = []
        self.execution_log = []

    def run_strategy(self, stock_list=None, max_stocks=50,
                    enable_trading=False, dry_run=True):
        """
        运行完整策略流程
        参数:
        - stock_list: 股票列表(None则获取全市场)
        - max_stocks: 最大扫描数
        - enable_trading: 是否启用实盘交易
        - dry_run: 模拟运行(不实际下单)
        """
        start_time = datetime.now()

        print("=" * 90)
        print("  🚀 量化打板选股策略系统")
        print(f"  启动时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  模式: {'🔴 实盘交易' if enable_trading and not dry_run else '📊 模拟测试'}")
        print("=" * 90)

        if stock_list is None:
            print("\n[步骤1] 获取股票列表...")
            all_stocks = tq.get_stock_list()
            if isinstance(all_stocks, list) and len(all_stocks) > 0:
                stock_list = all_stocks[:max_stocks]
                print(f"  → 获取到 {len(stock_list)} 只股票")
            else:
                print("  → [ERROR] 无法获取股票列表")
                return

        print(f"\n{'='*90}")
        print(f"[步骤2] 第一轮: 竞价数据分析 (目标: {len(stock_list)}只)")
        print('='*90)

        auction_passed = []
        for i, stock in enumerate(stock_list):
            if (i + 1) % 20 == 0:
                print(f"  进度: [{i+1}/{len(stock_list)}]", end='\r')

            signal = self.auction_analyzer.analyze_auction(stock)
            if signal:
                auction_passed.append(signal)

            time.sleep(0.02)

        print(f"\n  ✅ 竞价筛选通过: {len(auction_passed)}/{len(stock_list)} 只")

        if not auction_passed:
            print("\n⚠️  无股票通过竞价筛选，策略结束")
            self._print_summary(start_time, 0)
            return

        print(f"\n{'='*90}")
        print(f"[步骤3] 第二轮: 打板信号检测 & K线数据获取")
        print('='*90)

        signals_with_kline = []
        for i, auction_signal in enumerate(auction_passed):
            print(f"  处理: [{i+1}/{len(auction_passed)}] {auction_signal.code} {auction_signal.name}", end='\r')

            limit_signal = self.limit_up_detector.detect_signal(
                auction_signal.code,
                base_signal=auction_signal
            )

            if limit_signal:
                try:
                    kline = tq.get_market_data(
                        stock_list=[auction_signal.code],
                        period='1d',
                        count=25,
                        dividend_type='none'
                    )
                    signals_with_kline.append((limit_signal, kline))
                except:
                    signals_with_kline.append((limit_signal, None))

            time.sleep(0.03)

        print(f"\n  ✅ 信号检测完成: {len(signals_with_kline)} 只候选股票")

        print(f"\n{'='*90}")
        print(f"[步骤4] 第三轮: 综合评分")
        print('='*90)

        scored_signals = []
        for signal, kline in signals_with_kline:
            score = self.scoring_system.calculate_score(signal, kline)
            if score >= self.risk_manager.params['min_score_threshold']:
                scored_signals.append(signal)
                print(f"  ✓ {signal.code} {signal.name:<8} | "
                      f"{signal.signal_type.value:<12} | "
                      f"评分:{score:>5.1f} | "
                      f"价格:{signal.current_price:>7.2f}")

        scored_signals.sort(key=lambda x: x.score, reverse=True)

        print(f"\n{'='*90}")
        print(f"[步骤5] 第四轮: 风控过滤")
        print('='*90)

        final_candidates = []
        for signal in scored_signals:
            can_enter, msg = self.risk_manager.check_entry_conditions(signal)
            if can_enter:
                position_size = self.risk_manager.calculate_position_size(signal)
                signal.details['建议仓位'] = f"{position_size:.0f}元 ({position_size/self.risk_manager.total_capital*100:.1f}%)"
                final_candidates.append((signal, position_size))
                print(f"  🎯 {signal.code} {signal.name:<8} | 评分:{signal.score:>5.1f} | {msg} | 仓位:{position_size/10000:.0f}万")
            else:
                print(f"  ❌ {signal.code} {signal.name:<8} | 评分:{signal.score:>5.1f} | {msg}")

        self.filtered_signals = final_candidates

        print(f"\n{'='*90}")
        print(f"【最终结果】共 {len(final_candidates)} 只股票进入交易候选")
        print('='*90)

        if final_candidates:
            self._print_final_report(final_candidates, dry_run)

            if enable_trading and not dry_run:
                self._execute_trades(final_candidates)
        else:
            print("\n⚠️  无股票通过所有筛选条件")

        self._print_summary(start_time, len(final_candidates))

    def _print_final_report(self, candidates: List, dry_run=True):
        """输出最终报告"""

        print(f"\n{'='*90}")
        print(f"【🏆 量化打板选股结果】按评分排序")
        print('='*90)

        print(f"\n  {'排名':<4} {'代码':<12} {'名称':<8} {'信号类型':<12} "
              f"{'现价':>7} {'高开%':>6} {'评分':>5} {'建议仓位':>10} {'操作建议'}")
        print('  ' + '-' * 95)

        for i, (signal, position) in enumerate(candidates[:10], 1):
            name = signal.name[:6]
            advice = self._generate_advice(signal)
            print(f"  {i:<4} {signal.code:<12} {name:<8} {signal.signal_type.value:<12} "
                  f"{signal.current_price:>7.2f} {signal.high_open_ratio:>6.2f}% "
                  f"{signal.score:>5.1f} {position/10000:>8.0f}万  {advice}")

        if len(candidates) > 10:
            print(f"\n  ... 还有 {len(candidates)-10} 只候选股票未显示")

        top3 = candidates[:3] if len(candidates) >= 3 else candidates
        if top3:
            print(f"\n  🌟 TOP 3 重点推荐:")
            print('  ' + '=' * 95)
            for i, (signal, pos) in enumerate(top3, 1):
                print(f"\n  【{i}】{signal.code} {signal.name}")
                print(f"      💰 当前价格: {signal.current_price:.2f}元")
                print(f"      📊 信号类型: {signal.signal_type.value}")
                print(f"      📈 高开幅度: {signal.high_open_ratio:.2f}%")
                print(f"      ⭐ 综合评分: {signal.score}/100")
                print(f"      💼 建议仓位: {pos/10000:.0f}万 ({pos/self.risk_manager.total_capital*100:.1f}%)")

                if signal.ma5 > 0:
                    print(f"      📉 均线状态: MA5={signal.ma5}, MA10={signal.ma10}, MA20={signal.ma20}")

                if '评分明细' in signal.details:
                    details = signal.details['评分明细']
                    print(f"      📋 评分详情:")
                    print(f"         信号强度: {details.get('信号强度')}/100")
                    print(f"         价格位置: {details.get('价格位置')}/100")
                    print(f"         量能质量: {details.get('量能质量')}/100")
                    print(f"         动能指标: {details.get('动能指标')}/100")
                    print(f"         风控指标: {details.get('风控指标')}/100")

                print(f"      ⚡ 操作建议: {self._generate_advice(signal)}")

    def _generate_advice(self, signal: StockSignal) -> str:
        """生成操作建议"""
        if signal.score >= 90:
            if signal.signal_type == SignalType.LIMIT_UP:
                return "⭐⭐⭐ 强烈关注，等待开板机会"
            else:
                return "⭐⭐⭐ 重点跟踪，准备介入"
        elif signal.score >= 80:
            if signal.signal_type in [SignalType.NEAR_LIMIT_UP, SignalType.RAPID_RISE]:
                return "⭐⭐ 积极关注，逢低吸纳"
            else:
                return "⭐⭐ 可以关注，适当参与"
        elif signal.score >= 70:
            return "⭐ 一般关注，轻仓试探"
        else:
            return "⚠️ 观望为主，谨慎参与"

    def _execute_trades(self, candidates: List):
        """执行交易"""
        print(f"\n{'='*90}")
        print(f"【⚡ 开始执行交易】")
        print('='*90)

        for signal, position in candidates[:3]:  # 最多交易前3只
            try:
                print(f"\n  📤 准备下单: {signal.code} {signal.name}")
                print(f"     目标仓位: {position/10000:.0f}万元")

                result = tq.order_stock(
                    stock_code=signal.code,
                    price=signal.current_price,
                    volume=int(position / signal.current_price / 100) * 100,
                    order_type='buy',
                    strategy_name='量化打板策略'
                )

                if result and result.get('errorcode', -1) == 0:
                    print(f"     ✅ 下单成功! 订单号: {result.get('orderid', 'N/A')}")
                    self.execution_log.append({
                        'time': datetime.now(),
                        'action': 'BUY',
                        'stock': signal.code,
                        'price': signal.current_price,
                        'volume': int(position / signal.current_price / 100) * 100,
                        'status': 'SUCCESS'
                    })
                else:
                    error_msg = result.get('msg', '未知错误') if result else '返回为空'
                    print(f"     ❌ 下单失败: {error_msg}")
                    self.execution_log.append({
                        'time': datetime.now(),
                        'action': 'BUY',
                        'stock': signal.code,
                        'price': signal.current_price,
                        'status': 'FAILED',
                        'error': error_msg
                    })

                time.sleep(0.5)

            except Exception as e:
                print(f"     ❌ 异常: {e}")
                self.execution_log.append({
                    'time': datetime.now(),
                    'action': 'BUY',
                    'stock': signal.code,
                    'status': 'ERROR',
                    'error': str(e)[:100]
                })

    def _print_summary(self, start_time, candidate_count):
        """打印总结报告"""
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        timestamp = end_time.strftime('%Y%m%d_%H%M%S')
        report_file = Path(__file__).parent / f'limitup_strategy_{timestamp}.txt'

        print(f"\n{'='*90}")
        print(f"【📊 策略运行总结】")
        print('='*90)
        print(f"\n  ⏱️  总耗时: {elapsed:.1f}秒")
        print(f"  🎯 最终候选: {candidate_count}只股票")
        print(f"  📝 报告文件: {report_file.name}")

        if self.execution_log:
            success_count = sum(1 for log in self.execution_log if log['status'] == 'SUCCESS')
            print(f"  ✅ 成功下单: {success_count}笔")

        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(f"量化打板选股策略报告\n")
                f.write(f"时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"候选数量: {candidate_count}\n")
                f.write(f"{'='*50}\n\n")

                for signal, pos in self.filtered_signals:
                    f.write(f"{signal.code} {signal.name}\n")
                    f.write(f"  评分: {signal.score}\n")
                    f.write(f"  信号: {signal.signal_type.value}\n")
                    f.write(f"  建议仓位: {pos}\n\n")

            print(f"  💾 报告已保存")
        except Exception as e:
            print(f"  ⚠️ 保存报告失败: {e}")

        print(f"\n{'='*90}")


def main():
    """主函数"""
    strategy = QuantLimitUpStrategy()

    test_stocks = [
        '600519.SH', '000001.SZ', '300750.SZ',
        '000002.SZ', '601318.SH', '600036.SH',
        '000858.SZ', '002594.SZ', '601012.SH',
        '300059.SZ', '600276.SH', '000333.SZ',
        '000404.SZ', '000543.SZ', '000559.SZ'
    ]

    try:
        print("\n[初始化] 连接TQ接口...")
        tq.initialize(path=os.path.abspath(__file__))
        print(f"  → TQ连接成功! run_id={tq.run_id}")

        strategy.run_strategy(
            stock_list=test_stocks,
            max_stocks=len(test_stocks),
            enable_trading=False,
            dry_run=True
        )

    except KeyboardInterrupt:
        print("\n\n[用户中断] 策略停止")
    except Exception as e:
        print(f"\n[ERROR] 策略运行异常: {e}")
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
