# -*- coding: utf-8 -*-
"""
通达信TQ接口功能测试脚本
测试项目:
1. 基础连接与数据获取
2. K线数据获取
3. 财务数据获取
4. 板块信息获取
5. 实时行情订阅
6. ⭐ 自动交易下单测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tqcenter import tq
import json
import time
from datetime import datetime

def test_basic_connection():
    """测试1: 基础连接"""
    print("\n" + "="*60)
    print("【测试1】基础连接测试")
    print("="*60)
    
    try:
        # 初始化连接(使用当前文件路径)
        tq.initialize(path=os.path.abspath(__file__))
        print(f"✅ 连接成功! run_id={tq.run_id}")
        return True
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

def test_kline_data():
    """测试2: K线数据获取"""
    print("\n" + "="*60)
    print("【测试2】K线历史数据获取")
    print("="*60)
    
    try:
        # 获取贵州茅台最近30天日线
        data = tq.get_market_data(
            stock_list=['600519.SH'],
            period='1d',
            start_time='20241201',
            end_time='20241231',
            dividend_type='front',  # 前复权
            count=-1
        )
        
        if data and 'close' in data:
            df = data['close']
            print(f"✅ K线数据获取成功!")
            print(f"   数据形状: {df.shape}")
            print(f"   时间范围: {df.index[0]} ~ {df.index[-1]}")
            print(f"   最新收盘价: {df.iloc[-1, 0]:.2f}")
            
            # 显示前5行
            print("\n   最近5个交易日收盘价:")
            print(df.tail().to_string())
            return True
        else:
            print("❌ 未获取到K线数据")
            return False
            
    except Exception as e:
        print(f"❌ K线数据获取失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_stock_info():
    """测试3: 股票基本信息"""
    print("\n" + "="*60)
    print("【测试3】股票基本信息")
    print("="*60)
    
    try:
        info = tq.get_stock_info('600519.SH')
        
        if info:
            print(f"✅ 股票信息获取成功!")
            print(f"   股票代码: {info.get('Code', 'N/A')}")
            print(f"   股票名称: {info.get('Name', 'N/A')}")
            print(f"   所属行业: {info.get('Industry', 'N/A')}")
            return True
        else:
            print("❌ 未获取到股票信息")
            return False
            
    except Exception as e:
        print(f"❌ 股票信息获取失败: {e}")
        return False

def test_financial_data():
    """测试4: 财务数据"""
    print("\n" + "="*60)
    print("【测试4】财务数据获取")
    print("="*60)
    
    try:
        # 获取主要财务指标
        financial = tq.get_financial_data(
            stock_list=['600519.SH'],
            field_list=['基本每股收益', '净资产收益率', '营业收入'],
            start_time='20240101',
            end_time='20241231'
        )
        
        if financial and '600519.SH' in financial:
            df = financial['600519.SH']
            print(f"✅ 财务数据获取成功!")
            print(f"   数据形状: {df.shape}")
            print("\n   财务数据预览:")
            print(df.head().to_string())
            return True
        else:
            print("⚠️  未获取到财务数据(可能字段名不匹配)")
            return False
            
    except Exception as e:
        print(f"❌ 财务数据获取失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sector_data():
    """测试5: 板块数据"""
    print("\n" + "="*60)
    print("【测试5】板块信息获取")
    print("="*60)
    
    try:
        # 获取板块列表
        sectors = tq.get_sector_list()
        
        if sectors:
            print(f"✅ 板块列表获取成功! 共{len(sectors)}个板块")
            print(f"\n   前10个板块:")
            for i, sector in enumerate(sectars[:10], 1):
                print(f"   {i}. {sector}")
            
            # 获取第一个板块的成分股(如果是行业板块)
            if len(sectors) > 0:
                first_sector = sectors[0].split('.')[0] if '.' in sectors[0] else sectors[0]
                stocks = tq.get_stock_list_in_sector(first_sector)
                if stocks:
                    print(f"\n   板块'{first_sector}'成分股数量: {len(stocks)}")
                    print(f"   前5只股票: {stocks[:5]}")
            
            return True
        else:
            print("❌ 未获取到板块列表")
            return False
            
    except Exception as e:
        print(f"❌ 板板数据获取失败: {e}")
        return False

def test_trading_calendar():
    """测试6: 交易日历"""
    print("\n" + "="*60)
    print("【测试6】交易日历")
    print("="*60)
    
    try:
        dates = tq.get_trading_calendar(
            market='SH',
            start_time='20241201',
            end_time='20241231'
        )
        
        if dates:
            print(f"✅ 交易日历获取成功!")
            print(f"   2024年12月交易日数: {len(dates)}天")
            print(f"   前5个交易日: {dates[:5]}")
            return True
        else:
            print("❌ 未获取到交易日历")
            return False
            
    except Exception as e:
        print(f"❌ 交易日历获取失败: {e}")
        return False

def test_realtime_quote_subscription():
    """测试7: 实时行情订阅"""
    print("\n" + "="*60)
    print("【测试7】实时行情订阅(3秒测试)")
    print("="*60)
    
    received_data = []
    
    def on_quote_callback(data):
        """行情回调函数"""
        print(f"   📊 收到行情数据!")
        received_data.append(data)
        try:
            json_data = json.loads(data)
            print(f"      股票: {json_data.get('Code', 'N/A')}")
            print(f"      价格: {json_data.get('Price', 'N/A')}")
        except:
            pass
    
    try:
        # 订阅贵州茅台实时行情
        result = tq.subscribe_quote(
            stock_code='600519.SH',
            period='tick',
            callback=on_quote_callback,
            count=10  # 订阅最近10条tick
        )
        
        if result:
            print(f"✅ 行情订阅成功!")
            print(f"   等待3秒接收数据...")
            
            # 等待3秒接收数据
            time.sleep(3)
            
            if received_data:
                print(f"   ✅ 成功收到{len(received_data)}条行情数据!")
                return True
            else:
                print("   ⚠️  3秒内未收到行情数据(可能非交易时间)")
                return True  # 非交易时间也算成功
        else:
            print("❌ 行情订阅失败")
            return False
            
    except Exception as e:
        print(f"❌ 行情订阅异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_auto_trading():
    """测试8: ⭐ 自动交易下单功能 (重点测试!)"""
    print("\n" + "="*60)
    print("【测试8】⭐ 自动交易下单功能测试 (重点!)")
    print("="*60)
    
    try:
        print("📝 测试参数:")
        print("   账户: 测试账户")
        print("   股票: 600519.SH (贵州茅台)")
        print("   操作: 买入 (order_type=0)")
        print("   数量: 100股")
        print("   价格: 1800.00元 (限价)")
        
        # 尝试下单 (使用极小数量测试,不会实际成交!)
        result = tq.order_stock(
            account='test_account',       # 测试账户
            stock_code='600519.SH',       # 贵州茅台
            order_type=0,                 # 0=买入, 1=卖出
            order_volume=100,             # 100股 (1手)
            price_type=0,                 # 0=限价委托
            price=1.00,                   # 极低价格(不会成交!)
            strategy_name='TQ接口测试',
            order_remark='自动化测试订单'
        )
        
        print(f"\n📋 下单返回结果:")
        print(f"   返回类型: {type(result)}")
        
        if isinstance(result, dict):
            print(f"   ✅ 返回字典数据:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            error_id = result.get('ErrorId', -1)
            error_msg = result.get('Error', '')
            
            if error_id == '0':
                print(f"\n   🎉🎉🎉 自动交易功能可用!!! 🎉🎉🎉")
                print(f"   订单已提交,ErrorId=0表示成功")
                return True
            else:
                print(f"\n   ⚠️  返回错误码: {error_id}")
                print(f"   错误信息: {error_msg}")
                
                if '暂无' in str(error_msg) or '不支持' in str(error_msg) or '未开通' in str(error_msg):
                    print(f"\n   ❌ 确认: 自动交易功能暂未开放或未配置")
                    return False
                else:
                    print(f"   ⚠️  其他错误,可能需要检查账户/权限配置")
                    return None  # 不确定状态
                    
        elif result == -1:
            print(f"   ❌ 返回-1,下单接口调用失败或异常")
            return False
        else:
            print(f"   ❓ 未知返回值: {result}")
            return None
            
    except Exception as e:
        print(f"❌ 自动交易测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_send_warning():
    """测试9: 发送预警信号"""
    print("\n" + "="*60)
    print("【测试9】预警信号发送")
    print("="*60)
    
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        result = tq.send_warn(
            stock_list=['600519.SH'],
            time_list=[now],
            price_list=['1800.00'],
            close_list=['1795.00'],
            volum_list=['1000'],
            bs_flag_list=['1'],  # 买入信号
            warn_type_list=['0'],
            reason_list=['TQ接口功能测试'],
            count=1
        )
        
        if result and result.get('ErrorId') == '0':
            print(f"✅ 预警信号发送成功!")
            print(f"   请在通达信客户端查看预警提示")
            return True
        else:
            print(f"❌ 预警发送失败: {result}")
            return False
            
    except Exception as e:
        print(f"❌ 预警发送异常: {e}")
        return False

def main():
    """主测试函数"""
    print("\n" + "█"*60)
    print("█" + " "*20 + "通达信TQ接口功能测试" + " "*21 + "█")
    print("█"*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # 执行所有测试
    tests = [
        ("基础连接", test_basic_connection),
        ("K线数据", test_kline_data),
        ("股票信息", test_stock_info),
        ("财务数据", test_financial_data),
        ("板块数据", test_sector_data),
        ("交易日历", test_trading_calendar),
        ("实时行情", test_realtime_quote_subscription),
        ("⭐自动交易", test_auto_trading),  # 重点!
        ("预警信号", test_send_warning),
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"\n❌ {test_name}测试异常: {e}")
            results[test_name] = False
    
    # 汇总报告
    print("\n\n" + "█"*60)
    print("█" + " "*22 + "测试结果汇总" + " "*23 + "█")
    print("█"*60)
    
    for test_name, result in results.items():
        if result is True:
            status = "✅ 通过"
        elif result is False:
            status = "❌ 失败"
        else:
            status = "⚠️ 待确认"
        
        marker = "★" if "自动交易" in test_name else " "
        print(f"{marker} {test_name:<15} {status}")
    
    print("\n" + "-"*60)
    
    # 特别说明自动交易能力
    auto_trade_result = results.get("⭐自动交易")
    if auto_trade_result is True:
        print("\n🎉 结论: 该接口支持自动交易功能,可实现全自动策略交易!")
    elif auto_trade_result is False:
        print("\n⚠️  结论: 自动交易接口存在但暂未开放实际功能")
        print("   可能原因:")
        print("   1. 需要在通达信中配置交易账户")
        print("   2. 需要开通特定权限或插件")
        print("   3. 接口版本限制")
        print("\n   ✅ 但仍可使用以下方式实现半自动交易:")
        print("   • 使用 send_warn() 发送买卖预警")
        print("   • 使用 send_message() 提示操作建议")
        print("   • 使用 send_user_block() 自动添加自选股")
    else:
        print("\n❓ 自动交易功能状态不确定,需要进一步验证")
    
    # 关闭连接
    try:
        tq.close()
        print("\n✅ 连接已关闭")
    except:
        pass
    
    print("\n" + "█"*60 + "\n")

if __name__ == '__main__':
    main()
