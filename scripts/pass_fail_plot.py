import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("results/normalized_samples.csv")

counts = df["status"].value_counts()

counts.plot(kind="bar")

plt.xlabel("QC status")
plt.ylabel("Sample count")
plt.title("Normalization QC")

plt.savefig("results/pass_fail.png")