# -*- coding: utf-8 -*-
"""
通达信TQ接口功能测试脚本 (增强版)
自动检测DLL路径,支持手动配置
"""

import sys
import os
from pathlib import Path

# 尝试多种可能的DLL位置
possible_dll_paths = [
    Path(__file__).parent.parent / 'TPythClient.dll',  # 默认位置(上级目录)
    Path(__file__).parent / 'TPythClient.dll',          # 当前目录
    Path(r'C:\new_tdx\TPythClient.dll'),               # 常见通达信安装路径
    Path(r'D:\new_tdx\TPythClient.dll'),
    Path(r'C:\TDX\TPythClient.dll'),
]

dll_found = False
actual_dll_path = None

for dll_path in possible_dll_paths:
    if dll_path.exists():
        print(f"✅ 找到DLL文件: {dll_path}")
        actual_dll_path = dll_path
        dll_found = True
        break

if not dll_found:
    print("\n⚠️  未找到 TPythClient.dll 文件!")
    print("\n请确认:")
    print("1. 通达信软件是否已正确安装")
    print("2. DLL文件是否已复制到以下任一位置:")

    for i, path in enumerate(possible_dll_paths, 1):
        print(f"   {i}. {path}")

    print("\n3. 或者将DLL路径添加到脚本中")
    print("\n当前搜索的路径:")
    for path in possible_dll_paths:
        exists = "✅ 存在" if path.exists() else "❌ 不存在"
        print(f"   {exists}: {path}")

    # 尝试用户输入路径
    user_input = input("\n是否要手动指定DLL路径? (y/n): ").strip().lower()
    if user_input == 'y':
        custom_path = input("请输入完整的DLL文件路径: ").strip()
        if os.path.exists(custom_path):
            actual_dll_path = Path(custom_path)
            dll_found = True
            print(f"\n✅ 使用自定义路径: {actual_dll_path}")
        else:
            print(f"\n❌ 路径不存在: {custom_path}")
            sys.exit(1)
    else:
        print("\n❌ 无法继续测试,程序退出")
        sys.exit(1)

# 如果找到了DLL,修改tqcenter.py中的路径引用
if dll_found and actual_dll_path != Path(__file__).parent.parent / 'TPythClient.dll':
    print(f"\n📝 检测到DLL不在默认位置,正在临时修改路径...")
    
    # 动态修改全局变量
    import importlib.util
    spec = importlib.util.spec_from_file_location("tqcenter", Path(__file__).parent / "tqcenter.py")

    # 先读取原始文件内容
    with open(Path(__file__).parent / "tqcenter.py", 'r', encoding='utf-8') as f:
        original_content = f.read()

    # 替换DLL路径
    modified_content = original_content.replace(
        "global_dll_path = Path(__file__).resolve().parents[1] / 'TPythClient.dll'",
        f"global_dll_path = Path(r'{actual_dll_path}')"
    )

    # 写入临时文件
    temp_file = Path(__file__).parent / "tqcenter_modified.py"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(modified_content)

    # 导入修改后的模块
    spec = importlib.util.spec_from_file_location("tqcenter", temp_file)
    tqcenter_module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(Path(__file__).parent))
    spec.loader.exec_module(tqcenter_module)
    tq = tqcenter_module.tq

else:
    # 使用默认导入方式
    from tqcenter import tq

print(f"\n{'█'*60}")
print(f"开始执行功能测试...")
print(f"{'█'*60}\n")

# 现在可以正常使用tq接口了
import json
import time
from datetime import datetime

def test_connection():
    """测试基础连接"""
    try:
        tq.initialize(path=os.path.abspath(__file__))
        print(f"✅ 连接成功! run_id={tq.run_id}")
        return True
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

def test_simple_data():
    """简单数据获取测试"""
    try:
        data = tq.get_market_data(
            stock_list=['600519.SH'],
            period='1d',
            start_time='20241220',
            end_time='20241231',
            count=5
        )
        
        if data and len(data) > 0:
            print(f"✅ 数据获取成功!")
            first_key = list(data.keys())[0]
            df = data[first_key]
            print(f"   字段: {first_key}, 形状: {df.shape}")
            return True
        return False
    except Exception as e:
        print(f"❌ 数据获取失败: {e}")
        return False

