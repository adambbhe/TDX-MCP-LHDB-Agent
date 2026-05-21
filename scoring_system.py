# -*- coding: utf-8 -*-
"""
统一评分系统模块
功能:
1. 多维度评分（信号强度、价格位置、量能质量、动能指标、风控指标）
2. 可配置的权重系统
3. 统一的评分接口
4. 详细的评分明细输出
"""

from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum


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
    current_price: float
    last_close: float
    volume: float = 0
    amount: float = 0
    high_open_ratio: float = 0
    ma5: float = 0
    ma10: float = 0
    ma20: float = 0
    score: float = 0
    details: Dict = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class UnifiedScoringSystem:
    """统一评分系统"""

    def __init__(self, custom_weights: Optional[Dict] = None):
        """初始化评分系统

        Args:
            custom_weights: 自定义权重配置，如未提供则使用默认权重
        """
        self.default_weights = {
            'signal_strength': 25,
            'price_position': 20,
            'volume_quality': 20,
            'momentum': 20,
            'risk_control': 15
        }

        self.weights = custom_weights if custom_weights else self.default_weights.copy()
        self._validate_weights()

    def _validate_weights(self):
        """验证权重配置"""
        total_weight = sum(self.weights.values())
        if not (99 <= total_weight <= 101):
            raise ValueError(f"权重总和应为100%，当前为{total_weight}%")

    def calculate_score(self, signal: StockSignal, kline_data: Optional[Dict] = None) -> float:
        """计算综合评分

        Args:
            signal: 股票信号数据
            kline_data: K线数据，用于价格位置评分

        Returns:
            综合评分 (0-100)
        """
        try:
            score = 0.0

            signal_strength = self._score_signal_strength(signal)
            price_position = self._score_price_position(signal, kline_data)
            volume_quality = self._score_volume_quality(signal)
            momentum = self._score_momentum(signal)
            risk_control = self._score_risk_control(signal)

            score += signal_strength * self.weights['signal_strength'] / 100
            score += price_position * self.weights['price_position'] / 100
            score += volume_quality * self.weights['volume_quality'] / 100
            score += momentum * self.weights['momentum'] / 100
            score += risk_control * self.weights['risk_control'] / 100

            signal.score = round(score, 1)
            signal.details['评分明细'] = {
                '总分': f"{score:.1f}",
                '信号强度': f"{signal_strength:.1f}",
                '价格位置': f"{price_position:.1f}",
                '量能质量': f"{volume_quality:.1f}",
                '动能指标': f"{momentum:.1f}",
                '风控指标': f"{risk_control:.1f}"
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
                base_score = 100
            elif rise >= 9.95:
                base_score = 95

        elif signal.signal_type == SignalType.AUCTION_HIGH_OPEN:
            if signal.high_open_ratio >= 5:
                base_score = 70
            elif signal.high_open_ratio >= 3:
                base_score = 65

        return min(base_score, 100)

    def _score_price_position(self, signal: StockSignal, kline_data: Optional[Dict] = None) -> float:
        """价格位置评分 (基于均线)"""
        if kline_data is None or signal.code not in kline_data:
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
            return 100
        elif price > ma5 > ma10:
            return 85
        elif price > ma5:
            return 70
        elif price > ma20:
            return 55
        else:
            return 35

    def _score_volume_quality(self, signal: StockSignal) -> float:
        """量能质量评分"""
        if signal.amount <= 0:
            return 50

        if signal.signal_type == SignalType.LIMIT_UP:
            if signal.amount > 100000000:
                return 95
            elif signal.amount > 50000000:
                return 85
            else:
                return 70

        else:
            ratio = signal.amount / max(signal.last_close * signal.volume, 1)
            if ratio > 1.5:
                return 85
            elif ratio > 1.0:
                return 70
            else:
                return 55

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
        score = 80

        if '*' in signal.name:
            score -= 30
        if signal.current_price < 5:
            score -= 10
        if signal.high_open_ratio > 6:
            score -= 15
        if (signal.current_price / signal.last_close - 1) > 0.095:
            score -= 10

        return max(score, 0)
