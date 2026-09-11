import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

PRODUCT_FILE = BASE_DIR / "data" / "synthetic" / "products.csv"
BOM_FILE = BASE_DIR / "data" / "synthetic" / "bom.csv"
REPAIR_FILE = BASE_DIR / "data" / "synthetic" / "warranty_repairs.csv"

OUTPUT_DIR = BASE_DIR / "analytics"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 60)
print("EchoChain Analytics Data Preparation")
print("=" * 60)

print("\nLoading Product Master...")
products = pd.read_csv(PRODUCT_FILE)
print(f"Products loaded: {len(products):,}")

print("\nLoading BOM...")
bom = pd.read_csv(BOM_FILE)
print(f"BOM records loaded: {len(bom):,}")

print("\nLoading Warranty/Repair data...")
repairs = pd.read_csv(REPAIR_FILE)
print(f"Repair events loaded: {len(repairs):,}")


# ============================================================
# 1. DIM_PRODUCT
# ============================================================

print("\n" + "-" * 60)
print("Creating DIM_PRODUCT...")
print("-" * 60)

dim_product = products.copy()

dim_product.to_csv(
    OUTPUT_DIR / "dim_product.csv",
    index=False
)

print(f"DIM_PRODUCT rows: {len(dim_product):,}")


# ============================================================
# 2. DIM_COMPONENT
# ============================================================

print("\n" + "-" * 60)
print("Creating DIM_COMPONENT...")
print("-" * 60)

dim_component = bom.copy()

dim_component.to_csv(
    OUTPUT_DIR / "dim_component.csv",
    index=False
)

print(f"DIM_COMPONENT rows: {len(dim_component):,}")


# ============================================================
# 3. DIM_DATE
# ============================================================

print("\n" + "-" * 60)
print("Creating DIM_DATE...")
print("-" * 60)

repairs["failure_date"] = pd.to_datetime(
    repairs["failure_date"]
)

min_date = repairs["failure_date"].min()
max_date = repairs["failure_date"].max()

date_range = pd.date_range(
    start=min_date,
    end=max_date,
    freq="D"
)

dim_date = pd.DataFrame({
    "date": date_range
})

dim_date["date_key"] = (
    dim_date["date"].dt.strftime("%Y%m%d").astype(int)
)

dim_date["year"] = dim_date["date"].dt.year
dim_date["quarter"] = "Q" + dim_date["date"].dt.quarter.astype(str)
dim_date["month"] = dim_date["date"].dt.month
dim_date["month_name"] = dim_date["date"].dt.month_name()
dim_date["week"] = dim_date["date"].dt.isocalendar().week.astype(int)
dim_date["day"] = dim_date["date"].dt.day
dim_date["day_name"] = dim_date["date"].dt.day_name()

dim_date = dim_date[
    [
        "date_key",
        "date",
        "year",
        "quarter",
        "month",
        "month_name",
        "week",
        "day",
        "day_name"
    ]
]

dim_date.to_csv(
    OUTPUT_DIR / "dim_date.csv",
    index=False
)

print(f"Date range: {min_date.date()} → {max_date.date()}")
print(f"DIM_DATE rows: {len(dim_date):,}")


# ============================================================
# 4. FACT_WARRANTY_REPAIR
# ============================================================

print("\n" + "-" * 60)
print("Creating FACT_WARRANTY_REPAIR...")
print("-" * 60)

fact = repairs.copy()


# ------------------------------------------------------------
# Join Product information
# ------------------------------------------------------------

product_columns = [
    "product_id",
    "sku",
    "brand",
    "model",
    "product_family",
    "release_year",
    "warranty_months",
    "msrp"
]

product_lookup = products[product_columns].copy()

fact = fact.merge(
    product_lookup,
    on=["product_id", "sku"],
    how="left",
    validate="many_to_one"
)


# ------------------------------------------------------------
# Join BOM information
# ------------------------------------------------------------

component_columns = [
    "sku",
    "component_id",
    "component_type",
    "component_cost",
    "repairability_score",
    "recyclability_score",
    "replacement_cost",
    "estimated_resale_value"
]

component_lookup = bom[component_columns].copy()

fact = fact.merge(
    component_lookup,
    on=["sku", "component_id"],
    how="left",
    suffixes=("", "_bom"),
    validate="many_to_one"
)


# ============================================================
# DERIVED ANALYTICAL COLUMNS
# ============================================================

print("Creating derived analytical fields...")


# ------------------------------------------------------------
# Date fields
# ------------------------------------------------------------

