import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# ECHOCHAIN - SYNTHETIC WARRANTY / REPAIR EVENT GENERATOR
# OPTIMIZED VERSION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

PRODUCT_FILE = BASE_DIR / "data" / "synthetic" / "products.csv"
BOM_FILE = BASE_DIR / "data" / "synthetic" / "bom.csv"

OUTPUT_DIR = BASE_DIR / "data" / "synthetic"
OUTPUT_FILE = OUTPUT_DIR / "warranty_repairs.csv"


# ============================================================
# 1. LOAD DATA
# ============================================================

print("Loading EchoChain product master...", flush=True)

products = pd.read_csv(PRODUCT_FILE)

print(f"Products loaded: {len(products):,}", flush=True)

print("Loading EchoChain BOM...", flush=True)

bom = pd.read_csv(BOM_FILE)

print(f"BOM records loaded: {len(bom):,}", flush=True)


# ============================================================
# 2. BASIC VALIDATION
# ============================================================

print("\nValidating input datasets...", flush=True)

print(
    f"Unique product SKUs : {products['sku'].nunique():,}",
    flush=True
)

print(
    f"Unique BOM records  : {len(bom.drop_duplicates()):,}",
    flush=True
)

print(
    f"BOM SKUs            : {bom['sku'].nunique():,}",
    flush=True
)


# ============================================================
# 3. REPRODUCIBILITY
# ============================================================

rng = np.random.default_rng(42)


# ============================================================
# 4. COMPONENT FAILURE PROBABILITIES
# ============================================================

failure_probability = {
    "Motherboard": 0.18,
    "Battery": 0.15,
    "Display": 0.09,
    "Keyboard": 0.07,
    "SSD": 0.06,
    "RAM": 0.04
}


# ============================================================
# 5. FAILURE TYPES
# ============================================================

failure_types = {
    "Motherboard": [
        "Power failure",
        "Boot failure",
        "System instability",
        "Charging circuit failure"
    ],

    "Battery": [
        "Battery degradation",
        "Battery not charging",
        "Rapid battery drain",
        "Battery swelling"
    ],

    "Display": [
        "Screen flickering",
        "Display failure",
        "Dead pixels",
        "Backlight failure"
    ],

    "Keyboard": [
        "Key failure",
        "Keyboard not responding",
        "Liquid damage",
        "Multiple keys malfunctioning"
    ],

    "SSD": [
        "Storage failure",
        "Read/write errors",
        "Drive not detected",
        "Performance degradation"
    ],

    "RAM": [
        "Memory error",
        "System crashes",
        "RAM module failure",
        "Memory instability"
    ]
}


# ============================================================
# 6. REPAIR STATUS
# ============================================================

repair_statuses = [
    "Repaired",
    "Component Replaced",
    "End of Life"
]


# ============================================================
# 7. PREPARE PRODUCT DATA
# ============================================================

print("\nPreparing product data...", flush=True)

product_columns = [
    "product_id",
    "sku",
    "release_year",
    "warranty_months"
]

products_small = products[product_columns].copy()


# ============================================================
# 8. MERGE PRODUCT MASTER + BOM
# ============================================================

print(
    "Joining product master with BOM...",
    flush=True
)

# Instead of searching the complete BOM for every product,
# perform ONE merge operation.

merged = bom.merge(
    products_small,
    on="sku",
    how="inner",
    validate="many_to_one"
)

print(
    f"Joined records: {len(merged):,}",
    flush=True
)


# ============================================================
# 9. COMPONENT FAILURE PROBABILITY
# ============================================================

print(
    "Calculating component failure probabilities...",
    flush=True
)

merged["failure_probability"] = (
    merged["component_type"]
    .map(failure_probability)
)


# Validate that every component has a probability

missing_probability = (
    merged["failure_probability"]
    .isna()
    .sum()
)

if missing_probability > 0:

    missing_components = (
        merged.loc[
            merged["failure_probability"].isna(),
            "component_type"
        ]
        .dropna()
        .unique()
    )

    raise ValueError(
        "Missing failure probabilities for components: "
        f"{list(missing_components)}"
    )


# ============================================================
# 10. SIMULATE COMPONENT FAILURES
# ============================================================

print(
    "Simulating component failures...",
    flush=True
)

random_values = rng.random(len(merged))

failed_mask = (
    random_values
    <= merged["failure_probability"].to_numpy()
)

repairs = merged.loc[
    failed_mask
].copy()

print(
    f"Potential repair events: {len(repairs):,}",
    flush=True
)


# ============================================================
# 11. GENERATE FAILURE DATES
# ============================================================

print(
    "Generating failure dates...",
    flush=True
)

release_dates = pd.to_datetime(
    repairs["release_year"].astype(str) + "-01-01"
)

# Products released before 2020 start simulation in 2020.
simulation_start_dates = release_dates.where(
    release_dates.dt.year >= 2020,
    pd.Timestamp("2020-01-01")
)

simulation_end = pd.Timestamp(
    "2026-08-31"
)

days_range = (
    simulation_end - simulation_start_dates
).dt.days

days_range = days_range.clip(lower=0)

random_days = np.floor(
    rng.random(len(repairs))
    * (days_range.to_numpy() + 1)
).astype(int)

repairs["failure_date"] = (
    simulation_start_dates
    + pd.to_timedelta(
        random_days,
        unit="D"
    )
)


# ============================================================
# 12. GENERATE FAILURE TYPES
# ============================================================

print(
    "Generating failure types...",
    flush=True
)

def choose_failure_type(component_type):

    return rng.choice(
        failure_types[component_type]
    )


