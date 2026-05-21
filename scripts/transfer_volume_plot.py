import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("results/normalized_samples.csv")

df["sample_volume_ul"].hist()

plt.xlabel("Required sample volume (uL)")
plt.ylabel("Sample count")
plt.title("Transfer volume distribution")

plt.savefig("results/transfer_volume_distribution.png")