import pandas as pd

TARGET_CONC = 10
FINAL_VOLUME = 20

df = pd.read_csv("data/raw/sample_sheet.csv")

required_sample_volume = []
buffer_volume = []
status = []

for _, row in df.iterrows():

    conc = row["conc_ng_ul"]
    available_volume = row["volume_ul"]

    sample_volume = (TARGET_CONC * FINAL_VOLUME) / conc
    buffer = FINAL_VOLUME - sample_volume

    if sample_volume > available_volume:
        qc = "FAIL"
    else:
        qc = "PASS"

    required_sample_volume.append(round(sample_volume, 2))
    buffer_volume.append(round(buffer, 2))
    status.append(qc)

df["sample_volume_ul"] = required_sample_volume
df["buffer_volume_ul"] = buffer_volume
df["status"] = status

print(df.head())

df.to_csv("results/normalized_samples.csv", index=False)