# -*- coding: utf-8 -*-
"""
数据接口验证与竞价选股测试脚本
功能：
1. 验证TQ接口可获取的数据字段
2. 获取实时市场数据
3. 测试竞价选股基础条件
4. 输出可用字段清单供策略开发使用

作者: 量化打板策略系统
日期: 2026-05-18
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# 设置控制台编码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ===== DLL路径自动检测 =====
possible_dll_paths = [
    Path(__file__).parent.parent / 'TPythClient.dll',
    Path(__file__).parent / 'TPythClient.dll',
    Path(r'D:\new_tdx64\PYPlugins\TPythClient.dll'),
    Path(r'C:\new_tdx\TPythClient.dll'),
    Path(r'D:\new_tdx\TPythClient.dll'),
    Path(r'C:\TDX\TPythClient.dll'),
]

dll_found = False
actual_dll_path = None

for dll_path in possible_dll_paths:
    if dll_path.exists():
        print(f"[OK] 找到DLL文件: {dll_path}")
        actual_dll_path = dll_path
        dll_found = True
        break

if not dll_found:
    print("\n[WARN] 未找到 TPythClient.dll 文件!")
    print("\n请确认:")
    print("1. 通达信软件是否已正确安装")
    print("2. DLL文件是否已复制到以下任一位置:")

    for i, path in enumerate(possible_dll_paths, 1):
        print(f"   {i}. {path}")

    user_input = input("\n是否要手动指定DLL路径? (y/n): ").strip().lower()
    if user_input == 'y':
        custom_path = input("请输入完整的DLL文件路径: ").strip()
        if os.path.exists(custom_path):
            actual_dll_path = Path(custom_path)
            dll_found = True
            print(f"\n[OK] 使用自定义路径: {actual_dll_path}")
        else:
            print(f"\n[ERROR] 路径不存在: {custom_path}")
            sys.exit(1)
    else:
        print("\n[ERROR] 无法继续测试,程序退出")
        sys.exit(1)

if dll_found and actual_dll_path != Path(__file__).parent.parent / 'TPythClient.dll':
    print(f"\n[INFO] 检测到DLL在: {actual_dll_path}")
    print("正在临时修改tqcenter模块...")

    original_file = Path(__file__).parent / "tqcenter.py"
    temp_file = Path(__file__).parent / "tqcenter_auto_test.py"

    with open(original_file, 'r', encoding='utf-8') as f:
        content = f.read()

    modified_content = content.replace(
        "global_dll_path = Path(__file__).resolve().parents[1] / 'TPythClient.dll'",
        f"global_dll_path = Path(r'{actual_dll_path}')"
    )

    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(modified_content)

    sys.path.insert(0, str(Path(__file__).parent))
    from tqcenter_auto_test import tq
else:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from tqcenter import tq


class DataInterfaceValidator:
    """TQ数据接口验证器"""

    def __init__(self):
        self.test_stocks = ['600519.SH', '000001.SZ', '300750.SZ']
        self.results = {}

    def test_connection(self):
        """测试1: 连接初始化"""
        print("=" * 70)
        print("【测试1】TQ连接初始化")
        print("=" * 70)

        try:
            tq.initialize(path=os.path.abspath(__file__))
            print(f"[OK] 连接成功!")
            print(f"   run_id: {tq.run_id}")
            return True
        except Exception as e:
            print(f"[ERROR] 连接失败: {e}")
            return False

    def test_market_snapshot(self):
        """测试2: 实时行情快照 - 关键! 竞价选股依赖此接口"""
        print("\n" + "=" * 70)
        print("【测试2】实时行情快照 (get_market_snapshot)")
        print("=" * 70)
        print("[INFO] 此接口是竞价选股的核心,需要验证返回哪些字段\n")

        snapshot_fields = {}

        for stock in self.test_stocks:
            print(f"获取 {stock} 的实时快照...")
            try:
                data = tq.get_market_snapshot(stock)

                if not data:
                    print(f"   [ERROR] 返回空数据")
                    continue

                print(f"   [OK] 成功获取 {len(data)} 个字段")
                print("\n   字段列表:")

                for key, value in data.items():
                    value_str = str(value)[:50] if len(str(value)) > 50 else str(value)
                    print(f"      - {key}: {value_str}")

                    if key not in snapshot_fields:
                        snapshot_fields[key] = type(value).__name__

                print()

            except Exception as e:
                print(f"   [ERROR] 异常: {e}\n")

        self.results['snapshot_fields'] = snapshot_fields
        print(f"\n汇总: 共发现 {len(snapshot_fields)} 个可用字段")
        for field_name, field_type in sorted(snapshot_fields.items()):
            print(f"      - {field_name} ({field_type})")

        return snapshot_fields

    def test_kline_data(self):
        """测试3: K线数据 - 用于计算均线、涨幅等"""
        print("\n" + "=" * 70)
        print("【测试3】K线历史数据 (get_market_data)")
        print("=" * 70)
        print("[INFO] 用于计算MA5/MA10支撑、近5日涨幅等条件\n")

        kline_fields = {}

        for stock in self.test_stocks[:1]:
            print(f"获取 {stock} 最近20个交易日K线...")

            try:
                data = tq.get_market_data(
                    stock_list=[stock],
                    period='1d',
                    count=20,
                    dividend_type='none'
                )

                if not data or stock not in data:
                    print(f"   [ERROR] 返回空数据")
                    continue

                stock_data = data[stock]
                print(f"   [OK] 成功获取K线数据")
                print(f"\n   数据维度: {len(stock_data)} 条记录")

                if hasattr(stock_data, 'columns'):
                    print(f"   字段列表:")
                    for col in stock_data.columns:
                        print(f"      - {col}")
                        kline_fields[col] = str(stock_data[col].dtype)

                    print(f"\n   最新5条数据:")
                    print(stock_data.tail().to_string())

            except Exception as e:
                print(f"   [ERROR] 异常: {e}\n")
                import traceback
                traceback.print_exc()

        self.results['kline_fields'] = kline_fields
        return kline_fields

    def test_financial_data(self):
        """测试4: 财务数据 - 流通市值等关键指标"""
        print("\n" + "=" * 70)
        print("【测试4】财务数据 (get_financial_data)")
        print("=" * 70)
        print("[INFO] 用于流通市值筛选(30-280亿)\n")

        financial_fields = {}
        test_fields = ['流通市值', '总市值', '总股本', '上市日期']

        for stock in self.test_stocks[:2]:
            print(f"获取 {stock} 的财务数据...")

            try:
                data = tq.get_financial_data(
                    stock_list=[stock],
                    field_list=test_fields
                )

                if not data or stock not in data:
                    print(f"   [ERROR] 返回空数据")
                    continue

                df = data[stock]
                print(f"   [OK] 成功获取财务数据")
                print(f"\n   数据预览:")
                print(df.to_string())

                for col in df.columns:
                    financial_fields[col] = str(df[col].dtype)

            except Exception as e:
                print(f"   [ERROR] 异常: {e}\n")

        self.results['financial_fields'] = financial_fields
        return financial_fields

    def test_stock_info(self):
        """测试5: 股票基础信息 - ST过滤、名称等"""
        print("\n" + "=" * 70)
        print("【测试5】股票基础信息 (get_stock_info)")
        print("=" * 70)
        print("[INFO] 用于ST股票排除、股票名称识别\n")

        info_fields = {}

        for stock in self.test_stocks[:2]:
            print(f"获取 {stock} 的基础信息...")

            try:
                data = tq.get_stock_info(stock)

                if not data:
                    print(f"   [ERROR] 返回空数据")
                    continue

                print(f"   [OK] 成功获取基础信息")
                print(f"\n   所有字段:")

                for key, value in data.items():
                    value_str = str(value)[:80] if len(str(value)) > 80 else str(value)
                    print(f"      - {key}: {value_str}")
                    info_fields[key] = type(value).__name__

            except Exception as e:
                print(f"   [ERROR] 异常: {e}\n")

        self.results['info_fields'] = info_fields
        return info_fields

    def test_stock_list(self):
        """测试6: 股票列表 - 全市场扫描"""
        print("\n" + "=" * 70)
        print("【测试6】全市场股票列表 (get_stock_list)")
        print("=" * 70)

        try:
            all_stocks = tq.get_stock_list()
            print(f"[OK] 成功获取全市场股票列表")
            print(f"   总数: {len(all_stocks)} 只")

            sh_count = len([s for s in all_stocks if '.SH' in s])
            sz_count = len([s for s in all_stocks if '.SZ' in s])
            bj_count = len([s for s in all_stocks if '.BJ' in s])

            print(f"\n   分布:")
            print(f"      上海主板(SH): {sh_count} 只")
            print(f"      深圳主板/中小板(SZ): {sz_count} 只")
            print(f"      北京交易所(BJ): {bj_count} 只")

            print(f"\n   示例(前10只):")
            for i, stock in enumerate(all_stocks[:10]):
                print(f"      {i+1}. {stock}")

            self.results['total_stocks'] = len(all_stocks)
            self.results['all_stocks'] = all_stocks[:100]

            return all_stocks

        except Exception as e:
            print(f"[ERROR] 获取失败: {e}")
            return []

    def test_sector_data(self):
        """测试7: 板块数据 - 板块联动分析"""
        print("\n" + "=" * 70)
        print("【测试7】板块数据 (get_sector_list / get_stock_list_in_sector)")
        print("=" * 70)

        try:
            sectors = tq.get_sector_list()
            print(f"[OK] 成功获取板块列表")
            print(f"   板块总数: {len(sectors)}")

            print(f"\n   示例板块(前15个):")
            for i, sector in enumerate(sectors[:15]):
                print(f"      {i+1}. {sector}")

            if sectors:
                test_sector = sectors[0]
                print(f"\n   测试获取 '{test_sector}' 的成分股...")
                stocks_in_sector = tq.get_stock_list_in_sector(test_sector)
                print(f"   [OK] 成功获取成分股: {len(stocks_in_sector)} 只")

                if stocks_in_sector:
                    print(f"   前5只: {stocks_in_sector[:5]}")

        except Exception as e:
            print(f"[ERROR] 获取失败: {e}")


class AuctionStockSelector:
    """竞价选股器 - 基于实际可用字段实现"""

    def __init__(self, available_fields):
        self.fields = available_fields
        self.selected_stocks = []

        # 策略参数
        self.params = {
            'market_cap_min': 30,
            'market_cap_max': 280,
            'high_open_min': 3.2,
            'high_open_max': 5.8,
            'max_5day_rise': 25,
            'min_volume_ratio': 5.5,
        }

    def calculate_high_open_rate(self, snapshot_data):
        """
        计算高开幅度%
        根据实际可用字段动态选择计算方式
        """
        open_price = None
        prev_close = None

        possible_open = ['Open', '开盘价', 'OpenPrice', 'open', '最新价', 'Last', 'Close']
        possible_prev = ['PreClose', '昨收', 'PrevClose', 'preclose']

        for field in possible_open:
            if field in snapshot_data:
                open_price = float(snapshot_data[field])
                break

        for field in possible_prev:
            if field in snapshot_data:
                prev_close = float(snapshot_data[field])
                break

        if open_price and prev_close and prev_close > 0:
            high_open = (open_price / prev_close - 1) * 100
            return round(high_open, 2), True
        else:
            return 0, False

    def check_basic_filter(self, stock_code, stock_info=None):
        """
        基础条件过滤
        1. 排除ST/*ST
        2. 流通市值范围
        3. 上市天数>250天
        """
        reasons = []

        try:
            if not stock_info:
                stock_info = tq.get_stock_info(stock_code)

            name = stock_info.get('Name', '')
            code = stock_info.get('Code', '')

            # 1. ST过滤
            if 'ST' in name or '*' in name:
                reasons.append('ST股票')
                return False, reasons

            # 2. 上市日期检查
            list_date = stock_info.get('上市日期', '')
            if list_date:
                try:
                    list_dt = datetime.strptime(list_date[:10], '%Y-%m-%d')
                    days_since_listing = (datetime.now() - list_dt).days
                    if days_since_listing < 250:
                        reasons.append(f'次新股({days_since_listing}天)')
                        return False, reasons
                except:
                    pass

            # 3. 流通市值(需要财务数据)
            financial = tq.get_financial_data([stock_code], ['流通市值'])
            if financial and stock_code in financial:
                df = financial[stock_code]
                if '流通市值' in df.columns and len(df) > 0:
                    market_cap = df['流通市值'].iloc[-1]
                    if isinstance(market_cap, (int, float)):
                        market_cap_yi = market_cap / 1e8
                        if not (self.params['market_cap_min'] <= market_cap_yi <= self.params['market_cap_max']):
                            reasons.append(f'市值{market_cap_yi:.1f}亿不在{self.params["market_cap_min"]}-{self.params["market_cap_max"]}亿')
                            return False, reasons

            return True, reasons

        except Exception as e:
            reasons.append(f'异常:{str(e)[:30]}')
            return False, reasons

    def check_kline_conditions(self, stock_code):
        """
        K线条件检查
        1. 收盘价 > MA5
        2. 收盘价 > MA10
        3. 近5日涨幅 <= 25%
        """
        reasons = []

        try:
            kline = tq.get_market_data(
                stock_list=[stock_code],
                period='1d',
                count=15,
                dividend_type='none'
            )

            if not kline or stock_code not in kline:
                reasons.append('无法获取K线数据')
                return False, reasons

            df = kline[stock_code]

            if len(df) < 6:
                reasons.append('K线数据不足')
                return False, reasons

            close = df['close'].values[-1]

            ma5 = df['close'].rolling(window=5).mean().iloc[-1]
            ma10 = df['close'].rolling(window=10).mean().iloc[-1]

            if close < ma5:
                reasons.append(f'收盘{close:.2f}<MA5{ma5:.2f}')
                return False, reasons

            if close < ma10:
                reasons.append(f'收盘{close:.2f}<MA10{ma10:.2f}')
                return False, reasons

            close_5days_ago = df['close'].values[-6]
            rise_5d = (close / close_5days_ago - 1) * 100

            if rise_5d > self.params['max_5day_rise']:
                reasons.append(f'近5日涨{rise_5d:.1f}%>{self.params["max_5day_rise"]}%')
                return False, reasons

            return True, [f'MA5={ma5:.2f}, MA10={ma10:.2f}, 近5日涨幅={rise_5d:.1f}%']

        except Exception as e:
            reasons.append(f'K线异常:{str(e)[:30]}')
            return False, reasons

    def run_auction_selection(self, stock_list, max_test=20):
        """
        执行竞价选股测试
        对前N只股票进行完整筛选流程
        """
        print("\n" + "=" * 70)
        print("【竞价选股测试】基于实际数据的选股流程")
        print("=" * 70)
        print(f"\n待测试股票数: {len(stock_list)} (实际测试前{max_test}只)\n")

        passed_stocks = []
        failed_stats = {
            'basic_filter': 0,
            'kline_condition': 0,
            'auction_condition': 0,
            'data_error': 0,
        }

        for i, stock in enumerate(stock_list[:max_test]):
            print(f"[{i+1}/{min(max_test, len(stock_list))}] 检查 {stock}", end=' ... ')

            try:
                basic_ok, basic_reasons = self.check_basic_filter(stock)
                if not basic_ok:
                    print(f"[FAIL] 基础过滤失败: {basic_reasons[0]}")
                    failed_stats['basic_filter'] += 1
                    continue

                kline_ok, kline_reasons = self.check_kline_conditions(stock)
                if not kline_ok:
                    print(f"[FAIL] K线条件不满足: {kline_reasons[0]}")
                    failed_stats['kline_condition'] += 1
                    continue

                snapshot = tq.get_market_snapshot(stock)
                if not snapshot:
                    print(f"[WARN] 无法获取实时快照")
                    failed_stats['data_error'] += 1
                    continue

                high_open, has_open_data = self.calculate_high_open_rate(snapshot)

                if has_open_data:
                    if self.params['high_open_min'] <= high_open <= self.params['high_open_max']:
                        print(f"[PASS] 通过! 高开{high_open}% | {kline_reasons[0]}")
                        passed_stocks.append({
                            'code': stock,
                            'high_open': high_open,
                            'details': kline_reasons[0],
                            'snapshot': snapshot
                        })
                    else:
                        print(f"[FAIL] 高开幅度{high_open}%不在{self.params['high_open_min']}-{self.params['high_open_max']}%")
                        failed_stats['auction_condition'] += 1
                else:
                    print(f"[WARN] 缺少竞价价格字段")
                    failed_stats['data_error'] += 1

            except Exception as e:
                print(f"[ERROR] 异常: {str(e)[:40]}")
                failed_stats['data_error'] += 1

            time.sleep(0.1)

        print("\n" + "-" * 70)
        print("选股结果统计:")
        print("-" * 70)
        print(f"  总测试: {min(max_test, len(stock_list))} 只")
        print(f"  通过:   {len(passed_stocks)} 只 ({len(passed_stocks)/min(max_test, len(stock_list))*100:.1f}%)")
        print(f"\n淘汰原因分布:")
        for reason, count in failed_stats.items():
            pct = count / min(max_test, len(stock_list)) * 100
            print(f"  - {reason}: {count} 只 ({pct:.1f}%)")

        if passed_stocks:
            print(f"\n入选标的 ({len(passed_stocks)}只):")
            print("-" * 70)
            for i, item in enumerate(passed_stocks, 1):
                print(f"  {i}. {item['code']} - 高开{item['high_open']}% | {item['details']}")

        self.selected_stocks = passed_stocks
        return passed_stocks


def main():
    """主函数"""
    print("="*70)
    print("  TQ数据接口验证 & 竞价选股测试系统")
    print("  测试时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("="*70)

    validator = DataInterfaceValidator()

    if not validator.test_connection():
        print("\n[ERROR] 连接失败,终止测试")
        return

    input("\n按回车继续测试数据接口...")

    snapshot_fields = validator.test_market_snapshot()
    input("\n按回车继续K线数据测试...")

    kline_fields = validator.test_kline_data()
    input("\n按回车继续财务数据测试...")

    financial_fields = validator.test_financial_data()
    input("\n按回车继续股票信息测试...")

    info_fields = validator.test_stock_info()
    input("\n按回车继续股票列表测试...")

    all_stocks = validator.test_stock_list()
    input("\n按回车继续板块数据测试...")

    validator.test_sector_data()
    input("\n按回车开始竞价选股测试...")

    if all_stocks:
        selector = AuctionStockSelector({
            'snapshot': snapshot_fields,
            'kline': kline_fields,
            'financial': financial_fields,
            'info': info_fields
        })

        selector.run_auction_selection(all_stocks, max_test=30)

    print("\n" + "=" * 70)
    print("测试完成总结")
    print("=" * 70)

    print("\n可用字段汇总:")
    print("-" * 70)

    if snapshot_fields:
        print(f"\n实时快照字段 ({len(snapshot_fields)}个):")
        for f in sorted(snapshot_fields.keys()):
            print(f"  - {f}")

    if kline_fields:
        print(f"\nK线数据字段 ({len(kline_fields)}个):")
        for f in sorted(kline_fields.keys()):
            print(f"  - {f}")

    if financial_fields:
        print(f"\n财务数据字段 ({len(financial_fields)}个):")
        for f in sorted(financial_fields.keys()):
            print(f"  - {f}")

    if info_fields:
        print(f"\n股票信息字段 ({len(info_fields)}个):")
        for f in sorted(info_fields.keys()):
            print(f"  - {f}")

    print("\n" + "=" * 70)
    print("[OK] 所有测试完成!")
    print("=" * 70)

    try:
        tq.close()
    except:
        pass


if __name__ == '__main__':
    main()
