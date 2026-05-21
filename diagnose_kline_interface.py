# -*- coding: utf-8 -*-
"""
K线数据接口诊断与修复测试脚本
专门诊断和解决K线数据获取的连接状态管理问题
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# DLL路径配置
dll_path = Path(r'D:\new_tdx64\PYPlugins\TPythClient.dll')
original_file = Path(__file__).parent / "tqcenter.py"
temp_file = Path(__file__).parent / "tqcenter_kline_fix.py"

# 修改DLL路径
with open(original_file, 'r', encoding='utf-8') as f:
    content = f.read()

modified_content = content.replace(
    "global_dll_path = Path(__file__).resolve().parents[1] / 'TPythClient.dll'",
    f"global_dll_path = Path(r'{dll_path}')"
)

with open(temp_file, 'w', encoding='utf-8') as f:
    f.write(modified_content)

sys.path.insert(0, str(Path(__file__).parent))
from tqcenter_kline_fix import tq


class KLineInterfaceDiagnostic:
    """K线接口诊断器"""

    def __init__(self):
        self.test_stocks = ['600519.SH', '000001.SZ', '300750.SZ']
        self.diagnostic_results = []

    def test_1_basic_connection(self):
        """测试1: 基础连接状态"""
        print("=" * 70)
        print("[TEST 1] 基础连接初始化与状态检查")
        print("=" * 70)

        try:
            # 初始化连接
            print("\n[STEP 1] 调用 tq.initialize()...")
            tq.initialize(path=os.path.abspath(__file__))
            print(f"  -> 成功! run_id={tq.run_id}")
            print(f"  -> _initialized={tq._initialized}")

            # 检查run_id有效性
            print(f"\n[STEP 2] 检查 run_id 有效性...")
            current_run_id = tq._get_run_id()
            print(f"  -> _get_run_id() 返回: {current_run_id}")
            print(f"  -> 类型: {type(current_run_id)}")

            return True

        except Exception as e:
            print(f"  -> 失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_2_single_kline_query(self):
        """测试2: 单次K线查询"""
        print("\n" + "=" * 70)
        print("[TEST 2] 单次K线数据查询")
        print("=" * 70)

        stock = self.test_stocks[0]
        print(f"\n测试股票: {stock}")

        try:
            # 直接调用get_market_data
            print("\n[STEP 1] 调用 get_market_data()...")

            data = tq.get_market_data(
                stock_list=[stock],
                period='1d',
                count=20,
                dividend_type='none'
            )

            if not data:
                print("  -> 返回空字典")
                return False

            if stock in data:
                stock_data = data[stock]
                print(f"  -> 成功! 获取到数据")
                print(f"  -> 数据类型: {type(stock_data)}")

                if hasattr(stock_data, 'columns'):
                    print(f"  -> 字段数: {len(stock_data.columns)}")
                    print(f"  -> 记录数: {len(stock_data)}")
                    print(f"\n  字段列表:")
                    for col in stock_data.columns[:10]:
                        print(f"      - {col}")
                    print(f"\n  最新3条数据:")
                    print(stock_data.tail(3).to_string())
                    return True
                else:
                    print(f"  -> 数据格式: {type(stock_data)}")
                    print(f"  -> 内容预览: {str(stock_data)[:200]}")
                    return True
            else:
                print(f"  -> 错误: 股票{stock}不在返回数据中")
                print(f"  -> 可用keys: {list(data.keys())[:5]}")
                return False

        except Exception as e:
            print(f"  -> 异常: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_3_multiple_kline_queries(self):
        """测试3: 多次连续K线查询"""
        print("\n" + "=" * 70)
        print("[TEST 3] 多次连续K线查询 (模拟选股循环)")
        print("=" * 70)

        success_count = 0
        fail_count = 0
        errors = []

        for i, stock in enumerate(self.test_stocks):
            print(f"\n[{i+1}/{len(self.test_stocks)}] 查询 {stock}...", end=" ")

            try:
                data = tq.get_market_data(
                    stock_list=[stock],
                    period='1d',
                    count=15,
                    dividend_type='none'
                )

                if data and stock in data:
                    stock_data = data[stock]
                    record_count = len(stock_data) if hasattr(stock_data, '__len__') else 'N/A'
                    print(f"[OK] 记录数={record_count}")
                    success_count += 1
                else:
                    print(f"[FAIL] 数据为空")
                    fail_count += 1
                    errors.append(f"{stock}: 返回数据为空")

            except Exception as e:
                print(f"[FAIL] {str(e)[:50]}")
                fail_count += 1
                errors.append(f"{stock}: {str(e)[:80]}")

            time.sleep(0.2)  # 避免请求过快

        print(f"\n统计:")
        print(f"  成功: {success_count}/{len(self.test_stocks)} ({success_count/len(self.test_stocks)*100:.1f}%)")
        print(f"  失败: {fail_count}/{len(self.test_stocks)}")

        if errors:
            print(f"\n错误详情:")
            for err in errors[:5]:
                print(f"  - {err}")

        return success_count == len(self.test_stocks)

    def test_4_mixed_api_calls(self):
        """测试4: 混合API调用 (模拟实际选股流程)"""
        print("\n" + "=" * 70)
        print("[TEST 4] 混合API调用流程 (模拟实际选股)")
        print("=" * 70)
        print("流程: get_stock_info -> get_financial_data -> get_market_snapshot -> get_market_data\n")

        success_count = 0
        total_tests = min(5, len(self.test_stocks))

        for i, stock in enumerate(self.test_stocks[:total_tests]):
            print(f"\n{'='*60}")
            print(f"[股票 {i+1}/{total_tests}] {stock}")
            print('='*60)

            all_ok = True

            # Step 1: 获取股票信息
            print(f"\n  [Step 1] get_stock_info()...", end=" ")
            try:
                info = tq.get_stock_info(stock)
                if info and 'Name' in info:
                    print(f"[OK] 名称={info['Name']}")
                else:
                    print(f"[WARN] 数据不完整")
            except Exception as e:
                print(f"[FAIL] {str(e)[:40]}")
                all_ok = False

            # Step 2: 获取财务数据
            print(f"  [Step 2] get_financial_data()...", end=" ")
            try:
                financial = tq.get_financial_data(
                    [stock],
                    field_list=['流通市值', '总市值']
                )
                if financial and stock in financial:
                    df = financial[stock]
                    print(f"[OK] 字段={list(df.columns)}")
                else:
                    print(f"[WARN] 无数据")
            except Exception as e:
                print(f"[FAIL] {str(e)[:40]}")
                all_ok = False

            # Step 3: 获取实时快照
            print(f"  [Step 3] get_market_snapshot()...", end=" ")
            try:
                snapshot = tq.get_market_snapshot(stock)
                if snapshot and 'Open' in snapshot:
                    print(f"[OK] Open={snapshot['Open']}, LastClose={snapshot['LastClose']}")
                else:
                    print(f"[WARN] 缺少关键字段")
            except Exception as e:
                print(f"[FAIL] {str(e)[:40]}")
                all_ok = False

            # Step 4: 获取K线数据 (关键!)
            print(f"  [Step 4] get_market_data() (K线)...", end=" ")
            try:
                kline = tq.get_market_data(
                    [stock],
                    period='1d',
                    count=15,
                    dividend_type='none'
                )

                if kline and stock in kline:
                    df = kline[stock]
                    if hasattr(df, 'shape'):
                        print(f"[OK] shape={df.shape}, close={df['close'].iloc[-1]:.2f}")
                        success_count += 1
                    else:
                        print(f"[WARN] 格式异常: {type(df)}")
                        all_ok = False
                else:
                    print(f"[FAIL] K线数据为空!")
                    all_ok = False
            except Exception as e:
                print(f"[FAIL] {str(e)[:60]}")
                all_ok = False
                import traceback
                traceback.print_exc()

            if all_ok:
                print(f"\n  结果: 全部通过 ✓")
            else:
                print(f"\n  结果: 存在失败 ✗")

            time.sleep(0.3)

        print(f"\n{'='*70}")
        print(f"混合API测试结果:")
        print(f"  完全通过: {success_count}/{total_tests} ({success_count/total_tests*100:.1f}%)")
        print('='*70)

        return success_count == total_tests

    def test_5_connection_state_monitoring(self):
        """测试5: 连接状态监控"""
        print("\n" + "=" * 70)
        print("[TEST 5] 连接状态监控 (多次操作后检查)")
        print("=" * 70)

        states = []
        operations = [
            ("初始状态", lambda: None),
            ("get_stock_info", lambda: tq.get_stock_info('600519.SH')),
            ("get_market_snapshot", lambda: tq.get_market_snapshot('600519.SH')),
            ("get_financial_data", lambda: tq.get_financial_data(['600519.SH'], ['流通市值'])),
            ("get_market_data(K线)", lambda: tq.get_market_data(['600519.SH'], period='1d', count=10)),
            ("再次get_stock_info", lambda: tq.get_stock_info('000001.SZ')),
            ("再次get_market_data(K线)", lambda: tq.get_market_data(['000001.SZ'], period='1d', count=10)),
        ]

        for op_name, op_func in operations:
            print(f"\n[{op_name}]", end=" ")

            # 记录操作前状态
            before_state = {
                'initialized': tq._initialized,
                'run_id': tq.run_id,
            }

            try:
                result = op_func()
                after_state = {
                    'initialized': tq._initialized,
                    'run_id': tq.run_id,
                }

                state_changed = before_state != after_state
                status = "[OK]" if result else "[WARN]"
                change_marker = " [STATE CHANGED!]" if state_changed else ""

                print(f"{status}{change_marker}")

                states.append({
                    'operation': op_name,
                    'before': before_state,
                    'after': after_state,
                    'result': 'OK' if result else 'WARN',
                    'state_changed': state_changed
                })

            except Exception as e:
                after_state = {
                    'initialized': tq._initialized,
                    'run_id': tq.run_id,
                }
                print(f"[ERROR] {str(e)[:40]}")

                states.append({
                    'operation': op_name,
                    'before': before_state,
                    'after': after_state,
                    'result': 'ERROR',
                    'error': str(e)[:100],
                    'state_changed': before_state != after_state
                })

            time.sleep(0.2)

        # 输出状态变化报告
        print(f"\n{'-'*70}")
        print("状态变化报告:")
        print("-"*70)

        state_changes = [s for s in states if s.get('state_changed')]
        if state_changes:
            print(f"\n发现 {len(state_changes)} 次状态变化:")
            for s in state_changes:
                print(f"  • {s['operation']}: {s['result']}")
                if 'error' in s:
                    print(f"    错误: {s['error']}")
        else:
            print("\n✓ 所有操作期间连接状态稳定")

        return len(state_changes) == 0

    def test_6_error_recovery(self):
        """测试6: 错误恢复能力"""
        print("\n" + "=" * 70)
        print("[TEST 6] 错误恢复测试 (故意传入错误参数)")
        print("=" * 70)

        recovery_success = True

        # 测试1: 空列表
        print("\n[Test 6.1] 传入空stock_list...")
        try:
            result = tq.get_market_data([], period='1d', count=10)
            print(f"  -> 未抛出异常 (返回: {type(result)})")
        except ValueError as e:
            print(f"  -> 正确抛出ValueError: {e}")
            print(f"  -> 当前状态: initialized={tq._initialized}, run_id={tq.run_id}")

        # 测试2: 无效周期
        print("\n[Test 6.2] 传入无效period...")
        try:
            result = tq.get_market_data(['600519.SH'], period='invalid', count=10)
            print(f"  -> 返回: {result}")
        except Exception as e:
            print(f"  -> 异常: {e}")
            print(f"  -> 当前状态: initialized={tq._initialized}, run_id={tq.run_id}")

        # 测试3: 错误后恢复
        print("\n[Test 6.3] 错误后尝试正常查询...")
        try:
            result = tq.get_market_data(['600519.SH'], period='1d', count=10)
            if result and '600519.SH' in result:
                print(f"  -> [OK] 恢复成功! 获取到K线数据")
            else:
                print(f"  -> [FAIL] 无法恢复")
                recovery_success = False
        except Exception as e:
            print(f"  -> [FAIL] 恢复失败: {e}")
            recovery_success = False

        return recovery_success


def main():
    """主诊断函数"""
    print("="*70)
    print("  K线数据接口诊断系统")
    print("  目的: 定位并分析连接状态管理问题")
    print("  时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("="*70)

    diagnostic = KLineInterfaceDiagnostic()

    tests = [
        ("基础连接", diagnostic.test_1_basic_connection),
        ("单次K线查询", diagnostic.test_2_single_kline_query),
        ("多次连续查询", diagnostic.test_3_multiple_kline_queries),
        ("混合API调用", diagnostic.test_4_mixed_api_calls),
        ("连接状态监控", diagnostic.test_5_connection_state_monitoring),
        ("错误恢复能力", diagnostic.test_6_error_recovery),
    ]

    results = {}

    for test_name, test_func in tests:
        input(f"\n按回车开始 [{test_name}] 测试...")
        try:
            passed = test_func()
            results[test_name] = passed
        except Exception as e:
            print(f"\n[致命错误] {test_name} 测试崩溃: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False

    # 输出最终报告
    print("\n" + "=" * 70)
    print("诊断报告总结")
    print("=" * 70)

    total_passed = sum(results.values())
    total_tests = len(results)

    print(f"\n测试通过率: {total_passed}/{total_tests} ({total_passed/total_tests*100:.1f}%)\n")

    for test_name, passed in results.items():
        status = "PASS ✓" if passed else "FAIL ✗"
        print(f"  {status} {test_name}")

    if total_passed < total_tests:
        print(f"\n⚠️  发现 {total_tests - total_passed} 个问题需要修复")
        print("\n建议:")
        print("  1. 检查_auto_initialize()是否在每次调用时正确执行")
        print("  2. 验证_get_run_id()是否始终返回有效值")
        print("  3. 确认close()不会被意外调用")
        print("  4. 考虑添加连接重试机制")
    else:
        print("\n✓ 所有测试通过,连接状态管理正常")

    print("\n" + "=" * 70)

    # 清理
    try:
        tq.close()
    except:
        pass

    # 删除临时文件
    if temp_file.exists():
        temp_file.unlink()


if __name__ == '__main__':
    main()
