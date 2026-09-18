#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test ONNX Runtime memory arena disable fix - corrected API.
"""

import os
import sys
import time
import psutil
import threading
import gc

sys.path.insert(0, r"C:\Users\mehmet\Desktop\UNHUMAN")

import onnxruntime
from rembg import new_session, remove
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

def test_with_arena_disabled():
    print("=" * 60)
    print("TEST: ONNX Runtime with enable_cpu_mem_arena=False")
    print("=" * 60)
    
    gc.collect()
    time.sleep(1)
    print(f"Baseline: {get_mem():.1f} MB")
    
    print("\n--- Creating session with arena disabled ---")
    pid = os.getpid()
    results = {}
    stop_event = threading.Event()
    monitor_thread = threading.Thread(target=monitor_process, args=(pid, results, stop_event))
    monitor_thread.start()
    
    before = get_mem()
    
    opts = onnxruntime.SessionOptions()
    opts.intra_op_num_threads = 4
    opts.inter_op_num_threads = 1
    opts.log_severity_level = 3
    # KEY FIX: Disable CPU memory arena
    opts.enable_cpu_mem_arena = False
    
    sess = new_session("bria-rmbg", sess_opts=opts)
    
    stop_event.set()
    monitor_thread.join(timeout=2)
    
    after = get_mem()
    print(f"After session creation: {after:.1f} MB (delta: {after - before:.1f} MB)")
    print(f"Peak: {results.get('peak', 0):.1f} MB")
    
    for i in range(5):
        print(f"\n--- Inference {i+1} (160x160) ---")
        img = Image.new("RGB", (160, 160), (100, 150, 200))
        
        results = {}
        stop_event = threading.Event()
        monitor_thread = threading.Thread(target=monitor_process, args=(pid, results, stop_event))
        monitor_thread.start()
        
        before = get_mem()
        print(f"Before: {before:.1f} MB")
        
        result = remove(img, session=sess).convert("RGBA")
        
        stop_event.set()
        monitor_thread.join(timeout=2)
        
        after = get_mem()
        print(f"After: {after:.1f} MB (delta: {after - before:.1f} MB)")
        print(f"Peak: {results.get('peak', 0):.1f} MB")
        
        del result
        gc.collect()
        time.sleep(0.5)
        print(f"After gc: {get_mem():.1f} MB")
    
    return sess

def test_without_arena_disabled():
    print("\n" + "=" * 60)
    print("TEST: ONNX Runtime WITHOUT arena disable (control)")
    print("=" * 60)
    
    gc.collect()
    time.sleep(1)
    print(f"Baseline: {get_mem():.1f} MB")
    
    print("\n--- Creating session WITHOUT arena disabled ---")
    pid = os.getpid()
    results = {}
    stop_event = threading.Event()
    monitor_thread = threading.Thread(target=monitor_process, args=(pid, results, stop_event))
    monitor_thread.start()
    
    before = get_mem()
    
    opts = onnxruntime.SessionOptions()
    opts.intra_op_num_threads = 4
    opts.inter_op_num_threads = 1
    opts.log_severity_level = 3
    # Default: enable_cpu_mem_arena = True
    
    sess = new_session("bria-rmbg", sess_opts=opts)
    
    stop_event.set()
    monitor_thread.join(timeout=2)
    
    after = get_mem()
    print(f"After session creation: {after:.1f} MB (delta: {after - before:.1f} MB)")
    print(f"Peak: {results.get('peak', 0):.1f} MB")
    
    for i in range(3):
        print(f"\n--- Inference {i+1} (160x160) ---")
        img = Image.new("RGB", (160, 160), (100, 150, 200))
        
        results = {}
        stop_event = threading.Event()
        monitor_thread = threading.Thread(target=monitor_process, args=(pid, results, stop_event))
        monitor_thread.start()
        
        before = get_mem()
        print(f"Before: {before:.1f} MB")
        
        result = remove(img, session=sess).convert("RGBA")
        
        stop_event.set()
        monitor_thread.join(timeout=2)
        
        after = get_mem()
        print(f"After: {after:.1f} MB (delta: {after - before:.1f} MB)")
        print(f"Peak: {results.get('peak', 0):.1f} MB")
        
        del result
        gc.collect()
        time.sleep(0.5)
        print(f"After gc: {get_mem():.1f} MB")
    
    return sess

if __name__ == "__main__":
    sess1 = test_with_arena_disabled()
    
    del sess1
    gc.collect()
    time.sleep(2)
    
    sess2 = test_without_arena_disabled()