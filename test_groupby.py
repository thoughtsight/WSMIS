import pandas as pd
import time
import numpy as np

df = pd.DataFrame({
    'Location Name': np.random.choice(['A', 'B', 'C', 'D'], 200000),
    'Location Group': np.random.choice(['G1', 'G2'], 200000),
    'Pre-GST Labour': np.random.rand(200000),
    'Labour Discount': np.random.rand(200000)
})

t0 = time.time()
gb = df.groupby('Location Name')
t1 = time.time()
res1 = gb.agg(L=("Pre-GST Labour","sum"), D=("Labour Discount","sum"))
t2 = time.time()
res2 = gb.agg(L=("Pre-GST Labour","sum"), D=("Labour Discount","sum"))
t3 = time.time()

print(f"GroupBy time: {t1-t0:.4f}")
print(f"Agg time 1: {t2-t1:.4f}")
print(f"Agg time 2: {t3-t2:.4f}")

# What if we sum everything?
t4 = time.time()
sum_all = gb.sum(numeric_only=True)
t5 = time.time()
print(f"Sum all time: {t5-t4:.4f}")
