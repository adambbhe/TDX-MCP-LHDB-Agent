# -*- coding: utf-8 -*-
"""
通达信TQ接口功能完整测试
DLL路径: D:\new_tdx64\PYPlugins\TPythClient.dll
"""

import sys
import os
from pathlib import Path

# 设置正确的DLL路径
DLL_PATH = r'D:\new_tdx64\PYPlugins\TPythClient.dll'

# 临时修改tqcenter.py中的DLL路径
tqcenter_file = Path(__file__).parent / "tqcenter.py"

with open(tqcenter_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 替换DLL路径
modified_content = content.replace(
    "global_dll_path = Path(__file__).resolve().parents[1] / 'TPythClient.dll'",
    f"global_dll_path = Path(r'{DLL_PATH}')"
)

temp_file = Path(__file__).parent / "tqcenter_temp.py"
with open(temp_file, 'w', encoding='utf-8') as f:
    f.write(modified_content)

# 导入修改后的模块
import importlib.util
spec = importlib.util.spec_from_file_location("tqcenter", temp_file)
tqcenter_module = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(Path(__file__).parent))
spec.loader.exec_module(tqcenter_module)
tq = tqcenter_module.tq

print(f"✅ DLL加载成功: {DLL_PATH}")

# 导入其他依赖
import json
import time
from datetime import datetime

