# -*- coding: utf-8 -*-
"""
量化打板选股策略 - 历史回测系统
功能:
1. 获取过去一年历史数据 (250个交易日)
2. 模拟运行打板策略
3. 计算关键绩效指标:
   - 总收益率 / 年化收益率
   - 胜率 / 盈亏比
   - 最大回撤 / 夏普比率
   - 交易次数 / 平均持仓天数
4. 生成详细回测报告

回测参数:
- 回测周期: 250个交易日 (约1年)
- 初始资金: 100万元
- 单只股票最大仓位: 15%
- 止损线: -5%
- 止盈线: +15%
- 持仓上限: 5只股票
"""

import sys
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import json

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tqcenter import tq


class TradeAction(Enum):
    """交易动作"""
    BUY = "买入"
    SELL = "卖出"
    HOLD = "持有"


class ExitReason(Enum):
    """出场原因"""
    TAKE_PROFIT = "止盈"
    STOP_LOSS = "止损"
    SIGNAL_EXIT = "信号离场"
    TIME_EXIT = "时间到期"


@dataclass
class TradeRecord:
    """交易记录"""
    trade_id: int
    stock_code: str
    stock_name: str
    action: TradeAction
    price: float
    volume: int
    amount: float
    datetime: str
    signal_type: str = ""
    exit_reason: str = ""
    pnl: float = 0.0
    pnl_pct: float = 0.0
    hold_days: int = 0


@dataclass
class Position:
    """持仓信息"""
    stock_code: str
    stock_name: str
    entry_price: float
    volume: int
    amount: float
    entry_date: str
    signal_type: str = ""
    stop_loss_price: float = 0.0
    take_profit_price: float = 0.0
    max_hold_days: int = 10