fact["failure_year"] = fact["failure_date"].dt.year
fact["failure_month"] = fact["failure_date"].dt.month
fact["failure_quarter"] = (
    "Q" + fact["failure_date"].dt.quarter.astype(str)
)

fact["date_key"] = (
    fact["failure_date"]
    .dt.strftime("%Y%m%d")
    .astype(int)
)


# ------------------------------------------------------------
# Product age
# ------------------------------------------------------------

fact["product_age_years"] = (
    fact["failure_date"].dt.year
    - fact["release_year"]
)

fact["product_age_years"] = (
    fact["product_age_years"].clip(lower=0)
)


# ------------------------------------------------------------
# Warranty status
# ------------------------------------------------------------

warranty_end_date = (
    pd.to_datetime(
        fact["release_year"].astype(str) + "-01-01"
    )
    + pd.to_timedelta(
        fact["warranty_months"] * 30,
        unit="D"
    )
)

fact["warranty_status"] = np.where(
    fact["failure_date"] <= warranty_end_date,
    "Under Warranty",
    "Out of Warranty"
)


# ------------------------------------------------------------
# Cost analysis
# ------------------------------------------------------------

fact["cost_difference"] = (
    fact["replacement_cost_bom"]
    - fact["repair_cost"]
)


fact["repair_vs_replacement_ratio"] = np.where(
    fact["replacement_cost_bom"] > 0,
    fact["repair_cost"] /
    fact["replacement_cost_bom"],
    np.nan
)


# ============================================================
# CLEAN COLUMN NAMES
# ============================================================

# The BOM replacement cost is the authoritative component
# replacement cost in the analytical fact table.

fact = fact.rename(
    columns={
        "replacement_cost_bom": "bom_replacement_cost"
    }
)


# ============================================================
# REORDER COLUMNS
# ============================================================

preferred_columns = [
    "repair_id",
    "product_id",
    "sku",
    "component_id",
    "component_type",

    "failure_date",
    "date_key",
    "failure_year",
    "failure_month",
    "failure_quarter",

    "failure_type",
    "failure_description",

    "repair_status",
    "warranty_claim",
    "warranty_status",

    "release_year",
    "product_age_years",
    "warranty_months",

    "repair_cost",
    "replacement_cost",
    "bom_replacement_cost",
    "cost_difference",
    "repair_vs_replacement_ratio",

    "downtime_days",

    "component_cost",
    "repairability_score",
    "recyclability_score",
    "estimated_resale_value",

    "brand",
    "model",
    "product_family",
    "msrp"
]

# Keep only columns that actually exist
preferred_columns = [
    col for col in preferred_columns
    if col in fact.columns
]

remaining_columns = [
    col for col in fact.columns
    if col not in preferred_columns
]

fact = fact[
    preferred_columns + remaining_columns
]


# ============================================================
# SAVE FACT TABLE
# ============================================================

fact.to_csv(
    OUTPUT_DIR / "fact_warranty_repair.csv",
    index=False
)

print(f"FACT_WARRANTY_REPAIR rows: {len(fact):,}")


# ============================================================
# VALIDATION
# ============================================================

print("\n" + "=" * 60)
print("ANALYTICS DATA VALIDATION")
print("=" * 60)

print(
    f"\nDIM_PRODUCT:           {len(dim_product):,} rows"
)

print(
    f"DIM_COMPONENT:        {len(dim_component):,} rows"
)

print(
    f"DIM_DATE:             {len(dim_date):,} rows"
)

print(
    f"FACT_WARRANTY_REPAIR: {len(fact):,} rows"
)


# Check missing joins
product_missing = fact["brand"].isna().sum()
component_missing = fact["component_cost"].isna().sum()

print(
    f"\nMissing Product joins:   {product_missing:,}"
)

print(
    f"Missing Component joins: {component_missing:,}"
)

# Check duplicate keys
print(
    f"\nDuplicate Product IDs: "
    f"{dim_product['product_id'].duplicated().sum():,}"
)

print(
    f"Duplicate Repair IDs: "
    f"{fact['repair_id'].duplicated().sum():,}"
)


if product_missing == 0 and component_missing == 0:
    print("\n✓ All Product and BOM joins successful.")
else:
    print("\n⚠ Some joins failed. Investigate before Power BI.")


print("\n" + "=" * 60)
print("ANALYTICS DATA PREPARATION COMPLETE")
print("=" * 60)

print("\nGenerated files:")

for file in sorted(OUTPUT_DIR.glob("*.csv")):
    print(f"  ✓ {file.name}")
