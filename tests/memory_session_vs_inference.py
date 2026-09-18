#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test session creation vs inference memory separately.
"""

import os
import sys
import time
import psutil
import threading
import gc

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

print("=" * 60)
print("SESSION CREATION vs INFERENCE MEMORY TEST")
print("=" * 60)

# Reset
app._BG_SESSION["session"] = None
gc.collect()
time.sleep(1)
print(f"Baseline: {get_mem():.1f} MB")

# Test 1: Just create session
print("\n--- Test 1: Create session only ---")
pid = os.getpid()
results = {}
stop_event = threading.Event()
monitor_thread = threading.Thread(target=monitor_process, args=(pid, results, stop_event))
monitor_thread.start()

before = get_mem()
print(f"Before session creation: {before:.1f} MB")

# Trigger session creation by calling _bg_remove_impl with tiny image
# But we want to isolate session creation...
import onnxruntime
from rembg import new_session

intra, inter = 4, 1
opts = onnxruntime.SessionOptions()
opts.intra_op_num_threads = intra
opts.inter_op_num_threads = inter
opts.log_severity_level = 3

sess = new_session("bria-rmbg", sess_opts=opts)
app._BG_SESSION["session"] = sess

stop_event.set()
monitor_thread.join(timeout=2)

after = get_mem()
print(f"After session creation: {after:.1f} MB")
print(f"Peak during creation: {results.get('peak', 0):.1f} MB")
print(f"Delta: {after - before:.1f} MB")

# Test 2: First inference
print("\n--- Test 2: First inference (160x160) ---")
img = Image.new("RGB", (160, 160), (100, 150, 200))

results = {}
stop_event = threading.Event()
monitor_thread = threading.Thread(target=monitor_process, args=(pid, results, stop_event))
monitor_thread.start()

before = get_mem()
print(f"Before inference: {before:.1f} MB")

result = app._bg_remove_impl(img)

stop_event.set()
monitor_thread.join(timeout=2)

after = get_mem()
print(f"After inference: {after:.1f} MB")
print(f"Peak during inference: {results.get('peak', 0):.1f} MB")
print(f"Delta: {after - before:.1f} MB")
print(f"Result size: {result.size}")

# Cleanup
del result
gc.collect()
time.sleep(1)
print(f"After gc: {get_mem():.1f} MB")

# Test 3: Second inference (same image)
print("\n--- Test 3: Second inference (same 160x160) ---")
img2 = Image.new("RGB", (160, 160), (100, 150, 200))

results = {}
stop_event = threading.Event()
monitor_thread = threading.Thread(target=monitor_process, args=(pid, results, stop_event))
monitor_thread.start()

before = get_mem()
print(f"Before inference: {before:.1f} MB")

result2 = app._bg_remove_impl(img2)

stop_event.set()
monitor_thread.join(timeout=2)

after = get_mem()
print(f"After inference: {after:.1f} MB")
print(f"Peak during inference: {results.get('peak', 0):.1f} MB")
print(f"Delta: {after - before:.1f} MB")

del result2
gc.collect()
time.sleep(1)
print(f"After gc: {get_mem():.1f} MB")

# Test 4: Third inference
print("\n--- Test 4: Third inference (same 160x160) ---")
img3 = Image.new("RGB", (160, 160), (100, 150, 200))

results = {}
stop_event = threading.Event()
monitor_thread = threading.Thread(target=monitor_process, args=(pid, results, stop_event))
monitor_thread.start()

before = get_mem()
print(f"Before inference: {before:.1f} MB")

result3 = app._bg_remove_impl(img3)

stop_event.set()
monitor_thread.join(timeout=2)

after = get_mem()
print(f"After inference: {after:.1f} MB")
print(f"Peak during inference: {results.get('peak', 0):.1f} MB")
print(f"Delta: {after - before:.1f} MB")

del result3
gc.collect()
time.sleep(1)
print(f"After gc: {get_mem():.1f} MB")

# Test 5: Check if session is really reused
print(f"\nSession object: {app._BG_SESSION['session']}")
print(f"Session ID: {id(app._BG_SESSION['session'])}")