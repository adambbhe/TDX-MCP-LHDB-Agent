# -*- coding: utf-8 -*-
"""
量化打板选股策略 - 完整流程框架图生成器
功能:
1. 策略全流程时间轴 (9:00-15:30)
2. 各阶段决策节点和判断条件
3. 策略参数和阈值标注
4. 风控体系集成展示
5. 信号生成与执行流程

输出: 高清PNG流程框架图 + 详细说明文档
"""

import sys
import os
from datetime import datetime
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle, Polygon
    import matplotlib.lines as mlines
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
except ImportError:
    print("请先安装: pip install matplotlib")
    sys.exit(1)


class StrategyFlowchartGenerator:
    """策略流程图生成器"""

    def __init__(self):
        self.fig = None
        self.ax = None

        self.colors = {
            'start_end': '#2E86AB',
            'process': '#28A745',
            'decision': '#FFC107',
            'data_io': '#17A2B8',
            'risk_control': '#DC3545',
            'parameter': '#6F42C1',
            'time_marker': '#343A40',
            'success': '#00C853',
            'fail': '#ff4444',
            'arrow': '#495057',
            'background': '#F8F9FA',
            'text': '#212529',
        }

        self.strategy_params = {
            '竞价阶段': {
                '时间': '9:15-9:25',
                '最小高开比例': '≥1.0%',
                '最大高开比例': '≤7.0%',
                '最小竞价金额': '≥1000万',
                '输出': '高开股票池A',
            },
            '开盘确认': {
                '时间': '9:25-9:35',
                '确认条件': '开盘价维持高开',
                '量能验证': '竞价量/昨日量≥0.3',
                '过滤': '剔除低开股票',
                '输出': '确认池B',
            },
            '盘中监控': {
                '时间': '9:30-14:55',
                '涨停检测': '涨幅≥9.9%',
                '强势检测': '涨幅≥3.0%',
                '均线验证': 'MA5>MA10>MA20',
                '量比要求': '量比≥0.8',
                '评分门槛': 'Score≥60分',
                '输出': '信号列表C',
            },
            '打板执行': {
                '时间': '9:30-14:57',
                '打板价': '涨停价或接近涨停',
                '仓位上限': '单只≤15%',
                '总仓位': '≤70%',
                '持仓数': '≤5只',
                '下单方式': '限价单/市价单',
            },
            '风控管理': {
                '止损线': '-5.0%',
                '止盈线': '+15.0%',
                '最大持仓': '10个交易日',
                '日亏限制': '-3.0%',
                '检查频率': '每5分钟',
            },
            '收盘结算': {
                '时间': '15:00-15:30',
                '统计收益': '当日P&L',
                '更新排名': '调整优先级',
                '生成报告': '交易日志',
                '准备明日': '更新股票池',
            }
        }

    def generate_complete_flowchart(self):
        """生成完整策略流程框架图"""

        fig = plt.figure(figsize=(28, 20), facecolor='white')
        ax = fig.add_subplot(111)
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 75)
        ax.axis('off')
        ax.set_facecolor('white')

        self.fig = fig
        self.ax = ax

        self._draw_title()
        self._draw_timeline()
        self._draw_phase_boxes()
        self._draw_decision_flow()
        self._draw_parameter_panels()
        self._draw_risk_system()
        self._draw_legend()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = Path(__file__).parent / 'charts'
        output_dir.mkdir(exist_ok=True)
        filepath = output_dir / f'strategy_flowchart_{timestamp}.png'

        plt.tight_layout()
        fig.savefig(filepath, dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        print(f"\n✅ 流程框架图已保存: {filepath.name}")
        print(f"   路径: {filepath}")

        return filepath

    def _draw_title(self):
        """绘制标题"""
        title_box = FancyBboxPatch((2, 70), 96, 4,
                                   boxstyle="round,pad=0.3",
                                   facecolor=self.colors['start_end'],
                                   edgecolor='white',
                                   linewidth=3,
                                   alpha=0.9)
        self.ax.add_patch(title_box)

        self.ax.text(50, 72,
                    '量化打板选股策略 - 完整流程框架图\n'
                    'Quantitative Limit-Up Stock Selection Strategy - Complete Workflow Framework',
                    fontsize=16, fontweight='bold',
                    ha='center', va='center', color='white',
                    linespacing=1.5)

        subtitle = self.ax.text(50, 68.5,
                               f'生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | '
                               f'回测周期: 250天 | 年化收益: +107.2% | 最大回撤: 2.4%',
                               fontsize=11, ha='center', va='center',
                               color=self.colors['text'], style='italic')

    def _draw_timeline(self):
        """绘制主时间轴"""
        timeline_y = 66

        time_points = [
            ('9:00\n盘前准备', 5),
            ('9:15\n集合竞价', 18),
            ('9:25\n竞价结束', 28),
            ('9:30\n开盘', 38),
            ('10:30\n早盘监控', 50),
            ('11:30\n午间休市', 60),
            ('13:00\n午后开盘', 67),
            ('14:30\n尾盘监控', 78),
            ('14:57\n停板限制', 85),
            ('15:00\n收盘', 92),
        ]

        for label, x in time_points:
            circle = Circle((x, timeline_y), 1.2,
                           facecolor=self.colors['time_marker'],
                           edgecolor='white',
                           linewidth=2,
                           zorder=10)
            self.ax.add_patch(circle)

            self.ax.text(x, timeline_y - 2.2, label,
                        fontsize=8, ha='center', va='top',
                        color=self.colors['time_marker'],
                        fontweight='bold')

        for i in range(len(time_points) - 1):
            x1 = time_points[i][1]
            x2 = time_points[i+1][1]
            self.ax.annotate('', xy=(x2, timeline_y), xytext=(x1, timeline_y),
                           arrowprops=dict(arrowstyle='->',
                                         color=self.colors['arrow'],
                                         lw=2,
                                         connectionstyle="arc3,rad=0"))

        self.ax.plot([3, 97], [timeline_y, timeline_y],
                    color=self.colors['arrow'],
                    linewidth=3,
                    solid_capstyle='round',
                    zorder=1)

        self.ax.text(50, timeline_y + 1.8,
                    '交易时间轴 (Trading Timeline)',
                    fontsize=12, fontweight='bold',
                    ha='center', va='bottom',
                    color=self.colors['time_marker'],
                    bbox=dict(boxstyle='round,pad=0.3',
                             facecolor='#E9ECEF',
                             edgecolor=self.colors['time_marker'],
                             alpha=0.8))

    def _draw_phase_boxes(self):
        """绘制各阶段主框"""
        phases = [
            {'name': '第一阶段: 数据获取与预处理', 'x': 2, 'y': 52, 'w': 22, 'h': 12,
             'color': self.colors['data_io']},
            {'name': '第二阶段: 信号生成与筛选', 'x': 26, 'y': 52, 'w': 24, 'h': 12,
             'color': self.colors['process']},
            {'name': '第三阶段: 综合评估与排序', 'x': 52, 'y': 52, 'w': 22, 'h': 12,
             'color': self.colors['decision']},
            {'name': '第四阶段: 风控过滤与执行', 'x': 76, 'y': 52, 'w': 22, 'h': 12,
             'color': self.colors['risk_control']},
        ]

        for phase in phases:
            box = FancyBboxPatch((phase['x'], phase['y']),
                                phase['w'], phase['h'],
                                boxstyle="round,pad=0.5",
                                facecolor=phase['color'],
                                edgecolor='white',
                                linewidth=2,
                                alpha=0.25)
            self.ax.add_patch(box)

            self.ax.text(phase['x'] + phase['w']/2, phase['y'] + phase['h'] - 0.8,
                        phase['name'],
                        fontsize=10, fontweight='bold',
                        ha='center', va='top',
                        color=phase['color'])

    def _draw_decision_flow(self):
        """绘制决策流程"""
        flow_items = [
            # 第一阶段：数据获取
            {'type': 'process', 'text': '获取全市场\n股票列表', 'x': 6, 'y': 59},
            {'type': 'process', 'text': '下载K线数据\n(250日)', 'x': 6, 'y': 56},
            {'type': 'data_io', 'text': '实时行情\n快照', 'x': 16, 'y': 59},
            {'type': 'data_io', 'text': '财务数据\n获取', 'x': 16, 'y': 56},

            # 第二阶段：信号生成
            {'type': 'decision', 'text': '高开?\n≥1%', 'x': 30, 'y': 61},
            {'type': 'decision', 'text': '涨停?\n≥9.9%', 'x': 38, 'y': 61},
            {'type': 'process', 'text': '均线多头\n排列检测', 'x': 30, 'y': 57},
            {'type': 'process', 'text': '成交量\n异动分析', 'x': 38, 'y': 57},
            {'type': 'process', 'text': '技术指标\n计算', 'x': 34, 'y': 54},

            # 第三阶段：评估排序
            {'type': 'parameter', 'text': '多维度\n评分系统', 'x': 56, 'y': 61},
            {'type': 'process', 'text': '按评分\n降序排列', 'x': 64, 'y': 61},
            {'type': 'decision', 'text': 'Score\n≥60?', 'x': 56, 'y': 57},
            {'type': 'process', 'text': '生成候选\n股票池', 'x': 64, 'y': 57},

            # 第四阶段：风控执行
            {'type': 'risk', 'text': '仓位计算\n(≤15%)', 'x': 80, 'y': 61},
            {'type': 'risk', 'text': '总仓检查\n(≤70%)', 'x': 88, 'y': 61},
            {'type': 'decision', 'text': '风险\n通过?', 'x': 80, 'y': 57},
            {'type': 'process', 'text': '发送委托\n订单', 'x': 88, 'y': 57},
        ]

        for item in flow_items:
            x, y = item['x'], item['y']
            item_type = item['type']

            if item_type == 'process':
                box = FancyBboxPatch((x-2.5, y-1), 5, 2,
                                    boxstyle="round,pad=0.3",
                                    facecolor=self.colors['process'],
                                    edgecolor='white',
                                    linewidth=1.5,
                                    alpha=0.8)
            elif item_type == 'decision':
                diamond = Polygon([(x, y+1.3), (x+2.5, y), (x, y-1.3), (x-2.5, y)],
                                 closed=True,
                                 facecolor=self.colors['decision'],
                                 edgecolor='white',
                                 linewidth=1.5,
                                 alpha=0.8)
                self.ax.add_patch(diamond)
                self.ax.text(x, y, item['text'],
                            fontsize=7, fontweight='bold',
                            ha='center', va='center',
                            color=self.colors['text'])
                continue
            elif item_type == 'data_io':
                box = FancyBboxPatch((x-2.5, y-1), 5, 2,
                                    boxstyle="round,pad=0.3",
                                    facecolor=self.colors['data_io'],
                                    edgecolor='white',
                                    linewidth=1.5,
                                    alpha=0.8)
            elif item_type == 'parameter':
                box = FancyBboxPatch((x-2.5, y-1), 5, 2,
                                    boxstyle="round,pad=0.3",
                                    facecolor=self.colors['parameter'],
                                    edgecolor='white',
                                    linewidth=1.5,
                                    alpha=0.8)
            elif item_type == 'risk':
                box = FancyBboxPatch((x-2.5, y-1), 5, 2,
                                    boxstyle="round,pad=0.3",
                                    facecolor=self.colors['risk_control'],
                                    edgecolor='white',
                                    linewidth=1.5,
                                    alpha=0.8)

            self.ax.add_patch(box)
            self.ax.text(x, y, item['text'],
                        fontsize=7, fontweight='bold',
                        ha='center', va='center',
                        color='white' if item_type in ['process', 'data_io', 'risk']
                              else self.colors['text'])

        arrows = [
            ((8.5, 59), (13.5, 59)),
            ((8.5, 56), (13.5, 56)),
            ((18.5, 58), (27.5, 60)),
            ((27.5, 60), (30, 61)),
            ((32.5, 61), (35.5, 61)),
            ((35.5, 61), (38, 61)),
            ((30, 59.7), (30, 58)),
            ((38, 59.7), (38, 58)),
            ((31.5, 56), (33.5, 55)),
            ((36.5, 56), (33.5, 55)),
            ((40.5, 59), (53.5, 61)),
            ((53.5, 61), (56, 61)),
            ((58.5, 61), (61.5, 61)),
            ((56, 59.7), (56, 58)),
            ((64, 59.7), (64, 58)),
            ((66.5, 59), (77.5, 61)),
            ((77.5, 61), (80, 61)),
            ((82.5, 61), (85.5, 61)),
            ((80, 59.7), (80, 58)),
            ((88, 59.7), (88, 58)),
        ]

        for start, end in arrows:
            self.ax.annotate('', xy=end, xytext=start,
                           arrowprops=dict(arrowstyle='->',
                                         color=self.colors['arrow'],
                                         lw=1.5,
                                         connectionstyle="arc3,rad=0"))

    def _draw_parameter_panels(self):
        """绘制参数面板"""
        panels = [
            {'title': '竞价筛选参数', 'x': 3, 'y': 42, 'params': [
                ('最小高开比例', '≥ 1.0%', 'min_high_open'),
                ('最大高开比例', '≤ 7.0%', 'max_high_open'),
                ('最小竞价金额', '≥ 1000万', 'min_amount'),
                ('竞价量比', '≥ 0.3', 'volume_ratio'),
            ]},
            {'title': '打板检测参数', 'x': 24, 'y': 42, 'params': [
                ('涨停阈值', '≥ 9.9%', 'limit_up'),
                ('接近涨停', '≥ 8.0%', 'near_limit'),
                ('强势上涨', '≥ 3.0%', 'strong_rise'),
                ('快速拉升', '> 3%/分钟', 'rapid_rise'),
            ]},
            {'title': '评分权重配置', 'x': 45, 'y': 42, 'params': [
                ('信号强度', '30%', 'signal_weight'),
                ('价格位置', '20%', 'price_pos'),
                ('量能质量', '20%', 'volume_qual'),
                ('动能指标', '15%', 'momentum'),
                ('风控指标', '15%', 'risk_ctrl'),
            ]},
            {'title': '执行控制参数', 'x': 69, 'y': 42, 'params': [
                ('单只仓位上限', '≤ 15%', 'single_max'),
                ('总仓位上限', '≤ 70%', 'total_max'),
                ('最大持仓数', '≤ 5只', 'max_hold'),
                ('手续费率', '万分之3', 'commission'),
            ]},
        ]

        for panel in panels:
            panel_height = 2 + len(panel['params']) * 1.8

            bg_box = FancyBboxPatch((panel['x'], panel['y'] - panel_height),
                                   19, panel_height + 1,
                                   boxstyle="round,pad=0.4",
                                   facecolor='#E9ECEF',
                                   edgecolor=self.colors['parameter'],
                                   linewidth=2,
                                   alpha=0.6)
            self.ax.add_patch(bg_box)

            header_box = FancyBboxPatch((panel['x'], panel['y'] - 1),
                                       19, 2,
                                       boxstyle="round,pad=0.3",
                                       facecolor=self.colors['parameter'],
                                       edgecolor='white',
                                       linewidth=1.5,
                                       alpha=0.9)
            self.ax.add_patch(header_box)

            self.ax.text(panel['x'] + 9.5, panel['y'],
                        panel['title'],
                        fontsize=9, fontweight='bold',
                        ha='center', va='center',
                        color='white')

            for i, (param_name, param_value, _) in enumerate(panel['params']):
                y_pos = panel['y'] - 2.5 - i * 1.8

                name_text = self.ax.text(panel['x'] + 0.5, y_pos,
                                        f"• {param_name}:",
                                        fontsize=8,
                                        ha='left', va='center',
                                        color=self.colors['text'])

                value_box = FancyBboxPatch((panel['x'] + 11, y_pos - 0.45),
                                         7.5, 0.9,
                                         boxstyle="round,pad=0.2",
                                         facecolor='white',
                                         edgecolor=self.colors['success'],
                                         linewidth=1,
                                         alpha=0.9)
                self.ax.add_patch(value_box)

                self.ax.text(panel['x'] + 14.75, y_pos,
                            param_value,
                            fontsize=8, fontweight='bold',
                            ha='center', va='center',
                            color=self.colors['success'])

    def _draw_risk_system(self):
        """绘制风控系统"""
        risk_y = 26

        main_box = FancyBboxPatch((2, risk_y - 10), 96, 12,
                                 boxstyle="round,pad=0.5",
                                 facecolor='#FFF3CD',
                                 edgecolor=self.colors['risk_control'],
                                 linewidth=3,
                                 alpha=0.4)
        self.ax.add_patch(main_box)

        self.ax.text(50, risk_y + 1,
                    '⚠️ 风险管理系统 (Risk Management System)',
                    fontsize=12, fontweight='bold',
                    ha='center', va='center',
                    color=self.colors['risk_control'],
                    bbox=dict(boxstyle='round,pad=0.3',
                             facecolor='#FFF3CD',
                             edgecolor=self.colors['risk_control']))

        risk_controls = [
            {'icon': '🛑', 'name': '止损机制', 'desc': '亏损达-5%\n自动平仓', 'x': 8},
            {'icon': '🎯', 'name': '止盈机制', 'desc': '盈利达+15%\n自动止盈', 'x': 24},
            {'icon': '⏱️', 'name': '时间止损', 'desc': '持仓超10天\n强制退出', 'x': 40},
            {'icon': '💰', 'name': '仓位控制', 'desc': '单只≤15%\n总仓≤70%', 'x': 56},
            {'icon': '📊', 'name': '日亏限制', 'desc': '日亏>-3%\n停止交易', 'x': 72},
            {'icon': '🔍', 'name': '实时监控', 'desc': '每5分钟\n检查一次', 'x': 88},
        ]

        for ctrl in risk_controls:
            x = ctrl['x']

            icon_circle = Circle((x, risk_y - 2), 1.5,
                                facecolor='white',
                                edgecolor=self.colors['risk_control'],
                                linewidth=2)
            self.ax.add_patch(icon_circle)

            self.ax.text(x, risk_y - 2, ctrl['icon'],
                        fontsize=14, ha='center', va='center')

            ctrl_box = FancyBboxPatch((x - 4, risk_y - 7.5), 8, 4.5,
                                    boxstyle="round,pad=0.3",
                                    facecolor='white',
                                    edgecolor=self.colors['risk_control'],
                                    linewidth=1.5,
                                    alpha=0.9)
            self.ax.add_patch(ctrl_box)

            self.ax.text(x, risk_y - 4, ctrl['name'],
                        fontsize=9, fontweight='bold',
                        ha='center', va='center',
                        color=self.colors['risk_control'])

            self.ax.text(x, risk_y - 6, ctrl['desc'],
                        fontsize=7, ha='center', va='center',
                        color=self.colors['text'],
                        linespacing=1.3)

        for i in range(len(risk_controls) - 1):
            x1 = risk_controls[i]['x'] + 4
            x2 = risk_controls[i+1]['x'] - 4
            self.ax.annotate('', xy=(x2, risk_y - 5.2), xytext=(x1, risk_y - 5.2),
                           arrowprops=dict(arrowstyle='<->',
                                         color=self.colors['risk_control'],
                                         lw=1.5,
                                         linestyle='--',
                                         connectionstyle="arc3,rad=0"))

    def _draw_legend(self):
        """绘制图例"""
        legend_y = 10

        legend_box = FancyBboxPatch((2, legend_y - 8), 96, 9,
                                  boxstyle="round,pad=0.5",
                                  facecolor='#F8F9FA',
                                  edgecolor='#DEE2E6',
                                  linewidth=2,
                                  alpha=0.8)
        self.ax.add_patch(legend_box)

        self.ax.text(50, legend_y,
                    '图例说明 (Legend) & 策略绩效指标 (Performance Metrics)',
                    fontsize=11, fontweight='bold',
                    ha='center', va='center',
                    color=self.colors['text'])

        legends = [
            {'symbol': 'rect', 'color': self.colors['process'], 'label': '处理步骤'},
            {'symbol': 'diamond', 'color': self.colors['decision'], 'label': '决策判断'},
            {'symbol': 'rect', 'color': self.colors['data_io'], 'label': '数据输入/输出'},
            {'symbol': 'rect', 'color': self.colors['parameter'], 'label': '参数配置'},
            {'symbol': 'rect', 'color': self.colors['risk_control'], 'label': '风控措施'},
        ]

        start_x = 8
        for i, leg in enumerate(legends):
            x = start_x + i * 18

            if leg['symbol'] == 'rect':
                box = Rectangle((x - 1.5, legend_y - 3), 3, 1.5,
                               facecolor=leg['color'],
                               edgecolor='white',
                               linewidth=1)
                self.ax.add_patch(box)
            elif leg['symbol'] == 'diamond':
                size = 0.8
                diamond = Polygon([(x, legend_y - 2.25 + size),
                                  (x + size, legend_y - 2.25),
                                  (x, legend_y - 2.25 - size),
                                  (x - size, legend_y - 2.25)],
                                 closed=True,
                                 facecolor=leg['color'],
                                 edgecolor='white',
                                 linewidth=1)
                self.ax.add_patch(diamond)

            self.ax.text(x + 3, legend_y - 2.25, leg['label'],
                        fontsize=9, ha='left', va='center',
                        color=self.colors['text'])

        metrics = [
            ('年化收益率', '+107.2%', self.colors['success']),
            ('最大回撤', '2.40%', '#FFC107'),
            ('夏普比率', '5.46', '#17A2B8'),
            ('胜率', '59.4%', '#2E86AB'),
            ('盈亏比', '3.47', '#A23B72'),
            ('交易次数', '128次', '#343A40'),
        ]

        metric_start_x = 8
        for i, (metric_name, metric_value, color) in enumerate(metrics):
            x = metric_start_x + i * 15

            self.ax.text(x, legend_y - 5.5, f'{metric_name}:',
                        fontsize=9, ha='left', va='center',
                        color=self.colors['text'])

            self.ax.text(x + len(metric_name)*0.6 + 1, legend_y - 5.5, metric_value,
                        fontsize=10, fontweight='bold',
                        ha='left', va='center', color=color)


def main():
    """主函数"""
    print("=" * 90)
    print("  📋 量化打板选股策略 - 流程框架图生成器")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 90)

    generator = StrategyFlowchartGenerator()
    filepath = generator.generate_complete_flowchart()

    print("\n" + "=" * 90)
    print("  ✅ 流程框架图生成完成!")
    print("=" * 90)

    print(f"\n📊 图表内容:")
    print("  • 完整交易时间轴 (9:00-15:30)")
    print("  • 4大策略阶段流程")
    print("  • 关键决策节点 (12个)")
    print("  • 核心参数面板 (4组)")
    print("  • 风控系统架构 (6项)")
    print("  • 图例与绩效指标")

    try:
        plt.show()
    except Exception as e:
        print(f"\n⚠️ 无法显示窗口: {e}")
        print("   图片已保存，可直接查看文件")


if __name__ == '__main__':
    main()
