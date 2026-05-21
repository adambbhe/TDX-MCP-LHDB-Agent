# -*- coding: utf-8 -*-
"""
终极诊断：追踪stock_list的变化
"""

import sys
import os
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 临时monkey-patch get_market_data来追踪调用
original_tq = None


def test_with_monkey_patch():
    """使用monkey-patch追踪get_market_data调用"""
    print("=" * 70)
    print("  终极诊断: 追踪stock_list变化")
    print("  时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 70)

    # 延迟导入以避免初始化问题
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "tqcenter_module",
        os.path.join(os.path.dirname(__file__), "tqcenter.py")
    )
    tqcenter_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tqcenter_mod)
    tq = tqcenter_mod.tq

    # 保存原始方法
    original_get_market_data = tq.get_market_data

    def traced_get_market_data(*args, **kwargs):
        print(f"\n[TRACE] get_market_data 被调用!")
        print(f"[TRACE]   args={args}")
        print(f"[TRACE]   kwargs={kwargs}")

        if len(args) >= 2:
            stock_list_arg = args[1]
            print(f"[TRACE]   args[1] (stock_list) = {stock_list_arg}")
            print(f"[TRACE]   id(args[1]) = {id(stock_list_arg)}")
        else:
            print(f"[TRACE]   stock_list from kwargs = {kwargs.get('stock_list', 'NOT FOUND')}")

        try:
            result = original_get_market_data(*args, **kwargs)
            print(f"[TRACE]   成功返回! type={type(result)}")
            return result
        except Exception as e:
            print(f"[TRACE]   异常: {e}")
            raise

    # 替换方法
    tq.get_market_data = traced_get_market_data

    # 初始化
    print("\n[1] 初始化连接...")
    try:
        tq.initialize(path=os.path.abspath(__file__))
        print(f"  -> 成功! run_id={tq.run_id}")
    except Exception as e:
        print(f"  -> 失败: {e}")
        return

    stock = '600519.SH'

    # Step 1: get_stock_info
    print(f"\n{'='*60}")
    print("[Step 1] get_stock_info()")
    print('='*60)
    try:
        info = tq.get_stock_info(stock)
        print(f"  结果: {info.get('Name', 'N/A') if info else 'None'}")
    except Exception as e:
        print(f"  异常: {e}")

    # Step 2: get_financial_data
    print(f"\n{'='*60}")
    print("[Step 2] get_financial_data()")
    print('='*60)
    try:
        financial = tq.get_financial_data([stock], field_list=['流通市值'])
        print(f"  结果: {'有数据' if (financial and stock in financial) else '无数据'}")
    except Exception as e:
        print(f"  异常: {e}")

    # Step 3: get_market_data - 关键测试
    print(f"\n{'='*60}")
    print("[Step 3] get_market_data(K线) - 准备调用")
    print('='*60)

    my_stock_list = [stock]
    print(f"\n  [准备] 创建列表:")
    print(f"      my_stock_list = {my_stock_list}")
    print(f"      id(my_stock_list) = {id(my_stock_list)}")
    print(f"      len(my_stock_list) = {len(my_stock_list)}")

    print(f"\n  [调用] tq.get_market_data(my_stock_list, ...)")
    try:
        kline = tq.get_market_data(
            my_stock_list,
            period='1d',
            count=15,
            dividend_type='none'
        )

        print(f"\n  返回结果:")
        if kline and stock in kline:
            df = kline[stock]
            print(f"  ✅ 成功! shape={df.shape}, close={df['close'].iloc[-1]:.2f}")
        else:
            print(f"  ❌ 数据格式异常: keys={list(kline.keys()) if kline else None}")

    except ValueError as ve:
        print(f"\n  ❌ ValueError: {ve}")

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
    test_with_monkey_patch()