repairs["failure_type"] = (
    repairs["component_type"]
    .map(choose_failure_type)
)


# ============================================================
# 13. GENERATE REPAIR STATUS
# ============================================================

print(
    "Generating repair statuses...",
    flush=True
)

status_random = rng.random(
    len(repairs)
)

repairs["repair_status"] = np.select(
    [
        status_random < 0.70,
        status_random < 0.95
    ],
    [
        "Component Replaced",
        "Repaired"
    ],
    default="End of Life"
)


# ============================================================
# 14. REPAIR COST
# ============================================================

print(
    "Calculating repair costs...",
    flush=True
)

repairs["replacement_cost"] = (
    pd.to_numeric(
        repairs["replacement_cost"],
        errors="coerce"
    )
)

cost_random = rng.random(
    len(repairs)
)

repairs["repair_cost"] = np.where(

    repairs["repair_status"]
    == "Component Replaced",

    repairs["replacement_cost"],

    np.where(

        repairs["repair_status"]
        == "Repaired",

        repairs["replacement_cost"]
        * (
            0.25
            + cost_random * (0.60 - 0.25)
        ),

        repairs["replacement_cost"]
        * (
            0.05
            + cost_random * (0.20 - 0.05)
        )
    )
)

repairs["repair_cost"] = (
    repairs["repair_cost"]
    .round(2)
)

repairs["replacement_cost"] = (
    repairs["replacement_cost"]
    .round(2)
)


# ============================================================
# 15. DOWNTIME
# ============================================================

print(
    "Generating downtime values...",
    flush=True
)

downtime_ranges = {

    "Motherboard": (5, 15),
    "Display": (3, 9),
    "Battery": (1, 4),
    "SSD": (2, 7),
    "RAM": (1, 4),
    "Keyboard": (1, 5)
}


def generate_downtime(component_type):

    low, high = downtime_ranges.get(
        component_type,
        (1, 5)
    )

    return int(
        rng.integers(
            low,
            high + 1
        )
    )


repairs["downtime_days"] = (
    repairs["component_type"]
    .map(generate_downtime)
)


# ============================================================
# 16. WARRANTY CLAIM
# ============================================================

print(
    "Calculating warranty claims...",
    flush=True
)

failure_age_days = (
    repairs["failure_date"]
    - pd.to_datetime(
        repairs["release_year"].astype(str)
        + "-01-01"
    )
).dt.days

warranty_limit_days = (
    repairs["warranty_months"]
    * 30
)

repairs["warranty_claim"] = (
    failure_age_days
    <= warranty_limit_days
)


# ============================================================
# 17. FAILURE DESCRIPTION
# ============================================================

repairs["failure_description"] = (
    repairs["failure_type"]
    + " reported for "
    + repairs["component_type"].str.lower()
    + "."
)


# ============================================================
# 18. CREATE REPAIR ID
# ============================================================

print(
    "Creating repair IDs...",
    flush=True
)

repairs["repair_id"] = [
    f"R{i:07d}"
    for i in range(
        1,
        len(repairs) + 1
    )
]


# ============================================================
# 19. SELECT FINAL COLUMNS
# ============================================================

final_columns = [

    "repair_id",
    "product_id",
    "sku",
    "component_id",
    "component_type",
    "failure_date",
    "failure_type",
    "failure_description",
    "repair_status",
    "repair_cost",
    "replacement_cost",
    "downtime_days",
    "warranty_claim"
]

repairs = repairs[final_columns].copy()


# Format date

repairs["failure_date"] = (
    repairs["failure_date"]
    .dt.strftime("%Y-%m-%d")
)


# ============================================================
# 20. SAVE DATASET
# ============================================================

print(
    "\nSaving warranty/repair dataset...",
    flush=True
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

repairs.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# 21. VALIDATION
# ============================================================

print("\n======================================")
print("ECHOCHAIN WARRANTY / REPAIR DATASET")
print("======================================")

print(
    f"Repair events       : "
    f"{len(repairs):,}"
)

print(
    f"Products affected   : "
    f"{repairs['product_id'].nunique():,}"
)

print(
    f"Components affected : "
    f"{repairs['component_id'].nunique():,}"
)

print(
    f"Unique repair IDs   : "
    f"{repairs['repair_id'].nunique():,}"
)

print(
    f"Output file         : "
    f"{OUTPUT_FILE}"
)


# ============================================================
# 22. FAILURE DISTRIBUTION
# ============================================================

print("\nFailure distribution:")

print(
    repairs["component_type"]
    .value_counts()
)


# ============================================================
# 23. REPAIR STATUS DISTRIBUTION
# ============================================================

print("\nRepair status distribution:")

print(
    repairs["repair_status"]
    .value_counts()
)


# ============================================================
# 24. WARRANTY CLAIM DISTRIBUTION
# ============================================================

print("\nWarranty claims:")

print(
    repairs["warranty_claim"]
    .value_counts()
)


# ============================================================
# 25. DUPLICATE CHECK
# ============================================================

print("\nDuplicate repair IDs:")

print(
    repairs["repair_id"]
    .duplicated()
    .sum()
)


print("\nDuplicate repair records:")

print(
    repairs.duplicated().sum()
)


# ============================================================
# 26. MISSING VALUES
# ============================================================

print("\nMissing values:")

print(
    repairs.isna()
    .sum()
    .sort_values(
        ascending=False
    )
)


# ============================================================
# 27. SAMPLE RECORDS
# ============================================================

print("\nSample repair records:")

print(
    repairs.head(10)
    .to_string(index=False)
)


print("\n======================================")
print("DONE!")
print("======================================")
