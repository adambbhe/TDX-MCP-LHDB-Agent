# -*- coding: utf-8 -*-
"""
K线接口直接测试 - 排除其他API干扰
"""

import sys
import os
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tqcenter import tq


def test_direct_kline():
    """直接测试K线接口"""
    print("=" * 70)
    print("  K线接口直接测试 (排除干扰)")
    print("  时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 70)

    # 初始化
    print("\n[1] 初始化连接...")
    try:
        tq.initialize(path=os.path.abspath(__file__))
        print(f"  -> 成功! run_id={tq.run_id}")
        print(f"  -> _initialized={tq._initialized}")
    except Exception as e:
        print(f"  -> 失败: {e}")
        return False

    # 直接调用get_market_data
    stock = '600519.SH'
    print(f"\n[2] 直接调用 get_market_data({stock})...")
    print(f"  参数: stock_list=['{stock}'], period='1d', count=20")

    try:
        # 添加调试信息
        print(f"\n  [调试] 调用前检查:")
        print(f"      stock_list = ['{stock}']")
        print(f"      bool(stock_list) = {bool(['{stock}'])}")

        data = tq.get_market_data(
            stock_list=[stock],
            period='1d',
            count=20,
            dividend_type='none'
        )

        if data and stock in data:
            df = data[stock]
            print(f"\n  -> 成功!")
            print(f"  -> 数据类型: {type(df)}")
            if hasattr(df, 'shape'):
                print(f"  -> shape: {df.shape}")
                print(f"\n  最新5条数据:")
                print(df.tail(5).to_string())
                return True
            else:
                print(f"  -> 数据: {str(df)[:200]}")
                return True
        else:
            print(f"\n  -> 返回数据为空")
            print(f"  -> 返回keys: {list(data.keys()) if data else None}")
            return False

    except ValueError as e:
        print(f"\n  -> ValueError: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n  -> 异常: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            tq.close()
        except:
            pass


if __name__ == '__main__':
    success = test_direct_kline()

    print("\n" + "=" * 70)
    if success:
        print("✅ K线接口工作正常!")
    else:
        print("❌ K线接口存在问题")
    print("=" * 70)