def print_separator(title):
    """打印分隔线"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_1_connection():
    """测试1: 基础连接"""
    print_separator("【测试1】基础连接")
    
    try:
        tq.initialize(path=os.path.abspath(__file__))
        print(f"✅ 连接成功!")
        print(f"   run_id: {tq.run_id}")
        print(f"   run_mode: {tq.run_mode}")
        return True
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

def test_2_kline_data():
    """测试2: K线数据获取"""
    print_separator("【测试2】K线历史数据")
    
    try:
        data = tq.get_market_data(
            stock_list=['600519.SH'],
            period='1d',
            start_time='20241201',
            end_time='20241231',
            dividend_type='front',
            count=10
        )
        
        if data and len(data) > 0:
            print(f"✅ K线数据获取成功!")
            
            # 显示所有字段
            print(f"\n   可用字段 ({len(data)}个):")
            for i, (key, df) in enumerate(data.items(), 1):
                if not key.startswith('Error'):
                    print(f"      {i}. {key:<15} 形状:{df.shape}")
            
            # 显示收盘价详情
            if 'close' in data:
                df_close = data['close']
                print(f"\n   📊 收盘价数据预览(最近5天):")
                print(df_close.tail().to_string())
            
            return True
        else:
            print("❌ 未获取到K线数据")
            return False
            
    except Exception as e:
        print(f"❌ K线数据获取异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_3_stock_info():
    """测试3: 股票信息"""
    print_separator("【测试3】股票基本信息")
    
    try:
        info = tq.get_stock_info('600519.SH')
        
        if info:
            print(f"✅ 股票信息获取成功!")
            print(f"\n   基础信息:")
            for key in ['Code', 'Name', 'Industry', 'ListDate']:
                if key in info:
                    print(f"      {key}: {info[key]}")
            return True
        else:
            print("❌ 未获取到股票信息")
            return False
            
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

def test_4_sector_list():
    """测试4: 板块列表"""
    print_separator("【测试4】板块信息")
    
    try:
        sectors = tq.get_sector_list()
        
        if sectors:
            print(f"✅ 板块列表获取成功! 共{len(sectors)}个板块")
            print(f"\n   前15个板块:")
            for i, sector in enumerate(sectars[:15], 1):
                print(f"      {i:>3}. {sector}")
            return True
        else:
            print("❌ 未获取到板块列表")
            return False
            
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

def test_5_trading_calendar():
    """测试5: 交易日历"""
    print_separator("【测试5】交易日历")
    
    try:
        dates = tq.get_trading_calendar(
            market='SH',
            start_time='20241220',
            end_time='20241231'
        )
        
        if dates:
            print(f"✅ 交易日历获取成功!")
            print(f"   2024年12月下旬交易日: {len(dates)}天")
            print(f"   日期列表: {dates}")
            return True
        else:
            print("❌ 未获取到交易日历")
            return False
            
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

def test_6_auto_trading_CRITICAL():
    """
    测试6: ⭐⭐⭐ 自动交易下单功能 (最关键测试!!!) ⭐⭐⭐
    """
    print_separator("【测试6】⭐⭐⭐ 自动交易下单功能 ⭐⭐⭐")
    print("   这是本次测试的核心目标!")
    print("="*70)
    
    try:
        print("\n📋 下单参数配置:")
        print("   • 账户类型: 测试账户")
        print("   • 目标股票: 600519.SH (贵州茅台)")
        print("   • 操作方向: 买入 (order_type=0)")
        print("   • 委托数量: 100股 (最小单位)")
        print("   • 委托价格: 1.00元 (远低于市价,不会成交!)")
        print("   • 价格类型: 限价委托")
        print("   • 策略名称: TQ接口自动化测试")
        
        print("\n⏳ 正在调用下单接口...")
        
        result = tq.order_stock(
            account='test_account',
            stock_code='600519.SH',
            order_type=0,
            order_volume=100,
            price_type=0,
            price=1.00,
            strategy_name='TQ接口自动化测试',
            order_remark='自动化功能验证-不会实际成交'
        )
        
        print("\n📊 下单接口返回结果:")
        print(f"   返回数据类型: {type(result).__name__}")
        print(f"   返回值内容:")
        
        if isinstance(result, dict):
            # 格式化输出字典
            print(json.dumps(result, indent=6, ensure_ascii=False))
            
            error_id = str(result.get('ErrorId', -1))
            error_msg = result.get('Error', '')
            order_info = result.get('OrderInfo', {})
            
            print("\n" + "-"*70)
            print("🔍 详细分析:")
            print("-"*70)
            print(f"   错误码(ErrorId): {error_id}")
            print(f"   错误描述: {error_msg}")
            
            if order_info:
                print(f"   订单信息: {json.dumps(order_info, indent=6)}")
            
            # 核心判断逻辑
            print("\n" + "★"*70)
            
            if error_id == '0':
                print("★" + " "*18 + "🎉🎉🎉 结论 🎉🎉🎉" + " "*21 + "★")
                print("★"*70)
                print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║         ✨✨✨ 重大发现:自动交易功能完全可用! ✨✨✨           ║
║                                                              ║
║   该接口支持以下全自动交易能力:                               ║
║                                                              ║
║   ✅ 功能清单:                                                ║
║      ┌────────────────────────────────────┐                  ║
║      │ 1. 自动买入/卖出股票               │                  ║
║      │ 2. 限价委托 / 市价委托             │                  ║
║      │ 3. 策略信号自动执行                 │                  ║
║      │ 4. 批量订单处理                     │                  ║
║      │ 5. 实时交易状态查询                 │                  ║
║      └────────────────────────────────────┘                  ║
║                                                              ║
║   💼 应用场景:                                                ║
║      • 量化策略实盘运行                                       ║
║      • 算法交易系统                                           ║
║      • 程序化交易                                             ║
║      • 自动化网格交易                                         ║
║      • 智能盯盘与自动止盈止损                                 ║
║                                                              ║
║   ⚠️  使用前提:                                               ║
║      1. 通达信已登录交易账户                                   ║
║      2. 已开通相关交易权限                                     ║
║      3. 网络连接稳定                                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
                return True
                
            elif '暂无' in error_msg or '不支持' in error_msg or '未实现' in error_msg:
                print("★" + " "*25 + "⚠️  重要发现 ⚠️" + " "*26 + "★")
                print("★"*70)
                print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║       ⚠️  接口存在但自动交易功能暂未开放                        ║
║                                                              ║
║   接口返回错误:                                               ║
║   ┌──────────────────────────────────┐                       ║
║   │ ErrorId: {}                       │                       ║
║   │ Error  : {}                       │                       ║
║   └──────────────────────────────────┘                       ║
║                                                              ║
║   ✅ 但仍可实现的半自动交易方案:                               ║
║                                                              ║
║   1️⃣  预警信号系统                                            ║
║      • send_warn() 发送买卖预警                               ║
║      • 通达信客户端弹窗提示                                   ║
║      • 支持自定义预警原因                                     ║
║                                                              ║
║   2️⃣  实时监控与筛选                                          ║
║      • subscribe_hq() 订阅实时行情                            ║
║      • 自动扫描全市场股票                                     ║
║      • 条件筛选后发送自选股                                   ║
║                                                              ║
║   3️⃣  数据分析与决策支持                                      ║
║      • 获取完整K线/财务/板块数据                              ║
║      • 策略回测并展示结果                                     ║
║      • send_bt_data() 输出回测报告                            ║
║                                                              ║
║   4️⃣  辅助工具                                                ║
║      • send_user_block() 自动管理自选股                       ║
║      • send_message() 发送策略消息                            ║
║      • print_to_tdx() 导出专业报表                            ║
║                                                              ║
║   💡 建议:                                                    ║
║      • 联系通达信官方确认是否需要购买专业版                    ║
║      • 或结合券商API(如华泰/中信)实现全自动交易                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""".format(error_id, error_msg))
                return False
                
            elif '未登录' in error_msg or '账户' in error_msg or '连接' in error_msg:
                print("★" + " "*28 + "💡 提示 💡" + " "*29 + "★")
                print("★"*70)
                print(f"""
   ⚠️  需要登录通达信交易账户!

   错误信息: {error_msg}

   解决步骤:
   1. 打开通达信客户端
   2. 登录您的证券交易账户
   3. 重新运行此测试脚本

   如果已登录但仍报错,可能需要:
   • 检查通达信版本是否支持Python交易接口
   • 确认是否需要额外插件或授权
""")
                return None
                
            else:
                print("★" + " "*30 + "❓ 待确认 ❓" + " "*29 + "★")
                print("★"*70)
                print(f"""
   ❓ 返回未知错误,需要进一步分析

   ErrorId: {error_id}
   Error  : {error_msg}

   建议:
   • 查阅通达信TQ接口文档
   • 联系技术支持
   • 检查账户权限和设置
""")
                return None
                
        elif result == -1:
            print("   ❌ 接口调用失败(返回值=-1)")
            print("""
   可能原因:
   • DLL函数执行异常
   • 参数格式错误
   • 连接已断开
""")
            return False
            
        else:
            print(f"   ❓ 未知返回类型: {result}")
            return None
            
    except Exception as e:
        print(f"\n❌ 自动交易测试异常!")
        print(f"   异常信息: {e}")
        print("\n   详细堆栈:")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试流程"""
    print("\n" + "█"*70)
    print("█" + " "*15 + "通达信TQ策略接口 - 完整功能测试" + " "*16 + "█")
    print("█"*70)
    print(f"  测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  DLL路径 : {DLL_PATH}")
    print(f"  Python  : {sys.version.split()[0]}")
    print("█"*70)
    
    results = {}
    
    # 定义测试序列
    tests = [
        ("基础连接", test_1_connection),
        ("K线数据", test_2_kline_data),
        ("股票信息", test_3_stock_info),
        ("板块列表", test_4_sector_list),
        ("交易日历", test_5_trading_calendar),
        ("⭐自动交易", test_6_auto_trading_CRITICAL),  # 最重要!
    ]
    
    # 依次执行测试
    for test_name, test_func in tests:
        try:
            is_critical = "自动交易" in test_name
            
            if is_critical:
                print("\n\n" + "⚠️"*35)
                print("⚠️ 即将执行最重要的测试:自动交易功能验证")
                print("⚠️"*35 + "\n")
                input("按回车键继续执行自动交易测试...")
            
            result = test_func()
            results[test_name] = result
            
            if result is False and test_name == "基础连接":
                print("\n❌ 基础连接失败,无法继续后续测试")
                break
                
        except KeyboardInterrupt:
            print(f"\n\n⚠️  用户中断了 {test_name} 测试")
            results[test_name] = None
            break
        except Exception as e:
            print(f"\n❌ {test_name} 测试出现未预期异常: {e}")
            results[test_name] = False
    
    # 生成最终报告
    print("\n\n\n")
    print("█"*70)
    print("█" + " "*22 + "📊 最终测试报告 📊" + " "*23 + "█")
    print("█"*70)
    
    print("\n测试结果汇总:")
    print("-"*70)
    
    for test_name, result in results.items():
        if result is True:
            status = "✅ 通过"
            color = "绿色"
        elif result is False:
            status = "❌ 失败"
            color = "红色"
        else:
            status = "⚠️ 待确认"
            color = "黄色"
        
        marker = "★" if "自动交易" in test_name else " "
        print(f"{marker} {test_name:<15} [{status}]")
    
    print("-"*70)
    
    # 统计
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    unknown = sum(1 for r in results.values() if r is None)
    total = len(results)
    
    print(f"\n统计: 总计{total}项 | 通过{passed}项 | 失败{failed}项 | 待确认{unknown}项")
    
    # 关闭连接
    print("\n" + "-"*70)
    try:
        tq.close()
        print("✅ 连接已安全关闭")
    except Exception as e:
        print(f"⚠️  关闭连接时出现问题: {e}")
    
    print("\n" + "█"*70 + "\n")
    
    return results

if __name__ == '__main__':
    test_results = main()
