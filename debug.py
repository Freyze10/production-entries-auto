import sys
import time
import faulthandler
import os

from PyQt6.QtCore import QCoreApplication

# If the script is stuck for 60 seconds, print exactly which line it is stuck on (repeats every 60s)
faulthandler.dump_traceback_later(60, repeat=True)

app = QCoreApplication(sys.argv)

import dbfread
from db import legacy


def check_dbf(label, path, sample=2000):
    print(f"\n--- {label}: {path}", flush=True)
    t = time.time()
    exists = os.path.exists(path)
    print(f"    exists: {exists}  ({time.time() - t:.1f}s)", flush=True)
    if not exists:
        return
    print(f"    size: {os.path.getsize(path) / 1024 / 1024:.1f} MB", flush=True)

    t = time.time()
    dbf = dbfread.DBF(path, encoding='latin1', char_decode_errors='ignore')
    print(f"    opened: {len(dbf)} records ({time.time() - t:.1f}s)", flush=True)

    t = time.time()
    for i, _ in enumerate(dbf, 1):
        if i == sample:
            break
    print(f"    read {i} records in {time.time() - t:.1f}s", flush=True)


# Step 1: test each DBF file separately
check_dbf("Formula items", legacy.FORMULA_ITEMS_DBF_PATH)
check_dbf("Production items", legacy.PRODUCTION_ITEMS_DBF_PATH)
check_dbf("Formula primary", legacy.FORMULA_PRIMARY_DBF_PATH)
check_dbf("Production primary", legacy.PRODUCTION_PRIMARY_DBF_PATH)
check_dbf("RM incoming", legacy.RM_INCOMING)

# Step 2: run the real Sync, no thread, no dialog
print("\n===== RUNNING Sync().run() =====", flush=True)
worker = legacy.Sync()
worker.progress.connect(lambda msg: print(f"[progress] {time.strftime('%H:%M:%S')} {msg}", flush=True))
worker.finished.connect(lambda ok, msg: print(f"[finished] success={ok} | {msg}", flush=True))

start = time.time()
worker.run()
print(f"\nTotal time: {time.time() - start:.1f}s", flush=True)