def test_auto_trading():
    """重点测试: 自动交易"""
    print("\n" + "★"*60)
    print("★ 重点测试: 自动交易下单功能")
    print("★"*60 + "\n")

    try:
        result = tq.order_stock(
            account='test',
            stock_code='600519.SH',
            order_type=0,
            order_volume=100,
            price_type=0,
            price=1.00,
            strategy_name='测试',
            order_remark='自动化测试'
        )

        print(f"返回结果类型: {type(result)}")
        print(f"返回值: {result}")

        if isinstance(result, dict):
            error_id = result.get('ErrorId')
            error_msg = result.get('Error', '')

            print(f"\n错误码(ErrorId): {error_id}")
            print(f"错误信息: {error_msg}")

            if str(error_id) == '0':
                print("\n" + "🎉"*20)
                print("🎉  结论: 自动交易功能完全可用!!! 🎉")
                print("🎉"*20 + "\n")
                return True
            else:
                print(f"\n⚠️  返回错误,原因分析:")
                if '暂无' in str(error_msg) or '不支持' in str(error_msg):
                    print("   ❌ 接口存在但暂未开放实际交易功能")
                    return False
                elif '未登录' in str(error_msg) or '账户' in str(error_msg):
                    print("   ⚠️  需要在通达信中登录交易账户")
                    return None
                else:
                    print(f"   ❓ 其他原因: {error_msg}")
                    return None
        elif result == -1:
            print("\n❌ 接口调用失败(返回-1)")
            return False
        else:
            print(f"\n❓ 未知返回: {result}")
            return None

    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

# 主流程
print("="*70)
print("通达信TQ接口 - 核心功能快速验证")
print("="*70)
print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

results = {}

# 执行关键测试
print("\n【步骤1】建立连接...")
results['连接'] = test_connection()

if results['连接']:
    print("\n【步骤2】验证数据获取能力...")
    results['数据获取'] = test_simple_data()

    print("\n【步骤3】测试自动交易功能 (核心!)...")
    results['自动交易'] = test_auto_trading()

# 最终结论
print("\n\n" + "█"*70)
print("█" + " "*20 + "最终测试结论" + " "*27 + "█")
print("█"*70)

for name, result in results.items():
    icon = "✅" if result else ("❌" if result is False else "⚠️")
    print(f"{icon} {name:<10} {'通过' if result else ('失败' if result is False else '待确认')}")

print("\n" + "-"*70)

auto_result = results.get('自动交易')

if auto_result is True:
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🎉🎉🎉 重大发现: 该接口完全支持自动交易!!!  🎉🎉🎉       ║
║                                                              ║
║   ✅ 可实现功能:                                              ║
║      • 全自动买卖股票                                         ║
║      • 策略信号自动执行                                        ║
║      • 程序化交易系统                                          ║
║      • 量化策略实盘运行                                        ║
║                                                              ║
║   ⚠️  使用注意事项:                                            ║
║      • 需要在通达信中登录交易账户                               ║
║      • 确保网络连接稳定                                       ║
║      • 建议先使用模拟账户测试                                  ║
║      • 设置合理的风控规则                                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")

elif auto_result is False:
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ⚠️  结论: 自动交易接口暂未开放实际功能                        ║
║                                                              ║
║   ✅ 但仍可实现的半自动/辅助交易方案:                           ║
║      • 发送买卖预警信号 (send_warn)                            ║
║      • 实时行情监控与提醒                                      ║
║      • 自动筛选并加入自选股                                    ║
║      • 策略回测与结果展示                                      ║
║      • 数据分析与决策支持                                      ║
║                                                              ║
║   💡 建议:                                                    ║
║      1. 联系通达信官方确认交易权限                              ║
║      2. 检查是否需要购买专业版插件                             ║
║      3. 或结合其他券商API实现自动交易                            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")

else:
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ❓ 自动交易功能状态不确定                                   ║
║                                                              ║
║   可能需要:                                                   ║
║      • 登录通达信交易账户后重试                                ║
║      • 检查通达信版本和插件权限                               ║
║      • 联系技术支持确认配置                                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")

try:
    tq.close()
    print("\n✅ 测试完成,连接已关闭")
except:
    pass

print("\n")
