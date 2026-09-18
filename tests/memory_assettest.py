#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Memory measurement during --assettest (UnityPy texture loading).
"""

import os
import sys
import time
import subprocess
import psutil
import threading
import json

def monitor_process(pid, results, stop_event, interval=0.1):
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

def run_assettest_memory(exe_path):
    print(f"Running --assettest on {exe_path}...")
    
    proc = subprocess.Popen([exe_path, "--assettest", os.path.dirname(exe_path)])
    
    pid = None
    for _ in range(50):
        for p in psutil.process_iter(['pid', 'exe']):
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
    
    results = {}
    stop_event = threading.Event()
    monitor_thread = threading.Thread(target=monitor_process, args=(pid, results, stop_event))
    monitor_thread.start()
    
    returncode = proc.wait()
    
    stop_event.set()
    monitor_thread.join(timeout=2)
    
    print(f"\n=== ASSETTEST MEMORY ===")
    print(f"Exit code: {returncode}")
    print(f"Average RSS: {results.get('avg', 0):.1f} MB")
    print(f"Peak RSS:    {results.get('peak', 0):.1f} MB")
    print(f"Samples:     {results.get('samples', 0)}")
    
    report_path = os.path.join(os.path.dirname(exe_path), "assettest_report.json")
    if os.path.exists(report_path):
        with open(report_path, "r") as f:
            report = json.load(f)
        print(f"\nAssetTest result: {'PASS' if report.get('pass') else 'FAIL'}")
        for t in report.get('tests', []):
            print(f"  {t['name']}: {'PASS' if t['pass'] else 'FAIL'} - {t.get('info', '')}")
        if report.get('errors'):
            for e in report['errors']:
                print(f"  ERROR: {e}")
    
    return results

if __name__ == "__main__":
    exe = r"C:\Users\mehmet\Desktop\UNHUMAN\dist\NHModTool.exe"
    if not os.path.exists(exe):
        print(f"EXE not found: {exe}")
        sys.exit(1)
    
    run_assettest_memory(exe)