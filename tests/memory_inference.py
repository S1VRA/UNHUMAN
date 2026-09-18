#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Memory measurement during high-resolution background removal.
Uses the internal _bg_remove_impl function directly.
"""

import os
import sys
import time
import psutil
import threading
import tempfile
from PIL import Image

sys.path.insert(0, r"C:\Users\mehmet\Desktop\UNHUMAN")

import NHModTool as app

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

def test_inference_memory(image_size, label):
    print(f"\n=== {label} ({image_size[0]}x{image_size[1]}) ===")
    
    # Create test image
    img = Image.new("RGB", image_size, (100, 150, 200))
    # Add some pattern
    for x in range(0, image_size[0], 20):
        for y in range(0, image_size[1], 20):
            if (x + y) % 40 == 0:
                for dx in range(min(10, image_size[0] - x)):
                    for dy in range(min(10, image_size[1] - y)):
                        img.putpixel((x + dx, y + dy), (255, 50, 50))
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        img.save(f.name, "PNG")
        temp_path = f.name
    
    try:
        pid = os.getpid()
        print(f"Monitoring PID: {pid}")
        
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
        print(f"Peak:   {results.get('peak', 0):.1f} MB")
        print(f"Avg:    {results.get('avg', 0):.1f} MB")
        print(f"Time:   {elapsed:.2f}s")
        print(f"Result: {result.size} {result.mode}")
        
        # Force cleanup
        del result
        import gc
        gc.collect()
        
        return {
            "size": image_size,
            "before_mb": before,
            "after_mb": after,
            "peak_mb": results.get('peak', 0),
            "avg_mb": results.get('avg', 0),
            "time_s": elapsed
        }
    finally:
        try:
            os.remove(temp_path)
        except:
            pass

if __name__ == "__main__":
    # Reset session to ensure fresh state
    app._BG_SESSION["session"] = None
    
    print("Testing background removal memory at various resolutions...")
    print("=" * 60)
    
    # Test different resolutions
    resolutions = [
        ((160, 160), "Tiny (bgtest size)"),
        ((512, 512), "Small"),
        ((1024, 1024), "Medium"),
        ((2048, 2048), "Large"),
        ((4096, 4096), "Very Large"),
    ]
    
    results = []
    for size, label in resolutions:
        try:
            r = test_inference_memory(size, label)
            results.append(r)
        except Exception as e:
            print(f"FAILED: {e}")
            import traceback
            traceback.print_exc()
        
        # Cool down between tests
        time.sleep(2)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"{'Resolution':<20} {'Before':>8} {'Peak':>8} {'After':>8} {'Delta':>8} {'Time':>6}")
    print("-" * 60)
    for r in results:
        delta = r['peak_mb'] - r['before_mb']
        print(f"{str(r['size']):<20} {r['before_mb']:>7.1f} {r['peak_mb']:>7.1f} {r['after_mb']:>7.1f} {delta:>7.1f} {r['time_s']:>5.1f}s")