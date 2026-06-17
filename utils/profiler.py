import time
import functools
from collections import defaultdict
import pandas as pd

class Profiler:
    def __init__(self):
        self.timings = defaultdict(list)
        self.aggregations = defaultdict(list)
        self.memory_snapshots = {}
        
    def measure(self, category, name):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start = time.time()
                result = func(*args, **kwargs)
                duration = time.time() - start
                self.timings[category].append((name, duration))
                return result
            return wrapper
        return decorator

    def measure_agg(self, name):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(df, *args, **kwargs):
                start = time.time()
                in_rows = len(df) if hasattr(df, '__len__') else 0
                result = func(df, *args, **kwargs)
                duration = time.time() - start
                out_rows = len(result) if hasattr(result, '__len__') else 0
                self.aggregations[name].append({
                    "time": duration,
                    "in_rows": in_rows,
                    "out_rows": out_rows
                })
                return result
            return wrapper
        return decorator
        
    def get_report(self):
        return self.timings, self.aggregations

profiler = Profiler()

import atexit
import json
@atexit.register
def save_profile():
    with open("profile_results.json", "w") as f:
        json.dump({"timings": profiler.timings, "aggregations": profiler.aggregations}, f, indent=2)
