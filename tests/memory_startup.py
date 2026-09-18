#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick startup memory measurement for NH Mod Tool.
"""

import os
import sys
import time
import subprocess
import psutil

def get_memory_mb(pid):
    try:
        p = psutil.Process(pid)
        mem = p.memory_info()
        return mem.rss / (1024 * 1024)
    except:
        return 0

def measure_startup(exe_path, duration=15):
    print(f"Starting {exe_path}...")
    
    if exe_path.endswith('.exe'):
        proc = subprocess.Popen([exe_path])
    else:
        proc = subprocess.Popen([sys.executable, exe_path])
    
    # Find the process
    pid = None
    for _ in range(100):
        for p in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                if p.info['exe'] and os.path.samefile(p.info['exe'], exe_path):
                    pid = p.info['pid']
                    break
            except:
                pass
        if pid:
            break
        time.sleep(0.1)
    
    if not pid:
        print("Could not find process")
        proc.terminate()
        return
    
    print(f"Found PID: {pid}")
    print(f"Monitoring for {duration} seconds...\n")
    
    peak = 0
    samples = []
    
    start = time.time()
    while time.time() - start < duration:
        rss = get_memory_mb(pid)
        samples.append(rss)
        if rss > peak:
            peak = rss
        elapsed = time.time() - start
        print(f"  t={elapsed:.1f}s  RSS: {rss:.1f} MB  Peak: {peak:.1f} MB")
        time.sleep(0.5)
    
    avg = sum(samples) / len(samples) if samples else 0
    print(f"\n=== STARTUP BASELINE ===")
    print(f"Average RSS: {avg:.1f} MB")
    print(f"Peak RSS:    {peak:.1f} MB")
    print(f"Samples:     {len(samples)}")
    
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except:
        proc.kill()
    
    return {"avg_mb": avg, "peak_mb": peak, "samples": len(samples)}

if __name__ == "__main__":
    exe = r"C:\Users\mehmet\Desktop\UNHUMAN\dist\NHModTool.exe"
    if not os.path.exists(exe):
        print(f"EXE not found: {exe}")
        sys.exit(1)
    
    measure_startup(exe, duration=15)