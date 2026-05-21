# -*- coding: utf-8 -*-
"""
测试TQ连接状态
"""

import sys
import os
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

import tqcenter

print("="*70)
print("测试TQ连接状态")
print("="*70)

print(f"\n1. 检查当前tq类状态:")
print(f"   _initialized: {tqcenter.tq._initialized}")
print(f"   run_id: {tqcenter.tq.run_id}")
print(f"   run_mode: {tqcenter.tq.run_mode}")

print(f"\n2. 尝试关闭旧连接...")
try:
    tqcenter.tq.close()
    print("   关闭成功")
except Exception as e:
    print(f"   关闭失败: {e}")

import time
time.sleep(2)

print(f"\n3. 关闭后状态:")
print(f"   _initialized: {tqcenter.tq._initialized}")
print(f"   run_id: {tqcenter.tq.run_id}")

print(f"\n4. 尝试重新初始化...")
try:
    tqcenter.tq.initialize(path=str(script_dir))
    print(f"   初始化成功!")
    print(f"   run_id: {tqcenter.tq.run_id}")
except Exception as e:
    print(f"   初始化失败: {e}")

print("\n" + "="*70)
