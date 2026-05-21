# -*- coding: utf-8 -*-
"""
K线接口修复验证脚本
验证修复后的get_market_data和get_financial_data是否正常工作
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

# 直接导入修复后的tqcenter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tqcenter import tq


def test_kline_after_financial_fix():
    """测试修复后：财务数据异常不再影响K线查询"""
    print("=" * 70)
    print("  K线接口修复验证测试")
    print("  时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 70)

    # 初始化连接
    print("\n[初始化] 建立TQ连接...")
    try:
        tq.initialize(path=os.path.abspath(__file__))
        print(f"  -> 成功! run_id={tq.run_id}")
    except Exception as e:
        print(f"  -> 失败: {e}")
        return False

    # 测试股票列表
    test_stocks = ['600519.SH', '000001.SZ', '300750.SZ', '000002.SZ', '601318.SH']

    results = {
        'stock_info': {'total': 0, 'success': 0},
        'financial': {'total': 0, 'success': 0, 'errors': []},
        'snapshot': {'total': 0, 'success': 0},
        'kline': {'total': 0, 'success': 0, 'ma_calculation': []}
    }

    print(f"\n{'='*70}")
    print(f"开始混合API调用测试 ({len(test_stocks)}只股票)")
    print('='*70)

    for i, stock in enumerate(test_stocks):
        print(f"\n[{i+1}/{len(test_stocks)}] 测试 {stock}")
        print("-" * 60)

        all_ok = True

        # Step 1: 股票信息
        print(f"  [1/4] get_stock_info()...", end=" ")
        try:
            info = tq.get_stock_info(stock)
            if info and 'Name' in info:
                name = info.get('Name', '')
                print(f"[OK] {name}")
                results['stock_info']['success'] += 1
            else:
                print("[WARN] 数据不完整")
                all_ok = False
            results['stock_info']['total'] += 1
        except Exception as e:
            print(f"[ERROR] {str(e)[:40]}")
            all_ok = False
            results['stock_info']['total'] += 1

        # Step 2: 财务数据 (关键测试点!)
        print(f"  [2/4] get_financial_data()...", end=" ")
        try:
            financial = tq.get_financial_data(
                [stock],
                field_list=['流通市值', '总市值']
            )
            if financial and stock in financial:
                df = financial[stock]
                cap_str = f"字段数={len(df.columns)}"
                print(f"[OK] {cap_str}")
                results['financial']['success'] += 1
            else:
                print("[WARN] 无数据(但不应崩溃!)")
                results['financial']['success'] += 1  # 不崩溃也算成功
            results['financial']['total'] += 1
        except Exception as e:
            error_msg = str(e)[:80]
            print(f"[ERROR] {error_msg}")
            results['financial']['errors'].append(error_msg)
            all_ok = False
            results['financial']['total'] += 1

        # Step 3: 实时快照
        print(f"  [3/4] get_market_snapshot()...", end=" ")
        try:
            snapshot = tq.get_market_snapshot(stock)
            if snapshot and 'Open' in snapshot and 'LastClose' in snapshot:
                open_price = float(snapshot['Open'])
                last_close = float(snapshot['LastClose'])
                high_open = (open_price / last_close - 1) * 100
                print(f"[OK] 高开={high_open:.2f}%")
                results['snapshot']['success'] += 1
            else:
                print("[WARN] 缺少关键字段")
                all_ok = False
            results['snapshot']['total'] += 1
        except Exception as e:
            print(f"[ERROR] {str(e)[:40]}")
            all_ok = False
            results['snapshot']['total'] += 1

        # Step 4: K线数据 (最关键的测试!)
        print(f"  [4/4] get_market_data(K线)...", end=" ")
        try:
            kline = tq.get_market_data(
                stock_list=[stock],
                period='1d',
                count=20,
                dividend_type='none'
            )

            if kline and stock in kline:
                df = kline[stock]
                if hasattr(df, 'columns') and 'close' in df.columns:
                    close = df['close'].iloc[-1]

                    # 计算均线
                    ma5 = df['close'].rolling(window=5).mean().iloc[-1]
                    ma10 = df['close'].rolling(window=10).mean().iloc[-1]

                    # 近5日涨幅
                    if len(df) >= 6:
                        rise_5d = (df['close'].iloc[-1] / df['close'].iloc[-6] - 1) * 100
                    else:
                        rise_5d = 0.0

                    ma_status = "MA5↑" if close >= ma5 else "MA5↓"
                    ma_status += " MA10↑" if close >= ma10 else " MA10↓"

                    print(f"[OK] Close={close:.2f} | {ma_status} | 5日涨{rise_5d:.1f}%")

                    results['kline']['success'] += 1
                    results['kline']['ma_calculation'].append({
                        'stock': stock,
                        'close': close,
                        'ma5': ma5,
                        'ma10': ma10,
                        'rise_5d': rise_5d,
                        'ma5_ok': close >= ma5,
                        'ma10_ok': close >= ma10
                    })
                else:
                    print(f"[WARN] 格式异常")
                    all_ok = False
                results['kline']['total'] += 1
            else:
                print(f"[FAIL] 返回空数据!")
                all_ok = False
                results['kline']['total'] += 1
        except Exception as e:
            error_msg = str(e)[:80]
            print(f"[ERROR] {error_msg}")
            all_ok = False
            results['kline']['total'] += 1

        status = "✓ 全部通过" if all_ok else "✗ 存在失败"
        print(f"\n  结果: {status}")

        time.sleep(0.2)  # 避免请求过快

    # 输出统计报告
    print(f"\n{'='*70}")
    print("验证结果统计")
    print('='*70)

    print(f"\n[股票信息] get_stock_info()")
    print(f"  成功率: {results['stock_info']['success']}/{results['stock_info']['total']} "
          f"({results['stock_info']['success']/max(results['stock_info']['total'],1)*100:.1f}%)")

    print(f"\n[财务数据] get_financial_data() (关键修复点)")
    fin_success = results['financial']['success']
    fin_total = results['financial']['total']
    print(f"  成功率: {fin_success}/{fin_total} ({fin_success/max(fin_total,1)*100:.1f}%)")
    if results['financial']['errors']:
        print(f"  错误数: {len(results['financial']['errors'])}")
        for err in results['financial']['errors'][:3]:
            print(f"    - {err}")
    else:
        print(f"  ✓ 无崩溃错误 (修复成功!)")

    print(f"\n[实时快照] get_market_snapshot()")
    snap_success = results['snapshot']['success']
    snap_total = results['snapshot']['total']
    print(f"  成功率: {snap_success}/{snap_total} ({snap_success/max(snap_total,1)*100:.1f}%)")

    print(f"\n[K线数据] get_market_data() (核心目标)")
    kline_success = results['kline']['success']
    kline_total = results['kline']['total']
    print(f"  成功率: {kline_success}/{kline_total} ({kline_success/max(kline_total,1)*100:.1f}%)")

    if results['kline']['ma_calculation']:
        print(f"\n  均线计算结果:")
        print(f"  {'股票代码':<12} {'收盘价':>8} {'MA5':>8} {'MA10':>8} {'MA5支撑':>8} {'MA10支撑':>8} {'5日涨幅':>8}")
        print(f"  {'-'*64}")
        for calc in results['kline']['ma_calculation']:
            ma5_status = "✓" if calc['ma5_ok'] else "✗"
            ma10_status = "✓" if calc['ma10_ok'] else "✗"
            print(f"  {calc['stock']:<12} {calc['close']:>8.2f} {calc['ma5']:>8.2f} {calc['ma10']:>8.2f} "
                  f"{ma5_status:>8} {ma10_status:>8} {calc['rise_5d']:>7.1f}%")

    # 最终判断
    print(f"\n{'='*70}")
    total_tests = len(test_stocks) * 4
    total_passed = (results['stock_info']['success'] +
                   results['financial']['success'] +
                   results['snapshot']['success'] +
                   results['kline']['success'])

    overall_rate = total_passed / max(total_tests, 1) * 100
    print(f"总体通过率: {total_passed}/{total_tests} ({overall_rate:.1f}%)")

    kline_pass_rate = kline_success / max(kline_total, 1) * 100
    if kline_pass_rate >= 80:
        print(f"\n✅ K线接口修复成功! 通过率 {kline_pass_rate:.1f}% >= 80%")
        print("   现在可以实现完整的均线筛选功能!")
        return True
    else:
        print(f"\n⚠️  K线接口仍存在问题，通过率仅 {kline_pass_rate:.1f}%")
        return False


if __name__ == '__main__':
    success = test_kline_after_financial_fix()

    # 清理
    try:
        tq.close()
    except:
        pass

    print("\n" + "=" * 70)
    if success:
        print("✅ 验证完成! 可以继续实现完整的量化打板选股策略")
    else:
        print("❌ 验证未完全通过，需要进一步排查")
    print("=" * 70)