class BacktestEngine:
    """回测引擎"""

    def __init__(self):
        self.params = {
            'initial_capital': 1000000,  # 初始资金100万
            'single_max_position': 0.15,  # 单只最大仓位15%
            'max_positions': 5,          # 最大持仓数
            'stop_loss_pct': 0.05,       # 止损5%
            'take_profit_pct': 0.15,      # 止盈15%
            'max_hold_days': 10,          # 最大持仓天数
            'commission_rate': 0.0003,    # 手续费率(万分之3)
            'min_score_threshold': 70,    # 策略最低评分
        }

        self.positions: List[Position] = []
        self.trade_records: List[TradeRecord] = []
        self.daily_equity: List[Dict] = []

        self.current_capital = self.params['initial_capital']
        self.total_pnl = 0.0
        self.trade_counter = 0

    def run_backtest(self, stock_list=None, days_back=250):
        """
        运行历史回测
        参数:
        - stock_list: 股票列表(None则用默认测试集)
        - days_back: 回溯天数(默认250个交易日≈1年)
        """
        start_time = datetime.now()

        print("=" * 95)
        print("  📊 量化打板选股策略 - 历史回测系统")
        print(f"  启动时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  回测周期: {days_back}个交易日 (约{days_back/242:.1f}年)")
        print(f"  初始资金: {self.params['initial_capital']/10000:.0f}万元")
        print("=" * 95)

        if stock_list is None:
            stock_list = [
                '600519.SH', '000001.SZ', '300750.SZ',
                '000002.SZ', '601318.SH', '600036.SH',
                '000858.SZ', '002594.SZ', '601012.SH',
                '000404.SZ', '000543.SZ', '000559.SZ',
                '000620.SZ', '000006.SZ', '000021.SZ'
            ]

        print(f"\n[步骤1] 获取历史数据 ({len(stock_list)}只股票 x {days_back}天)...")

        historical_data = {}
        for i, stock in enumerate(stock_list):
            if (i + 1) % 5 == 0:
                print(f"  进度: [{i+1}/{len(stock_list)}]", end='\r')

            try:
                kline_data = tq.get_market_data(
                    stock_list=[stock],
                    period='1d',
                    count=days_back + 30,
                    dividend_type='none'
                )

                if kline_data and stock in kline_data:
                    df = kline_data[stock]
                    if len(df) >= days_back:
                        historical_data[stock] = df.iloc[-days_back:]

                    info = tq.get_stock_info(stock)
                    name = info.get('Name', '') if info else ''
                    historical_data[f'{stock}_name'] = name

            except Exception as e:
                pass

            time.sleep(0.02)

        print(f"\n  ✅ 数据获取完成: {len(historical_data)//2} 只股票")

        if not historical_data:
            print("\n❌ 无法获取历史数据，回测终止")
            return

        print(f"\n{'='*95}")
        print(f"[步骤2] 开始模拟交易回测...")
        print('='*95)

        all_dates = set()
        for stock_code in historical_data:
            if not stock_code.endswith('_name'):
                all_dates.update(historical_data[stock_code].index.tolist())

        sorted_dates = sorted(list(all_dates))

        for day_idx, current_date in enumerate(sorted_dates):
            self._process_trading_day(historical_data, current_date, day_idx)

            equity = self._calculate_total_equity()
            self.daily_equity.append({
                'date': str(current_date)[:10],
                'equity': equity,
                'pnl_pct': (equity - self.params['initial_capital']) / self.params['initial_capital'] * 100,
                'positions_count': len(self.positions),
            })

            if (day_idx + 1) % 50 == 0:
                progress = (day_idx + 1) / len(sorted_dates) * 100
                print(f"  回测进度: [{day_idx+1}/{len(sorted_dates)}] ({progress:.1f}%) | "
                      f"当前权益: {equity/10000:.2f}万", end='\r')

        print(f"\n\n  ✅ 回测完成! 共 {len(sorted_dates)} 个交易日")

        self._generate_report(start_time, len(sorted_dates))

    def _process_trading_day(self, data: Dict, current_date, day_idx):
        """处理每个交易日"""

        positions_to_close = []

        for pos in self.positions:
            if pos.stock_code in data and current_date in data[pos.stock_code].index:
                row = data[pos.stock_code].loc[current_date]
                today_high = row.get('high', row['close'])
                today_low = row.get('low', row['close'])
                today_close = row['close']
                today_open = row.get('open', today_close)

                hold_days = day_idx - pos.entry_date_index if hasattr(pos, 'entry_date_index') else 0

                should_exit = False
                exit_reason = None
                exit_price = today_close

                if today_low <= pos.stop_loss_price:
                    should_exit = True
                    exit_reason = ExitReason.STOP_LOSS
                    exit_price = max(pos.stop_loss_price, today_low)

                elif today_high >= pos.take_profit_price:
                    should_exit = True
                    exit_reason = ExitReason.TAKE_PROFIT
                    exit_price = min(pos.take_profit_price, today_high)

                elif hold_days >= pos.max_hold_days:
                    should_exit = True
                    exit_reason = ExitReason.TIME_EXIT
                    exit_price = today_close

                elif self._check_exit_signal(data, pos, current_date):
                    should_exit = True
                    exit_reason = ExitReason.SIGNAL_EXIT
                    exit_price = today_close

                if should_exit:
                    positions_to_close.append((pos, exit_price, exit_reason, hold_days))

        for pos, exit_price, reason, hold_days in positions_to_close:
            self._close_position(pos, exit_price, reason, hold_days, current_date)

        if len(self.positions) < self.params['max_positions']:
            signals = self._generate_signals(data, current_date)

            for signal in signals[:3]:
                if len(self.positions) >= self.params['max_positions']:
                    break

                stock_code = signal['code']

                if stock_code in data and current_date in data[stock_code].index:
                    row = data[stock_code].loc[current_date]
                    buy_price = row.get('open', row['close'])

                    available_capital = self.current_capital * 0.8
                    position_value = min(
                        self.params['initial_capital'] * self.params['single_max_position'],
                        available_capital / max(1, self.params['max_positions'] - len(self.positions))
                    )

                    volume = int(position_value / buy_price / 100) * 100
                    if volume > 0 and volume * buy_price <= available_capital:
                        self._open_position(signal, buy_price, volume, current_date, day_idx)

    def _check_exit_signal(self, data: Dict, pos: Position, current_date) -> bool:
        """检查是否触发离场信号"""
        try:
            if pos.stock_code not in data or current_date not in data[pos.stock_code].index:
                return False

            df = data[pos.stock_code]
            current_idx = df.index.get_loc(current_date)

            if current_idx < 5:
                return False

            close_series = df['close'].iloc[max(0, current_idx-5):current_idx+1]

            if len(close_series) < 5:
                return False

            ma5 = close_series.mean()
            today_close = df.loc[current_date, 'close']

            if today_close < ma5 * 0.97:
                return True

            return False

        except Exception as e:
            return False

    def _generate_signals(self, data: Dict, current_date) -> List[Dict]:
        """生成交易信号"""
        signals = []

        for stock_code in data:
            if stock_code.endswith('_name'):
                continue

            if stock_code in [p.stock_code for p in self.positions]:
                continue

            try:
                df = data[stock_code]

                if current_date not in df.index:
                    continue

                current_idx = df.index.get_loc(current_date)
                if current_idx < 21:
                    continue

                row = df.iloc[current_idx]
                prev_row = df.iloc[current_idx - 1]

                today_close = row['close']
                yesterday_close = prev_row['close']
                today_open = row['open']
                today_volume = row['volume']
                today_amount = row.get('amount', 0)

                if yesterday_close <= 0:
                    continue

                rise_pct = (today_close / yesterday_close - 1) * 100
                high_open_ratio = (today_open / yesterday_close - 1) * 100

                signal_type = ""
                score = 50

                if rise_pct >= 9.9:
                    signal_type = "涨停"
                    score += 35
                elif rise_pct >= 7:
                    signal_type = "大涨"
                    score += 28
                elif rise_pct >= 5:
                    signal_type = "强势上涨"
                    score += 22
                elif high_open_ratio >= 2:
                    signal_type = "高开"
                    score += 15
                else:
                    continue

                close_series = df['close'].iloc[max(0, current_idx-20):current_idx+1]

                if len(close_series) >= 21:
                    ma5 = close_series.iloc[-5:].mean()
                    ma10 = close_series.iloc[-10:].mean()
                    ma20 = close_series.iloc[-20:].mean()

                    if today_close > ma5 > ma10 > ma20:
                        score += 15
                    elif today_close > ma5:
                        score += 8

                    vol_series = df['volume'].iloc[max(0, current_idx-6):current_idx]
                    if len(vol_series) >= 5:
                        avg_vol_5d = vol_series[:-1].mean() if len(vol_series) > 1 else today_volume
                        if avg_vol_5d > 0 and today_volume / avg_vol_5d > 1.3:
                            score += 10

                name_key = f'{stock_code}_name'
                stock_name = data.get(name_key, '')

                if '*' in str(stock_name):
                    score -= 12

                if today_close < 5:
                    score -= 6

                if rise_pct > 9.5:
                    score -= 4

                score = min(max(score, 0), 100)

                if score >= self.params['min_score_threshold']:
                    signals.append({
                        'code': stock_code,
                        'name': stock_name,
                        'signal_type': signal_type,
                        'score': score,
                        'price': today_close,
                        'rise_pct': rise_pct,
                        'high_open_ratio': high_open_ratio,
                    })

            except Exception as e:
                continue

        signals.sort(key=lambda x: x['score'], reverse=True)
        return signals

    def _open_position(self, signal: Dict, price: float, volume: int, 
                       date, date_index: int):
        """开仓"""
        amount = price * volume
        commission = amount * self.params['commission_rate']

        self.current_capital -= (amount + commission)

        position = Position(
            stock_code=signal['code'],
            stock_name=signal['name'],
            entry_price=price,
            volume=volume,
            amount=amount,
            entry_date=str(date)[:10],
            signal_type=signal['signal_type'],
            stop_loss_price=price * (1 - self.params['stop_loss_pct']),
            take_profit_price=price * (1 + self.params['take_profit_pct']),
            max_hold_days=self.params['max_hold_days'],
        )
        position.entry_date_index = date_index

        self.positions.append(position)

        self.trade_counter += 1
        record = TradeRecord(
            trade_id=self.trade_counter,
            stock_code=signal['code'],
            stock_name=signal['name'],
            action=TradeAction.BUY,
            price=price,
            volume=volume,
            amount=amount,
            datetime=str(date)[:10],
            signal_type=signal['signal_type'],
        )
        self.trade_records.append(record)

    def _close_position(self, pos: Position, price: float, 
                        reason: Enum, hold_days: int, date):
        """平仓"""
        amount = price * pos.volume
        commission = amount * self.params['commission_rate']

        pnl = amount - pos.amount - commission
        pnl_pct = (price / pos.entry_price - 1) * 100

        self.current_capital += (amount - commission)
        self.total_pnl += pnl

        self.trade_counter += 1
        record = TradeRecord(
            trade_id=self.trade_counter,
            stock_code=pos.stock_code,
            stock_name=pos.stock_name,
            action=TradeAction.SELL,
            price=price,
            volume=pos.volume,
            amount=amount,
            datetime=str(date)[:10],
            signal_type=pos.signal_type,
            exit_reason=reason.value,
            pnl=pnl,
            pnl_pct=round(pnl_pct, 2),
            hold_days=hold_days,
        )
        self.trade_records.append(record)

        self.positions.remove(pos)

    def _calculate_total_equity(self) -> float:
        """计算总权益"""
        total = self.current_capital

        for pos in self.positions:
            total += pos.amount

        return total

    def _generate_report(self, start_time, total_days):
        """生成回测报告"""
        end_time = datetime.now()

        final_equity = self.daily_equity[-1]['equity'] if self.daily_equity else self.params['initial_capital']
        total_return = (final_equity - self.params['initial_capital']) / self.params['initial_capital'] * 100
        annualized_return = total_return * (242 / total_days) if total_days > 0 else 0

        sell_trades = [t for t in self.trade_records if t.action == TradeAction.SELL]
        win_trades = [t for t in sell_trades if t.pnl > 0]
        lose_trades = [t for t in sell_trades if t.pnl <= 0]

        win_rate = len(win_trades) / len(sell_trades) * 100 if sell_trades else 0

        avg_win = sum(t.pnl for t in win_trades) / len(win_trades) if win_trades else 0
        avg_loss = abs(sum(t.pnl for t in lose_trades) / len(lose_trades)) if lose_trades else 1
        profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0

        max_equity = self.params['initial_capital']
        max_drawdown = 0
        for eq in self.daily_equity:
            if eq['equity'] > max_equity:
                max_equity = eq['equity']

            drawdown = (max_equity - eq['equity']) / max_equity * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        returns = []
        for i in range(1, len(self.daily_equity)):
            ret = (self.daily_equity[i]['equity'] - self.daily_equity[i-1]['equity']) / \
                  self.daily_equity[i-1]['equity'] * 100
            returns.append(ret)

        avg_daily_return = sum(returns) / len(returns) if returns else 0
        std_return = (sum((r - avg_daily_return)**2 for r in returns) / len(returns)) ** 0.5 if returns else 1
        sharpe_ratio = (avg_daily_return / std_return * (242**0.5)) if std_return > 0 else 0

        avg_hold_days = sum(t.hold_days for t in sell_trades) / len(sell_trades) if sell_trades else 0

        print(f"\n{'='*95}")
        print(f"【📊 历史回测报告】量化打板选股策略")
        print('='*95)

        print(f"\n{'─'*95}")
        print(f"  【基础信息】")
        print(f"{'─'*95}")
        print(f"  回测期间: {self.daily_equity[0]['date'] if self.daily_equity else 'N/A'} ~ "
              f"{self.daily_equity[-1]['date'] if self.daily_equity else 'N/A'}")
        print(f"  交易日数: {total_days} 天")
        print(f"  初始资金: {self.params['initial_capital']/10000:.2f} 万元")
        print(f"  最终权益: {final_equity/10000:.2f} 万元")
        print(f"  总耗时: {(end_time - start_time).total_seconds():.1f} 秒")

        print(f"\n{'─'*95}")
        print(f"  【收益指标】")
        print(f"{'─'*95}")
        print(f"  总收益率: {total_return:+.2f}%")
        print(f"  年化收益率: {annualized_return:+.2f}%")
        print(f"  最大回撤: {max_drawdown:.2f}%")
        print(f"  夏普比率: {sharpe_ratio:.2f}")

        print(f"\n{'─'*95}")
        print(f"  【交易统计】")
        print(f"{'─'*95}")
        print(f"  总交易次数: {len(sell_trades)} 次")
        print(f"  盈利次数: {len(win_trades)} 次")
        print(f"  亏损次数: {len(lose_trades)} 次")
        print(f"  胜率: {win_rate:.1f}%")
        print(f"  盈亏比: {profit_loss_ratio:.2f}")
        print(f"  平均盈利: {avg_win/10000:.4f} 万元")
        print(f"  平均亏损: {-avg_loss/10000:.4f} 万元")
        print(f"  平均持仓: {avg_hold_days:.1f} 天")

        if sell_trades:
            max_gain = max(t.pnl_pct for t in sell_trades)
            max_loss = min(t.pnl_pct for t in sell_trades)
            print(f"  最大单笔盈利: {max_gain:+.2f}%")
            print(f"  最大单笔亏损: {max_loss:+.2f}%")

        print(f"\n{'─'*95}")
        print(f"  【出场原因统计】")
        print(f"{'─'*95}")
        exit_stats = {}
        for t in sell_trades:
            reason = t.exit_reason
            exit_stats[reason] = exit_stats.get(reason, 0) + 1

        for reason, count in sorted(exit_stats.items(), key=lambda x: -x[1]):
            pct = count / len(sell_trades) * 100
            bar = '█' * int(pct / 5)
            print(f"    {reason:<8}: {count:>3}次 ({pct:>5.1f}%) {bar}")

        if sell_trades:
            print(f"\n{'─'*95}")
            print(f"  【最近10笔交易记录】")
            print(f"{'─'*95}")
            recent_trades = sell_trades[-10:]
            print(f"\n  {'ID':<4} {'代码':<12} {'名称':<8} {'入场价':>7} {'出场价':>7} "
                  f"{'盈亏%':>7} {'持仓天':>5} {'出场原因'}")
            print('  ' + '-' * 85)

            for t in recent_trades:
                name = t.stock_name[:6] if t.stock_name else ''
                entry_price_str = f"{t.entry_price:.2f}" if hasattr(t, 'entry_price') else "N/A"
                print(f"  {t.trade_id:<4} {t.stock_code:<12} {name:<8} "
                      f"{entry_price_str:>7} "
                      f"{t.price:>7.2f} {t.pnl_pct:>+7.2f}% "
                      f"{t.hold_days:>5}天 {t.exit_reason}")

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = Path(__file__).parent / f'backtest_report_{timestamp}.txt'

        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("=" * 90 + "\n")
                f.write(f"量化打板选股策略 - 历史回测报告\n")
                f.write(f"生成时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 90 + "\n\n")

                f.write(f"【收益指标】\n")
                f.write(f"总收益率: {total_return:+.2f}%\n")
                f.write(f"年化收益率: {annualized_return:+.2f}%\n")
                f.write(f"最大回撤: {max_drawdown:.2f}%\n")
                f.write(f"夏普比率: {sharpe_ratio:.2f}\n\n")

                f.write(f"【交易统计】\n")
                f.write(f"总交易次数: {len(sell_trades)}\n")
                f.write(f"胜率: {win_rate:.1f}%\n")
                f.write(f"盈亏比: {profit_loss_ratio:.2f}\n\n")

                f.write(f"【所有交易记录】\n")
                for t in self.trade_records:
                    f.write(f"{t.datetime} | {t.action.value} | {t.stock_code} | "
                           f"价格:{t.price:.2f} | 数量:{t.volume} | "
                           f"盈亏:{t.pnl/10000:.4f}万 ({t.pnl_pct:+.2f}%)\n")

            print(f"\n💾 报告已保存: {report_file.name}")

        except Exception as e:
            print(f"\n⚠️ 保存失败: {e}")

        print(f"\n{'='*95}")


def main():
    engine = BacktestEngine()

    test_stocks = [
        '000001.SZ', '000002.SZ', '000006.SZ', '000021.SZ', '000404.SZ',
        '000417.SZ', '000543.SZ', '000559.SZ', '000571.SZ', '000620.SZ',
        '000636.SZ', '601318.SH', '600036.SH', '600519.SH', '000858.SZ'
    ]

    try:
        print("\n[初始化] 连接TQ接口...")
        tq.initialize(path=os.path.abspath(__file__))
        print(f"  → TQ连接成功! run_id={tq.run_id}")

        engine.run_backtest(
            stock_list=test_stocks,
            days_back=250
        )

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
