# -*- coding: utf-8 -*-
"""
量化打板选股策略 - 可视化分析系统
功能:
1. 资金曲线图 (权益变化趋势)
2. 收益分布直方图 (交易盈亏分布)
3. 月度收益柱状图
4. 持仓天数分布图
5. 出场原因饼图
6. 累计收益曲线 vs 基准对比
7. 回撤分析图
8. 综合仪表板 Dashboard

输出: 高质量PNG图片 + 屏幕显示
"""

import sys
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.gridspec import GridSpec
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
except ImportError:
    print("请先安装matplotlib: pip install matplotlib")
    sys.exit(1)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from strategy_backtest import BacktestEngine


class StrategyVisualizer:
    """策略可视化分析器"""

    def __init__(self):
        self.engine = BacktestEngine()
        self.figures = []

        self.colors = {
            'primary': '#2E86AB',
            'secondary': '#A23B72',
            'success': '#28A745',
            'danger': '#DC3545',
            'warning': '#FFC107',
            'info': '#17A2B8',
            'dark': '#343A40',
            'light': '#F8F9FA',
            'profit': '#00C853',
            'loss': '#ff4444',
        }

    def run_and_visualize(self, stock_list=None, days_back=250):
        """运行回测并生成可视化"""
        print("=" * 90)
        print("  📊 量化打板选股策略 - 可视化分析系统")
        print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 90)

        if stock_list is None:
            stock_list = [
                '000001.SZ', '000002.SZ', '000006.SZ', '000021.SZ', '000404.SZ',
                '000417.SZ', '000543.SZ', '000559.SZ', '000571.SZ', '000620.SZ',
                '000636.SZ', '601318.SH', '600036.SH', '600519.SH', '000858.SZ'
            ]

        try:
            from tqcenter import tq
            print("\n[初始化] 连接TQ接口...")
            tq.initialize(path=os.path.abspath(__file__))
            print(f"  → TQ连接成功!")

            self.engine.run_backtest(stock_list=stock_list, days_back=days_back)

            if not self.engine.daily_equity:
                print("\n❌ 无回测数据")
                return

            self._generate_all_charts()

        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
        finally:
            try:
                from tqcenter import tq
                tq.close()
                print("\n[TQ连接已关闭]")
            except:
                pass

    def _generate_all_charts(self):
        """生成所有图表"""
        print(f"\n{'='*90}")
        print(f"[可视化] 开始生成图表...")
        print('='*90)

        self._create_dashboard()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = Path(__file__).parent / 'charts'
        output_dir.mkdir(exist_ok=True)

        for i, fig in enumerate(self.figures):
            filename = f'strategy_chart_{i+1}_{timestamp}.png'
            filepath = output_dir / filename
            fig.savefig(filepath, dpi=300, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            print(f"  ✅ 图表{i+1}已保存: {filename}")

        print(f"\n💾 所有图表已保存到: {output_dir}/")

        plt.show()

    def _create_dashboard(self):
        """创建综合仪表板"""
        fig = plt.figure(figsize=(20, 14))
        gs = GridSpec(3, 3, figure=fig, hspace=0.35, wspace=0.3)

        ax1 = fig.add_subplot(gs[0, :2])
        self._plot_equity_curve(ax1)

        ax2 = fig.add_subplot(gs[0, 2])
        self._plot_performance_summary(ax2)

        ax3 = fig.add_subplot(gs[1, 0])
        self._plot_pnl_distribution(ax3)

        ax4 = fig.add_subplot(gs[1, 1])
        self._plot_monthly_returns(ax4)

        ax5 = fig.add_subplot(gs[1, 2])
        self._plot_exit_reasons(ax5)

        ax6 = fig.add_subplot(gs[2, 0])
        self._plot_hold_days_distribution(ax6)

        ax7 = fig.add_subplot(gs[2, 1])
        self._plot_drawdown(ax7)

        ax8 = fig.add_subplot(gs[2, 2])
        self._plot_trade_statistics(ax8)

        fig.suptitle('量化打板选股策略 - 综合分析仪表板\n'
                    f'回测期间: {self.engine.daily_equity[0]["date"]} ~ '
                    f'{self.engine.daily_equity[-1]["date"]}',
                    fontsize=16, fontweight='bold', y=0.98)

        self.figures.append(fig)

    def _plot_equity_curve(self, ax):
        """资金曲线图"""
        dates = [datetime.strptime(d['date'], '%Y-%m-%d') for d in self.engine.daily_equity]
        equity = [d['equity'] / 10000 for d in self.engine.daily_equity]
        initial = self.engine.params['initial_capital'] / 10000

        ax.fill_between(dates, equity, initial,
                        where=[e >= initial for e in equity],
                        color=self.colors['success'], alpha=0.3, label='盈利区间')
        ax.fill_between(dates, equity, initial,
                        where=[e < initial for e in equity],
                        color=self.colors['danger'], alpha=0.3, label='亏损区间')

        ax.plot(dates, equity, color=self.colors['primary'],
               linewidth=2, label='权益曲线')
        ax.axhline(y=initial, color=self.colors['dark'],
                  linestyle='--', alpha=0.7, label=f'初始资金 ({initial:.0f}万)')

        final_equity = equity[-1]
        total_return = (final_equity - initial) / initial * 100

        ax.annotate(f'最终: {final_equity:.2f}万\n收益率: {total_return:+.1f}%',
                   xy=(dates[-1], final_equity),
                   xytext=(10, 10), textcoords='offset points',
                   fontsize=10, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                   arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

        ax.set_title('📈 资金曲线 (Equity Curve)', fontsize=12, fontweight='bold')
        ax.set_xlabel('日期', fontsize=10)
        ax.set_ylabel('权益 (万元)', fontsize=10)
        ax.legend(loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    def _plot_performance_summary(self, ax):
        """绩效指标摘要卡片"""
        sell_trades = [t for t in self.engine.trade_records if t.action.value == "卖出"]
        win_trades = [t for t in sell_trades if t.pnl > 0]
        lose_trades = [t for t in sell_trades if t.pnl <= 0]

        final_equity = self.engine.daily_equity[-1]['equity']
        total_return = (final_equity - self.engine.params['initial_capital']) / \
                      self.engine.params['initial_capital'] * 100

        win_rate = len(win_trades) / len(sell_trades) * 100 if sell_trades else 0
        avg_win = np.mean([t.pnl_pct for t in win_trades]) if win_trades else 0
        avg_loss = np.mean([t.pnl_pct for t in lose_trades]) if lose_trades else 0
        profit_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0

        max_dd = 0
        peak = self.engine.params['initial_capital']
        for eq in self.engine.daily_equity:
            if eq['equity'] > peak:
                peak = eq['equity']
            dd = (peak - eq['equity']) / peak * 100
            if dd > max_dd:
                max_dd = dd

        metrics = [
            ('总收益率', f'{total_return:+.1f}%', self.colors['success'] if total_return > 0 else self.colors['danger']),
            ('年化收益', f'{total_return * 242 / len(self.engine.daily_equity):+.1f}%', self.colors['primary']),
            ('最大回撤', f'{max_dd:.1f}%', self.colors['warning']),
            ('胜率', f'{win_rate:.1f}%', self.colors['info']),
            ('盈亏比', f'{profit_loss_ratio:.2f}', self.colors['secondary']),
            ('交易次数', f'{len(sell_trades)}次', self.colors['dark']),
        ]

        ax.axis('off')

        y_pos = 0.95
        ax.text(0.5, y_pos, '📊 核心指标', fontsize=13, fontweight='bold',
               transform=ax.transAxes, ha='center', va='top')

        y_pos -= 0.08
        for i, (label, value, color) in enumerate(metrics):
            box_color = '#E8F5E9' if i % 2 == 0 else '#FFF3E0'
            rect = plt.Rectangle((0.05, y_pos - 0.06), 0.9, 0.11,
                                 transform=ax.transAxes,
                                 facecolor=box_color, edgecolor=color,
                                 linewidth=2, alpha=0.8)
            ax.add_patch(rect)

            ax.text(0.1, y_pos - 0.01, label, fontsize=11, fontweight='bold',
                   transform=ax.transAxes, va='top', color=self.colors['dark'])
            ax.text(0.9, y_pos - 0.01, value, fontsize=12, fontweight='bold',
                   transform=ax.transAxes, ha='right', va='top', color=color)

            y_pos -= 0.125

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

    def _plot_pnl_distribution(self, ax):
        """收益分布直方图"""
        sell_trades = [t for t in self.engine.trade_records if t.action.value == "卖出"]
        pnls = [t.pnl_pct for t in sell_trades]

        bins = np.linspace(-6, 16, 23)
        colors = [self.colors['profit'] if p >= 0 else self.colors['loss'] for p in pnls]

        n, bins_out, patches = ax.hist(pnls, bins=bins, edgecolor='white',
                                       color=self.colors['primary'], alpha=0.7)

        for patch, right_edge in zip(patches, bins_out[1:]):
            if right_edge <= 0:
                patch.set_facecolor(self.colors['loss'])
            else:
                patch.set_facecolor(self.colors['profit'])

        ax.axvline(x=0, color=self.colors['dark'], linestyle='--', linewidth=2, alpha=0.7)
        mean_pnl = np.mean(pnls)
        ax.axvline(x=mean_pnl, color=self.colors['secondary'],
                  linestyle='-', linewidth=2, alpha=0.8,
                  label=f'均值: {mean_pnl:+.2f}%')

        ax.set_title('📊 收益分布 (P&L Distribution)', fontsize=12, fontweight='bold')
        ax.set_xlabel('收益率 (%)', fontsize=10)
        ax.set_ylabel('频次', fontsize=10)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3, axis='y')

    def _plot_monthly_returns(self, ax):
        """月度收益柱状图"""
        monthly_data = {}
        for eq in self.engine.daily_equity:
            date_str = eq['date']
            month_key = date_str[:7]
            if month_key not in monthly_data:
                monthly_data[month_key] = {'start': eq['equity'], 'end': eq['equity']}
            else:
                monthly_data[month_key]['end'] = eq['equity']

        months = sorted(monthly_data.keys())
        monthly_returns = []
        for month in months:
            data = monthly_data[month]
            ret = (data['end'] - data['start']) / data['start'] * 100
            monthly_returns.append(ret)

        colors = [self.colors['profit'] if r >= 0 else self.colors['loss']
                 for r in monthly_returns]

        bars = ax.bar(range(len(months)), monthly_returns, color=colors,
                     edgecolor='white', linewidth=0.5)

        ax.axhline(y=0, color=self.colors['dark'], linestyle='-', linewidth=1.5, alpha=0.7)

        for bar, ret in zip(bars, monthly_returns):
            height = bar.get_height()
            ax.annotate(f'{ret:+.1f}%',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3), textcoords="offset points",
                       ha='center', va='bottom', fontsize=8, fontweight='bold')

        ax.set_title('📅 月度收益 (Monthly Returns)', fontsize=12, fontweight='bold')
        ax.set_xlabel('月份', fontsize=10)
        ax.set_ylabel('收益率 (%)', fontsize=10)
        ax.set_xticks(range(len(months)))
        ax.set_xticklabels([m[5:] for m in months], rotation=45, ha='right', fontsize=8)
        ax.grid(True, alpha=0.3, axis='y')

    def _plot_exit_reasons(self, ax):
        """出场原因饼图"""
        sell_trades = [t for t in self.engine.trade_records if t.action.value == "卖出"]

        exit_counts = {}
        for t in sell_trades:
            reason = t.exit_reason
            exit_counts[reason] = exit_counts.get(reason, 0) + 1

        labels = list(exit_counts.keys())
        sizes = list(exit_counts.values())
        colors_pie = [self.colors['success'], self.colors['info'],
                     self.colors['danger'], self.colors['warning']][:len(labels)]

        explode = [0.03] * len(labels)
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors_pie,
                                          explode=explode, autopct='%1.1f%%',
                                          startangle=90, pctdistance=0.75,
                                          textprops={'fontsize': 9})

        for autotext in autotexts:
            autotext.set_fontweight('bold')

        ax.set_title('🎯 出场原因分布 (Exit Reasons)', fontsize=12, fontweight='bold')

        legend_labels = [f'{l}: {s}次' for l, s in zip(labels, sizes)]
        ax.legend(wedges, legend_labels, loc='lower center',
                 bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=8)

    def _plot_hold_days_distribution(self, ax):
        """持仓天数分布"""
        sell_trades = [t for t in self.engine.trade_records if t.action.value == "卖出"]
        hold_days = [t.hold_days for t in sell_trades]

        unique_days = sorted(set(hold_days))
        day_counts = [hold_days.count(d) for d in unique_days]

        bars = ax.bar(unique_days, day_counts, color=self.colors['info'],
                     edgecolor='white', linewidth=0.5, alpha=0.8)

        max_count = max(day_counts) if day_counts else 1
        for bar, count in zip(bars, day_counts):
            height = bar.get_height()
            ax.annotate(f'{count}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3), textcoords="offset points",
                       ha='center', va='bottom', fontsize=9, fontweight='bold')

        mean_hold = np.mean(hold_days)
        ax.axvline(x=mean_hold, color=self.colors['secondary'],
                  linestyle='--', linewidth=2, alpha=0.8,
                  label=f'平均: {mean_hold:.1f}天')

        ax.set_title('⏱️ 持仓天数分布 (Hold Days)', fontsize=12, fontweight='bold')
        ax.set_xlabel('持仓天数', fontsize=10)
        ax.set_ylabel('交易次数', fontsize=10)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3, axis='y')

    def _plot_drawdown(self, ax):
        """回撤分析图"""
        equity_series = [d['equity'] for d in self.engine.daily_equity]
        dates = [datetime.strptime(d['date'], '%Y-%m-%d') for d in self.engine.daily_equity]

        peak = equity_series[0]
        drawdowns = []
        for eq in equity_series:
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak * 100
            drawdowns.append(dd)

        ax.fill_between(dates, drawdowns, 0,
                        color=self.colors['danger'], alpha=0.5, label='回撤区域')

        ax.plot(dates, drawdowns, color=self.colors['danger'],
               linewidth=1.5, alpha=0.8)

        max_dd_idx = np.argmax(drawdowns)
        max_dd_val = drawdowns[max_dd_idx]
        ax.scatter([dates[max_dd_idx]], [max_dd_val],
                  color=self.colors['danger'], s=100, zorder=5,
                  marker='v', label=f'最大回撤: {max_dd_val:.2f}%')

        ax.fill_between(dates, drawdowns, 0,
                       where=[dd >= -5 for dd in drawdowns],
                       color=self.colors['warning'], alpha=0.3, label='<5%回撤')
        ax.fill_between(dates, drawdowns, 0,
                       where=[dd < -5 for dd in drawdowns],
                       color=self.colors['danger'], alpha=0.5, label='>5%回撤')

        ax.set_title('📉 回撤分析 (Drawdown Analysis)', fontsize=12, fontweight='bold')
        ax.set_xlabel('日期', fontsize=10)
        ax.set_ylabel('回撤 (%)', fontsize=10)
        ax.legend(loc='lower left', fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    def _plot_trade_statistics(self, ax):
        """交易统计信息"""
        sell_trades = [t for t in self.engine.trade_records if t.action.value == "卖出"]
        win_trades = [t for t in sell_trades if t.pnl > 0]
        lose_trades = [t for t in sell_trades if t.pnl <= 0]

        categories = ['总交易', '盈利', '亏损', '胜率', '盈亏比', '平均持仓']
        values = [
            len(sell_trades),
            len(win_trades),
            len(lose_trades),
            f"{len(win_trades)/len(sell_trades)*100:.1f}%" if sell_trades else "N/A",
            f"{abs(np.mean([t.pnl_pct for t in win_trades]) / np.mean([t.pnl_pct for t in lose_trades])):.2f}"
            if lose_trades and win_trades else "N/A",
            f"{np.mean([t.hold_days for t in sell_trades]):.1f}天" if sell_trades else "N/A"
        ]

        colors_stats = [self.colors['primary'], self.colors['success'],
                       self.colors['danger'], self.colors['info'],
                       self.colors['secondary'], self.colors['warning']]

        y_pos = np.arange(len(categories))
        bars = ax.barh(y_pos, [1]*len(categories), color=colors_stats,
                      height=0.6, edgecolor='white', linewidth=2)

        for bar, cat, val in zip(bars, categories, values):
            width = bar.get_width()
            ax.text(width/2, bar.get_y() + bar.get_height()/2,
                   f'{cat}\n{val}', ha='center', va='center',
                   fontsize=10, fontweight='bold', color='white')

        ax.set_xlim(0, 1.5)
        ax.set_yticks([])
        ax.set_xticks([])

        for spine in ax.spines.values():
            spine.set_visible(False)

        ax.set_title('📋 交易统计概览 (Trade Statistics)',
                    fontsize=12, fontweight='bold')


def main():
    visualizer = StrategyVisualizer()
    visualizer.run_and_visualize()


if __name__ == '__main__':
    main()
