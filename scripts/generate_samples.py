import pandas as pd
import random

samples = []

for i in range(1, 25):
    samples.append({
        "sample_id": f"S{i:02}",
        "conc_ng_ul": round(random.uniform(4, 35), 1),
        "volume_ul": round(random.uniform(8, 40), 1)
    })

df = pd.DataFrame(samples)

df.to_csv("data/raw/sample_sheet.csv", index=False)

print(df.head())
print("Generated:", len(df))