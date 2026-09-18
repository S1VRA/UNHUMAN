#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Memory baseline measurement for NH Mod Tool.

Measures:
- Working Set (WS)
- Private Bytes
- Commit Size
- RSS (Resident Set Size)
- CPU usage

Run with: python memory_baseline.py [--exe PATH_TO_EXE] [--iterations N]
"""

import os
import sys
import time
import subprocess
import threading
import json
import argparse
from pathlib import Path

try:
    import psutil
except ImportError:
    print("Installing psutil...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
    import psutil


def get_process_memory(pid):
    """Get memory info for a process."""
    try:
        p = psutil.Process(pid)
        mem = p.memory_info()
        full = p.memory_full_info()
        return {
            "pid": pid,
            "rss_mb": mem.rss / (1024 * 1024),
            "vms_mb": mem.vms / (1024 * 1024),
            "working_set_mb": getattr(mem, 'rss', 0) / (1024 * 1024),  # On Windows, rss == working set
            "private_mb": getattr(full, 'uss', mem.rss) / (1024 * 1024),
            "commit_mb": getattr(full, 'pss', mem.vms) / (1024 * 1024),
            "cpu_percent": p.cpu_percent(interval=None),
            "num_threads": p.num_threads(),
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


def find_nhmodtool_process(exe_path=None):
    """Find the NHModTool process."""
    for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
        try:
            if exe_path and proc.info['exe']:
                if os.path.samefile(proc.info['exe'], exe_path):
                    return proc.info['pid']
            elif proc.info['name'] and 'NHModTool' in proc.info['name']:
                return proc.info['pid']
            elif proc.info['cmdline']:
                cmd = ' '.join(proc.info['cmdline'])
                if 'NHModTool' in cmd:
                    return proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
            continue
    return None


def measure_memory(pid, duration=10, interval=0.5, label=""):
    """Measure memory over time."""
    print(f"\n=== {label} ===")
    print(f"Monitoring PID {pid} for {duration}s...")
    
    measurements = []
    peak = {"rss_mb": 0, "working_set_mb": 0, "private_mb": 0}
    
    start = time.time()
    while time.time() - start < duration:
        m = get_process_memory(pid)
        if m:
            measurements.append(m)
            for key in peak:
                if m.get(key, 0) > peak[key]:
                    peak[key] = m[key]
            print(f"  RSS: {m['rss_mb']:.1f} MB  WS: {m['working_set_mb']:.1f} MB  "
                  f"Priv: {m['private_mb']:.1f} MB  Threads: {m['num_threads']}  "
                  f"CPU: {m['cpu_percent']:.1f}%")
        time.sleep(interval)
    
    if measurements:
        avg = {
            "rss_mb": sum(m['rss_mb'] for m in measurements) / len(measurements),
            "working_set_mb": sum(m['working_set_mb'] for m in measurements) / len(measurements),
            "private_mb": sum(m['private_mb'] for m in measurements) / len(measurements),
        }
        print(f"\n  AVERAGE:  RSS: {avg['rss_mb']:.1f} MB  WS: {avg['working_set_mb']:.1f} MB  "
              f"Priv: {avg['private_mb']:.1f} MB")
        print(f"  PEAK:     RSS: {peak['rss_mb']:.1f} MB  WS: {peak['working_set_mb']:.1f} MB  "
              f"Priv: {peak['private_mb']:.1f} MB")
    
    return {
        "measurements": measurements,
        "peak": peak,
        "avg": avg if measurements else {}
    }


def launch_app(exe_path):
    """Launch the app and return PID."""
    if exe_path.endswith('.exe'):
        proc = subprocess.Popen([exe_path], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    else:
        proc = subprocess.Popen([sys.executable, exe_path], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    
    # Wait for process to appear
    for _ in range(50):
        pid = find_nhmodtool_process(exe_path)
        if pid:
            return pid, proc
        time.sleep(0.1)
    return None, proc


def run_baseline_tests(exe_path, iterations=10):
    """Run all baseline memory tests."""
    results = {}
    
    print("=" * 60)
    print("NH MOD TOOL - MEMORY BASELINE")
    print("=" * 60)
    print(f"Target: {exe_path}")
    print(f"Iterations for leak test: {iterations}")
    
    # TEST 0: STARTUP
    print("\n\n>>> TEST 0: STARTUP")
    pid, proc = launch_app(exe_path)
    if not pid:
        print("FAILED: Could not find process")
        return results
    
    print(f"Launched PID: {pid}")
    time.sleep(2)  # Let it settle
    results['startup'] = measure_memory(pid, duration=8, label="BASELINE (startup)")
    
    # Keep process running for subsequent tests
    print("\n[Process kept running for subsequent tests...]")
    
    # Note: For full automated testing we'd need to control the GUI
    # This script measures the baseline; manual GUI interaction needed for other tests
    print("\n>>> MANUAL TESTS REQUIRED")
    print("Please perform these manually while this script monitors memory:")
    print("  1. Open Photo Mods page, wait for thumbnails (405 images)")
    print("  2. Select an image")
    print("  3. Toggle Remove Background ON, wait for inference")
    print("  4. Toggle OFF, wait")
    print("  5. Toggle ON again (2nd inference)")
    print("  6. Run 10 consecutive inferences")
    print("  7. Test double-click on Remove Background")
    print("  8. Test high-res image")
    print("  9. Exit app")
    print("\nPress Ctrl+C when done to save results.")
    
    # Continue monitoring
    try:
        while True:
            m = get_process_memory(pid)
            if m:
                print(f"\r  Live: RSS: {m['rss_mb']:.1f} MB  WS: {m['working_set_mb']:.1f} MB  "
                      f"Priv: {m['private_mb']:.1f} MB  Threads: {m['num_threads']}", end="")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopped.")
    
    # TEST 11: PROCESS EXIT
    print("\n>>> TEST 11: PROCESS EXIT")
    proc.terminate()
    try:
        proc.wait(timeout=5)
        print("Process exited cleanly.")
    except subprocess.TimeoutExpired:
        proc.kill()
        print("Process killed (did not exit cleanly).")
    
    # Check for orphaned processes
    time.sleep(1)
    orphans = []
    for p in psutil.process_iter(['pid', 'name', 'ppid']):
        try:
            if p.info['ppid'] == pid:
                orphans.append(p.info)
        except:
            pass
    if orphans:
        print(f"WARNING: Orphaned child processes: {orphans}")
    else:
        print("No orphaned processes detected.")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="NH Mod Tool Memory Baseline")
    parser.add_argument("--exe", default=r"C:\Users\mehmet\Desktop\UNHUMAN\dist\NHModTool.exe",
                        help="Path to NHModTool.exe")
    parser.add_argument("--iterations", type=int, default=10,
                        help="Number of iterations for leak test")
    args = parser.parse_args()
    
    exe_path = os.path.abspath(args.exe)
    if not os.path.exists(exe_path):
        print(f"EXE not found: {exe_path}")
        sys.exit(1)
    
    results = run_baseline_tests(exe_path, args.iterations)
    
    # Save results
    out_path = os.path.join(os.path.dirname(exe_path), "memory_baseline.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {out_path}")


if __name__ == "__main__":
    main()