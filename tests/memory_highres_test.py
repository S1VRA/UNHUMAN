#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test EXE with a high-resolution image (simulates real user scenario).
"""

import os
import sys
import time
import subprocess
import psutil
import threading
import tempfile
from PIL import Image

def create_test_image(path, size):
    img = Image.new("RGB", size, (100, 150, 200))
    # Add pattern
    for x in range(0, size[0], 40):
        for y in range(0, size[1], 40):
            if (x + y) % 80 == 0:
                for dx in range(min(20, size[0] - x)):
                    for dy in range(min(20, size[1] - y)):
                        img.putpixel((x + dx, y + dy), (255, 50, 50))
    img.save(path, "PNG")

def monitor_process(pid, results, stop_event, interval=0.1):
    peak = 0
    cpu_peak = 0
    samples = 0
    while not stop_event.is_set():
        try:
            p = psutil.Process(pid)
            mem = p.memory_info()
            rss = mem.rss / (1024 * 1024)
            cpu = p.cpu_percent(interval=None)
            if rss > peak:
                peak = rss
            if cpu > cpu_peak:
                cpu_peak = cpu
            samples += 1
        except:
            pass
        time.sleep(interval)
    results['peak_mb'] = peak
    results['cpu_peak'] = cpu_peak
    results['samples'] = samples

def run_exe_with_image(exe_path, image_path):
    print(f"Testing EXE with image: {os.path.basename(image_path)} ({os.path.getsize(image_path)//1024} KB)")
    
    # We'll use the internal bg_remove via a custom script approach
    # Since we can't easily drive the GUI, let's use the internal function via python -c
    pass

def test_inference_directly(size=(2048, 2048), label="Test"):
    """Test inference directly using the updated NHModTool module."""
    import sys
    sys.path.insert(0, r"C:\Users\mehmet\Desktop\UNHUMAN")
    import NHModTool as app
    from PIL import Image
    import gc
    
    print(f"\n=== {label} ({size[0]}x{size[1]}) ===")
    
    # Reset session
    app._BG_SESSION["session"] = None
    gc.collect()
    time.sleep(1)
    
    pid = os.getpid()
    print(f"PID: {pid}")
    
    # Create test image
    img = Image.new("RGB", size, (100, 150, 200))
    for x in range(0, size[0], 40):
        for y in range(0, size[1], 40):
            if (x + y) % 80 == 0:
                for dx in range(min(20, size[0] - x)):
                    for dy in range(min(20, size[1] - y)):
                        img.putpixel((x + dx, y + dy), (255, 50, 50))
    
    # Monitor
    import psutil
    results = {}
    stop_event = threading.Event()
    monitor_thread = threading.Thread(target=monitor_process, args=(pid, results, stop_event))
    monitor_thread.start()
    
    before = psutil.Process(pid).memory_info().rss / (1024 * 1024)
    print(f"Before: {before:.1f} MB")
    
    start = time.time()
    result = app._bg_remove_impl(img)
    elapsed = time.time() - start
    
    stop_event.set()
    monitor_thread.join(timeout=2)
    
    after = psutil.Process(pid).memory_info().rss / (1024 * 1024)
    print(f"After:  {after:.1f} MB")
    print(f"Peak:   {results.get('peak_mb', 0):.1f} MB")
    print(f"CPU Peak: {results.get('cpu_peak', 0):.1f}%")
    print(f"Time:   {elapsed:.2f}s")
    print(f"Result: {result.size} {result.mode}")
    
    del result
    gc.collect()
    time.sleep(1)
    final = psutil.Process(pid).memory_info().rss / (1024 * 1024)
    print(f"After gc: {final:.1f} MB")
    
    return {
        "size": size,
        "before_mb": before,
        "after_mb": after,
        "peak_mb": results.get('peak_mb', 0),
        "cpu_peak": results.get('cpu_peak', 0),
        "time_s": elapsed,
        "final_mb": final
    }

if __name__ == "__main__":
    print("=" * 60)
    print("HIGH-RESOLUTION MEMORY & CPU TEST (Optimized Settings)")
    print("Settings: intra_op=2, inter_op=1, ORT_SEQUENTIAL, enable_cpu_mem_arena=False")
    print("=" * 60)
    
    resolutions = [
        ((512, 512), "Small"),
        ((1024, 1024), "Medium"),
        ((2048, 2048), "Large"),
        ((4096, 4096), "4K"),
    ]
    
    results = []
    for size, label in resolutions:
        try:
            r = test_inference_directly(size, label)
            results.append(r)
        except Exception as e:
            print(f"FAILED: {e}")
            import traceback
            traceback.print_exc()
        
        time.sleep(2)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"{'Resolution':<15} {'Before':>8} {'Peak':>8} {'After':>8} {'Final':>8} {'CPU Peak':>9} {'Time':>6}")
    print("-" * 75)
    for r in results:
        print(f"{str(r['size']):<15} {r['before_mb']:>7.1f} {r['peak_mb']:>7.1f} {r['after_mb']:>7.1f} {r['final_mb']:>7.1f} {r['cpu_peak']:>8.1f}% {r['time_s']:>5.1f}s")