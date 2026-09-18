#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick GUI smoke test - launch app, verify it starts, then close.
"""

import os
import sys
import time
import subprocess
import psutil

def test_gui_launch():
    exe = r"C:\Users\mehmet\Desktop\UNHUMAN\dist\NHModTool.exe"
    print(f"Launching {exe}...")
    
    proc = subprocess.Popen([exe])
    
    # Wait for process to appear
    pid = None
    for _ in range(50):
        for p in psutil.process_iter(['pid', 'exe']):
            try:
                if p.info['exe'] and os.path.samefile(p.info['exe'], exe):
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
        return False
    
    print(f"Found PID: {pid}")
    
    # Monitor for 10 seconds
    print("Monitoring for 10 seconds...")
    peak = 0
    for i in range(20):
        try:
            p = psutil.Process(pid)
            mem = p.memory_info()
            rss = mem.rss / (1024 * 1024)
            if rss > peak:
                peak = rss
            print(f"  t={i*0.5:.1f}s  RSS: {rss:.1f} MB  Peak: {peak:.1f} MB  Threads: {p.num_threads()}")
        except:
            break
        time.sleep(0.5)
    
    # Close gracefully
    print("Closing app...")
    try:
        p = psutil.Process(pid)
        p.terminate()
        p.wait(timeout=5)
        print("App closed cleanly")
    except:
        try:
            p.kill()
            print("App killed")
        except:
            pass
    
    # Check for orphans
    time.sleep(1)
    orphans = []
    for p in psutil.process_iter(['pid', 'ppid']):
        try:
            if p.info['ppid'] == pid:
                orphans.append(p.info)
        except:
            pass
    
    if orphans:
        print(f"WARNING: Orphaned processes: {orphans}")
        return False
    else:
        print("No orphaned processes")
        return True

if __name__ == "__main__":
    ok = test_gui_launch()
    sys.exit(0 if ok else 1)