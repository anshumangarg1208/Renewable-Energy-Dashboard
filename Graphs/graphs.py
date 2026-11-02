import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv("cleaned_dataset.csv")

sns.set_theme(style="whitegrid")

data = df.groupby("Year")["Renewable energy share in the total final energy consumption (%)"].mean()

plt.figure(figsize=(10, 5))
sns.lineplot(x=data.index, y=data.values, marker="o")
plt.title("Renewable Energy Trend (2000-2020)")
plt.xlabel("Year")
plt.ylabel("Average Renewable Energy Share (%)")
plt.xticks(range(2000, 2021, 2))
plt.tight_layout()
plt.savefig("graph1_renewable_trend.png", dpi=300)
plt.show()

data = df[df["Year"] == 2020]
data = data.sort_values(
    "Electricity from renewables (TWh)", ascending=False
).head(10)
data = data.sort_values("Electricity from renewables (TWh)", ascending=True)

plt.figure(figsize=(10, 6))
sns.barplot(
    data=data,
    x="Electricity from renewables (TWh)",
    y="Entity"
)
plt.title("Top 10 Countries by Renewable Electricity (2020)")
plt.xlabel("Renewable Electricity (TWh)")
plt.ylabel("Country")
plt.tight_layout()
plt.savefig("graph2_top_countries.png", dpi=300)
plt.show()

data = df[df["Year"] == 2020]
data = data[data["Value_co2_emissions_kt_by_country"] > 0]

plt.figure(figsize=(10, 6))
sns.scatterplot(
    data=data,
    x="Renewable energy share in the total final energy consumption (%)",
    y="Value_co2_emissions_kt_by_country",
    alpha=0.7
)
plt.yscale("log")
plt.title("Renewable Energy Share vs CO2 Emissions (2020)")
plt.xlabel("Renewable Energy Share (%)")
plt.ylabel("CO2 Emissions (kt, log scale)")
plt.tight_layout()
plt.savefig("graph3_renewable_vs_co2.png", dpi=300)
plt.show()

data = df.groupby("Year")[
    [
        "Electricity from renewables (TWh)",
        "Electricity from fossil fuels (TWh)"
    ]
].sum()

plt.figure(figsize=(10, 5))
plt.plot(
    data.index,
    data["Electricity from renewables (TWh)"],
    marker="o",
    label="Renewable Electricity"
)
plt.plot(
    data.index,
    data["Electricity from fossil fuels (TWh)"],
    marker="o",
    label="Fossil Fuel Electricity"
)
plt.title("Renewable vs Fossil Fuel Electricity (2000-2020)")
plt.xlabel("Year")
plt.ylabel("Electricity Generation (TWh)")
plt.xticks(range(2000, 2021, 2))
plt.legend()
plt.tight_layout()
plt.savefig("graph4_renewable_vs_fossil.png", dpi=300)
plt.show()

cols = [
    "Renewable energy share in the total final energy consumption (%)",
    "Value_co2_emissions_kt_by_country",
    "Electricity from fossil fuels (TWh)",
    "Electricity from renewables (TWh)",
    "gdp_per_capita",
    "Primary energy consumption per capita (kWh/person)"
]

corr = df[cols].corr()

labels = [
    "Renewable Share",
    "CO2 Emissions",
    "Fossil Electricity",
    "Renewable Electricity",
    "GDP per Capita",
    "Energy Consumption"
]

corr.index = labels
corr.columns = labels

plt.figure(figsize=(11, 8))
sns.heatmap(
    corr,
    annot=True,
    cmap="coolwarm",
    fmt=".2f",
    vmin=-1,
    vmax=1,
    square=True,
    linewidths=0.5,
    cbar_kws={"shrink": 0.8}
)
plt.title("Correlation Between Energy and Economic Indicators", pad=18)
plt.xticks(rotation=35, ha="right")
plt.yticks(rotation=0)
plt.tight_layout()
plt.savefig(
    "graph5_correlation_heatmap.png",
    dpi=300,
    bbox_inches="tight"
)
plt.show()

print("All five graphs generated and saved successfully.")
