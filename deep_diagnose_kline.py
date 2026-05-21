# -*- coding: utf-8 -*-
"""
深度诊断：混合API调用中的连接状态变化
"""

import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tqcenter import tq


def deep_diagnose():
    """深度诊断混合API调用"""
    print("=" * 70)
    print("  深度诊断: 混合API调用连接状态")
    print("  时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 70)

    # 初始化
    print("\n[初始化]")
    try:
        tq.initialize(path=os.path.abspath(__file__))
        print(f"  run_id={tq.run_id}, _initialized={tq._initialized}")
    except Exception as e:
        print(f"  失败: {e}")
        return

    stock = '600519.SH'

    # Step 1: get_stock_info (应该正常)
    print(f"\n{'='*60}")
    print("[Step 1] get_stock_info()")
    print('='*60)
    try:
        info = tq.get_stock_info(stock)
        print(f"  结果: {info.get('Name', 'N/A') if info else 'None'}")
        print(f"  当前状态: run_id={tq.run_id}, initialized={tq._initialized}")
    except Exception as e:
        print(f"  异常: {e}")
        import traceback
        traceback.print_exc()

    # Step 2: get_financial_data (可能触发问题)
    print(f"\n{'='*60}")
    print("[Step 2] get_financial_data() - 关键步骤")
    print('='*60)
    try:
        financial = tq.get_financial_data(
            [stock],
            field_list=['流通市值']
        )
        if financial and stock in financial:
            df = financial[stock]
            print(f"  结果: DataFrame shape={df.shape}")
        else:
            print(f"  结果: 无数据(但未崩溃)")
        print(f"  当前状态: run_id={tq.run_id}, initialized={tq._initialized}")
    except Exception as e:
        print(f"  异常: {e}")
        import traceback
        traceback.print_exc()
        print(f"  当前状态: run_id={tq.run_id}, initialized={tq._initialized}")

    # Step 3: 直接检查内部状态
    print(f"\n{'='*60}")
    print("[Step 3] 检查TQ内部状态")
    print('='*60)
    print(f"  tq.run_id = {tq.run_id}")
    print(f"  tq._initialized = {tq._initialized}")
    print(f"  tq._connection_path = '{tq._connection_path}'")

    # 尝试手动获取run_id
    try:
        manual_run_id = tq._get_run_id()
        print(f"  tq._get_run_id() = {manual_run_id}")
    except Exception as e:
        print(f"  tq._get_run_id() 异常: {e}")

    # Step 4: get_market_data (核心问题)
    print(f"\n{'='*60}")
    print("[Step 4] get_market_data(K线) - 核心测试")
    print('='*60)
    print(f"\n  [调试] 准备传入参数:")
    print(f"      stock_list = ['{stock}'] (type: {type([stock])})")
    print(f"      len(stock_list) = {len([stock])}")
    print(f"      bool(stock_list) = {bool([stock])}")

    try:
        kline = tq.get_market_data(
            [stock],  # ← 这里明确传入列表
            period='1d',
            count=15,
            dividend_type='none'
        )

        print(f"\n  返回结果:")
        if kline:
            print(f"      type(kline) = {type(kline)}")
            print(f"      len(kline) = {len(kline)}")
            print(f"      keys = {list(kline.keys())}")

            if stock in kline:
                df = kline[stock]
                print(f"\n  ✅ 成功! K线数据 shape={df.shape}")
                close = df['close'].iloc[-1]
                ma5 = df['close'].rolling(window=5).mean().iloc[-1]
                print(f"      Close={close:.2f}, MA5={ma5:.2f}")
            else:
                print(f"\n  ❌ 错误: 股票{stock}不在返回数据中!")
        else:
            print(f"  ❌ 返回空字典")

    except ValueError as ve:
        print(f"\n  ❌ ValueError: {ve}")
        print(f"\n  这说明stock_list参数在函数内部变成了空!")

        # 额外诊断
        print(f"\n  [额外诊断] 尝试重新初始化...")
        try:
            tq.initialize(path=os.path.abspath(__file__))
            print(f"  重新初始化成功: run_id={tq.run_id}")

            print(f"\n  [额外诊断] 再次尝试get_market_data...")
            kline2 = tq.get_market_data(
                [stock],
                period='1d',
                count=10,
                dividend_type='none'
            )
            if kline2 and stock in kline2:
                df2 = kline2[stock]
                print(f"  ✅ 重新初始化后成功! shape={df2.shape}")
            else:
                print(f"  ❌ 仍然失败")
        except Exception as e2:
            print(f"  重新初始化也失败: {e2}")

    except Exception as e:
        print(f"\n  ❌ 其他异常: {e}")
        import traceback
        traceback.print_exc()

    # 清理
    try:
        tq.close()
    except:
        pass


if __name__ == '__main__':
    deep_diagnose()
