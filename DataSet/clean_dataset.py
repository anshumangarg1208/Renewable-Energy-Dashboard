import pandas as pd
import numpy as np

INPUT_FILE = "global-data-on-sustainable-energy.csv"
OUTPUT_FILE = "cleaned_dataset.csv"


def load_data():
    df = pd.read_csv(INPUT_FILE, low_memory=False)

    df.columns = (
        df.columns.astype(str)
        .str.replace(r"\\n|\n", " ", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    if "Entity" not in df.columns or "Year" not in df.columns:
        raise ValueError("The CSV must contain Entity and Year columns.")

    df["Entity"] = df["Entity"].astype("string").str.strip()
    df["Entity"] = df["Entity"].replace("", pd.NA)

    for col in df.columns:
        if col != "Entity":
            values = (
                df[col].astype("string")
                .str.replace(",", "", regex=False)
                .str.strip()
                .replace("", pd.NA)
            )
            df[col] = pd.to_numeric(values, errors="coerce")

    return df


def clean_invalid_values(df):
    df = df.dropna(subset=["Entity", "Year"]).copy()
    df["Year"] = df["Year"].astype(int)
    df = df.drop_duplicates().copy()

    duplicate_keys = df.duplicated(
        subset=["Entity", "Year"], keep=False
    )

    if duplicate_keys.any():
        raise ValueError(
            "Duplicate country-year records found. "
            "Review them before continuing."
        )

    percentage_cols = [
        "Access to electricity (% of population)",
        "Access to clean fuels for cooking",
        "Renewable energy share in the total final energy consumption (%)",
        "Low-carbon electricity (% electricity)",
        "Renewables (% equivalent primary energy)"
    ]

    for col in percentage_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

            tiny_over = (df[col] > 100) & (df[col] <= 100.01)
            df.loc[tiny_over, col] = 100

            invalid = (df[col] < 0) | (df[col] > 100)
            df.loc[invalid, col] = np.nan

    non_negative_cols = [
        "Renewable-electricity-generating-capacity-per-capita",
        "Financial flows to developing countries (US $)",
        "Electricity from fossil fuels (TWh)",
        "Electricity from nuclear (TWh)",
        "Electricity from renewables (TWh)",
        "Primary energy consumption per capita (kWh/person)",
        "Energy intensity level of primary energy (MJ/$2017 PPP GDP)",
        "Value_co2_emissions_kt_by_country",
        "gdp_per_capita",
        "Density (P/Km2)",
        "Land Area(Km2)"
    ]

    for col in non_negative_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df.loc[df[col] < 0, col] = np.nan

    if "Latitude" in df.columns:
        df["Latitude"] = pd.to_numeric(
            df["Latitude"], errors="coerce"
        )
        df.loc[
            ~df["Latitude"].between(-90, 90), "Latitude"
        ] = np.nan

    if "Longitude" in df.columns:
        df["Longitude"] = pd.to_numeric(
            df["Longitude"], errors="coerce"
        )
        df.loc[
            ~df["Longitude"].between(-180, 180), "Longitude"
        ] = np.nan

    return df.sort_values(
        ["Entity", "Year"]
    ).reset_index(drop=True)


def fill_missing_values(df):
    static_cols = [
        "Density (P/Km2)",
        "Land Area(Km2)",
        "Latitude",
        "Longitude"
    ]

    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

    for col in numeric_cols:
        if not df[col].isna().any():
            continue

        if col == "Year":
            raise ValueError(
                "Missing Year values found. Review the source data."
            )

        if col in static_cols:
            country_medians = df.groupby("Entity")[col].transform(
                "median"
            )
            df[col] = df[col].fillna(country_medians)

        elif col == "Financial flows to developing countries (US $)":
            country_medians = df.groupby("Entity")[col].transform(
                "median"
            )
            df[col] = df[col].fillna(country_medians)

        else:
            interpolated = df.groupby(
                "Entity", sort=False
            )[col].transform(
                lambda s: s.interpolate(
                    method="linear",
                    limit_area="inside"
                )
            )

            df[col] = df[col].fillna(interpolated)

            country_medians = df.groupby("Entity")[col].transform(
                "median"
            )
            df[col] = df[col].fillna(country_medians)

        if df[col].isna().any():
            overall_median = df[col].median()

            if pd.isna(overall_median):
                raise ValueError(
                    f"Column '{col}' has no valid values to estimate "
                    "its missing entries. Review the source data."
                )

            df[col] = df[col].fillna(overall_median)

    remaining = df.isna().sum()

    if remaining.any():
        raise ValueError(
            "Missing values remain:\n"
            + remaining[remaining > 0].to_string()
        )

    return df


def main():
    df = load_data()
    df = clean_invalid_values(df)
    df = fill_missing_values(df)

    df = df.sort_values(
        ["Entity", "Year"]
    ).reset_index(drop=True)

    if df.duplicated().any():
        raise ValueError("Duplicate rows remain after cleaning.")

    if df.duplicated(subset=["Entity", "Year"]).any():
        raise ValueError("Duplicate country-year records remain.")

    df.to_csv(OUTPUT_FILE, index=False)

    print("\nDATA CLEANING COMPLETED")
    print("Rows:", df.shape[0])
    print("Columns:", df.shape[1])
    print("Missing values:", int(df.isna().sum().sum()))
    print("Duplicate rows:", int(df.duplicated().sum()))
    print("Output file:", OUTPUT_FILE)


if __name__ == "__main__":
    main()