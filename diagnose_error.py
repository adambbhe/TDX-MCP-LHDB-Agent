# -*- coding: utf-8 -*-
"""
自动交易错误码诊断工具
帮助识别错误码23的具体原因
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime

DLL_PATH = r'D:\new_tdx64\PYPlugins\TPythClient.dll'

print("="*70)
print("  自动交易错误码诊断工具")
print("="*70)
print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# 加载模块
tqcenter_file = Path(__file__).parent / "tqcenter.py"
with open(tqcenter_file, 'r', encoding='utf-8') as f:
    content = f.read()

modified_content = content.replace(
    "global_dll_path = Path(__file__).resolve().parents[1] / 'TPythClient.dll'",
    f"global_dll_path = Path(r'{DLL_PATH}')"
)

temp_file = Path(__file__).parent / "tqcenter_diag.py"
with open(temp_file, 'w', encoding='utf-8') as f:
    f.write(modified_content)

import importlib.util
spec = importlib.util.spec_from_file_location("tqcenter", temp_file)
tqcenter_module = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(Path(__file__).parent))
spec.loader.exec_module(tqcenter_module)
tq = tqcenter_module.tq

try:
    tq.initialize(path=os.path.abspath(__file__))
    print("✅ 连接成功\n")
except Exception as e:
    print(f"❌ 连接失败: {e}")
    sys.exit(1)

def diagnose_error_code():
    """诊断错误码"""
    
    print("-"*70)
    print("【诊断测试1】使用不同参数组合测试")
    print("-"*70)
    
    test_cases = [
        {
            'name': '空账户测试',
            'params': {
                'account': '',
                'stock_code': '600519.SH',
                'order_type': 0,
                'order_volume': 100,
                'price_type': 0,
                'price': 100.0,
                'strategy_name': 'diag'
            }
        },
        {
            'name': '有效账户+市价委托',
            'params': {
                'account': 'test_account',
                'stock_code': '600519.SH',
                'order_type': 0,
                'order_volume': 100,
                'price_type': 1,  # 市价
                'price': 0.0,
                'strategy_name': 'diag'
            }
        },
        {
            'name': '极小数量测试',
            'params': {
                'account': 'test_account',
                'stock_code': '600519.SH',
                'order_type': 0,
                'order_volume': 1,  # 最小单位
                'price_type': 0,
                'price': 100.0,
                'strategy_name': 'diag'
            }
        },
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'🔬'} 测试 {i}: {test_case['name']}")
        print(f"   参数: {test_case['params']}")
        
        try:
            result = tq.order_stock(**test_case['params'])
            
            print(f"   返回类型: {type(result).__name__}")
            
            if isinstance(result, dict):
                print(f"   ErrorId: {result.get('ErrorId', 'N/A')}")
                print(f"   Error:  {result.get('Error', 'N/A')}")
                if 'RawData' in result:
                    print(f"   RawData: {result.get('RawData', 'N/A')}")
                
                results.append({
                    'test': test_case['name'],
                    'error_id': str(result.get('ErrorId', -1)),
                    'error_msg': result.get('Error', ''),
                    'raw_data': result.get('RawData', '')
                })
            else:
                print(f"   返回值: {result}")
                results.append({
                    'test': test_case['name'],
                    'error_id': str(result),
                    'error_msg': '',
                    'raw_data': ''
                })
                
        except Exception as e:
            print(f"   ❌ 异常: {e}")
            results.append({
                'test': test_case['name'],
                'error_id': 'EXCEPTION',
                'error_msg': str(e),
                'raw_data': ''
            })
    
    return results


def analyze_results(results):
    """分析结果并给出建议"""
    
    print("\n\n" + "="*70)
    print("  📊 诊断结果分析")
    print("="*70)
    
    print("\n【汇总表】")
    print("-"*70)
    print(f"{'测试场景':<25} {'错误码':<10} {'错误信息'}")
    print("-"*70)
    
    for r in results:
        print(f"{r['test']:<25} {r['error_id']:<10} {r['error_msg'][:40]}")
    
    print("-"*70)
    
    # 分析模式
    error_codes = [r['error_id'] for r in results]
    unique_codes = set(error_codes)
    
    print("\n【模式分析】")
    
    if len(unique_codes) == 1:
        code = list(unique_codes)[0]
        
        if code == '23':
            print(f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🔍 诊断结论: 所有测试均返回错误码 23                        ║
║                                                              ║
║   💡 最可能的原因:                                            ║
║   ────────────────                                            ║
║                                                              ║
║   ① 【高度可能】通达信未登录交易账户                           ║
║      ───────────────────────────────                          ║
║      • 打开通达信客户端                                       ║
║      • 点击顶部菜单 [交易] 或 [委托]                          ║
║      • 使用您的券商账号和密码登录                             ║
║      • 登录成功后重新运行此脚本                               ║
║                                                              ║
║      预期结果: 登录后错误码应该变为其他值或成功               ║
║                                                              ║
║   ② 【可能】需要特定格式的账户名                              ║
║      ───────────────────────                                  ║
║      • 当前使用: 'test_account' (测试账户)                   ║
║      • 可能需要: 您的真实券商资金账号                         ║
║      • 格式示例: '1234567890' (10位数字)                     ║
║                                                              ║
║   ③ 【可能】通达信版本不支持交易接口                          ║
║      ────────────────────────────                              ║
║      • 确认使用的是专业版/机构版                              ║
║      • 普通版可能限制Python交易功能                           ║
║      • 联系通达信客服确认版本权限                             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
        
        elif code == '-1' or code == 'EXCEPTION':
            print("""
   所有测试都失败了,可能是技术层面的问题。
   
   建议:
   • 重启通达信客户端
   • 检查通达信是否正常运行
   • 查看通达信的错误日志
""")
            
    else:
        print(f"""
   不同测试返回不同错误码: {unique_codes}
   
   这说明接口对不同参数有不同反应,这是好现象!
   
   建议尝试:
   • 使用真实的券商账户名
   • 在交易时间内测试
   • 使用合理的价格和数量
""")


def main():
    print("开始诊断...\n")
    
    results = diagnose_error_code()
    analyze_results(results)
    
    # 清理
    try:
        if temp_file.exists():
            temp_file.unlink()
        tq.close()
        print("\n✅ 清理完成")
    except:
        pass
    
    print("\n" + "="*70 + "\n")

if __name__ == '__main__':
    main()
