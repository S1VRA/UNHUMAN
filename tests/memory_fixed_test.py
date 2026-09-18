#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fresh test of the fixed NHModTool._bg_remove_impl
"""

import os
import sys
import time
import psutil
import threading
import gc

# Fresh import
sys.path.insert(0, r"C:\Users\mehmet\Desktop\UNHUMAN")
import NHModTool as app
from PIL import Image

def monitor_process(pid, results, stop_event, interval=0.05):
    peak = 0
    samples = []
    while not stop_event.is_set():
        try:
            p = psutil.Process(pid)
            mem = p.memory_info()
            rss = mem.rss / (1024 * 1024)
            samples.append(rss)
            if rss > peak:
                peak = rss
        except:
            pass
        time.sleep(interval)
    results['peak'] = peak
    results['avg'] = sum(samples) / len(samples) if samples else 0
    results['samples'] = len(samples)

def get_mem():
    return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)

# Reset session
app._BG_SESSION["session"] = None
gc.collect()
time.sleep(1)

print("=" * 60)
print("TEST: Fixed NHModTool._bg_remove_impl")
print("=" * 60)
print(f"Baseline: {get_mem():.1f} MB")

pid = os.getpid()

# Test 1: First inference (creates session)
print("\n--- Inference 1 (160x160) ---")
img = Image.new("RGB", (160, 160), (100, 150, 200))

results = {}
stop_event = threading.Event()
monitor_thread = threading.Thread(target=monitor_process, args=(pid, results, stop_event))
monitor_thread.start()

before = get_mem()
print(f"Before: {before:.1f} MB")

result = app._bg_remove_impl(img)

stop_event.set()
monitor_thread.join(timeout=2)

after = get_mem()
print(f"After: {after:.1f} MB (delta: {after - before:.1f} MB)")
print(f"Peak: {results.get('peak', 0):.1f} MB")

del result
gc.collect()
time.sleep(1)
print(f"After gc: {get_mem():.1f} MB")

# Test 2: Second inference
print("\n--- Inference 2 (160x160) ---")
img2 = Image.new("RGB", (160, 160), (100, 150, 200))

results = {}
stop_event = threading.Event()
monitor_thread = threading.Thread(target=monitor_process, args=(pid, results, stop_event))
monitor_thread.start()

before = get_mem()
print(f"Before: {before:.1f} MB")

result2 = app._bg_remove_impl(img2)

stop_event.set()
monitor_thread.join(timeout=2)

after = get_mem()
print(f"After: {after:.1f} MB (delta: {after - before:.1f} MB)")
print(f"Peak: {results.get('peak', 0):.1f} MB")

del result2
gc.collect()
time.sleep(1)
print(f"After gc: {get_mem():.1f} MB")

# Test 3: Third inference
print("\n--- Inference 3 (160x160) ---")
img3 = Image.new("RGB", (160, 160), (100, 150, 200))

results = {}
stop_event = threading.Event()
monitor_thread = threading.Thread(target=monitor_process, args=(pid, results, stop_event))
monitor_thread.start()

before = get_mem()
print(f"Before: {before:.1f} MB")

result3 = app._bg_remove_impl(img3)

stop_event.set()
monitor_thread.join(timeout=2)

after = get_mem()
print(f"After: {after:.1f} MB (delta: {after - before:.1f} MB)")
print(f"Peak: {results.get('peak', 0):.1f} MB")

del result3
gc.collect()
time.sleep(1)
print(f"After gc: {get_mem():.1f} MB")

print(f"\nSession reused: {app._BG_SESSION['session'] is not None}")