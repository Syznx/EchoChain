import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# ECHOCHAIN - SYNTHETIC BOM GENERATOR
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "synthetic" / "products.csv"
OUTPUT_DIR = BASE_DIR / "data" / "synthetic"
OUTPUT_FILE = OUTPUT_DIR / "bom.csv"


# ============================================================
# 1. LOAD PRODUCT MASTER
# ============================================================

print("Loading EchoChain product master...")

products = pd.read_csv(INPUT_FILE)

print(f"Products loaded: {len(products):,}")


# ============================================================
# 2. REPRODUCIBILITY
# ============================================================

np.random.seed(42)


# ============================================================
# 3. COMPONENT DEFINITIONS
# ============================================================

component_types = [
    "Motherboard",
    "Display",
    "Battery",
    "RAM",
    "SSD",
    "Keyboard"
]


# ============================================================
# 4. COMPONENT ID GENERATOR
# ============================================================

component_id_map = {
    "Motherboard": "MB",
    "Display": "DSP",
    "Battery": "BAT",
    "RAM": "RAM",
    "SSD": "SSD",
    "Keyboard": "KBD"
}


# ============================================================
# 5. GENERATE BOM
# ============================================================

bom_records = []


for _, product in products.iterrows():

    sku = product["sku"]
    brand = product["brand"]
    model = product["model"]

    # --------------------------------------------------------
    # Base product price
    # --------------------------------------------------------

    msrp = float(product["msrp"])

    # --------------------------------------------------------
    # Component cost percentages
    # --------------------------------------------------------

    component_cost_pct = {
        "Motherboard": 0.22,
        "Display": 0.18,
        "Battery": 0.08,
        "RAM": 0.07,
        "SSD": 0.09,
        "Keyboard": 0.04
    }

    # --------------------------------------------------------
    # Component weights
    # --------------------------------------------------------

    component_weights = {
        "Motherboard": 0.25,
        "Display": 0.28,
        "Battery": 0.12,
        "RAM": 0.04,
        "SSD": 0.03,
        "Keyboard": 0.06
    }

    # --------------------------------------------------------
    # Component scores
    # --------------------------------------------------------

    component_scores = {
        "Motherboard": {
            "repairability": 4,
            "recyclability": 7
        },

        "Display": {
            "repairability": 6,
            "recyclability": 6
        },

        "Battery": {
            "repairability": 8,
            "recyclability": 5
        },

        "RAM": {
            "repairability": 9,
            "recyclability": 8
        },

        "SSD": {
            "repairability": 8,
            "recyclability": 7
        },

        "Keyboard": {
            "repairability": 7,
            "recyclability": 6
        }
    }

    # --------------------------------------------------------
    # Generate each component
    # --------------------------------------------------------

    for component_type in component_types:

        prefix = component_id_map[component_type]

        component_id = (
            f"{prefix}-"
            f"{sku.replace('LP-', '')}"
        )

        # Component name
        component_name = (
            f"{brand} {component_type} - "
            f"{model}"
        )

        # Manufacturer part number
        manufacturer_part = (
            f"{prefix}-"
            f"{brand[:3].upper()}-"
            f"{np.random.randint(10000, 99999)}"
        )

        # Component cost
        component_cost = round(
            msrp * component_cost_pct[component_type],
            2
        )

        # Small controlled variation
        component_cost *= np.random.uniform(
            0.90,
            1.10
        )

        component_cost = round(
            component_cost,
            2
        )

        # Component weight
        component_weight = round(
            component_weights[component_type]
            * np.random.uniform(0.85, 1.15),
            3
        )

        # Scores
        repairability_score = component_scores[
            component_type
        ]["repairability"]

        recyclability_score = component_scores[
            component_type
        ]["recyclability"]

        # Replacement cost
        replacement_cost = round(
            component_cost
            * np.random.uniform(1.05, 1.25),
            2
        )

        # Estimated resale/recovery value
        estimated_resale_value = round(
            component_cost
            * np.random.uniform(0.20, 0.65),
            2
        )

        bom_records.append({

            "sku": sku,

            "component_id":
                component_id,

            "component_type":
                component_type,

            "component_name":
                component_name,

            "manufacturer_part":
                manufacturer_part,

            "component_cost":
                component_cost,

            "component_weight_kg":
                component_weight,

            "repairability_score":
                repairability_score,

            "recyclability_score":
                recyclability_score,

            "replacement_cost":
                replacement_cost,

            "estimated_resale_value":
                estimated_resale_value
        })


# ============================================================
# 6. CREATE DATAFRAME
# ============================================================

bom = pd.DataFrame(bom_records)


# ============================================================
# 7. CREATE OUTPUT DIRECTORY
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# 8. SAVE BOM
# ============================================================

bom.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# 9. VALIDATION
# ============================================================

print("\n======================================")
print("ECHOCHAIN BOM CREATED")
print("======================================")

print(
    f"Products covered : "
    f"{bom['sku'].nunique():,}"
)

print(
    f"Components       : "
    f"{len(bom):,}"
)

print(
    f"Components/product : "
    f"{len(bom) / bom['sku'].nunique():.0f}"
)

print(
    f"Output file      : "
    f"{OUTPUT_FILE}"
)


print("\nComponent distribution:")

print(
    bom["component_type"]
    .value_counts()
)


print("\nSample BOM records:")

print(
    bom.head(12).to_string(
        index=False
    )
)


print("\nDuplicate component records:")

print(
    bom.duplicated(
        subset=[
            "sku",
            "component_type"
        ]
    ).sum()
)


print("\nMissing values:")

print(
    bom.isna()
    .sum()
    .sort_values(
        ascending=False
    )
    .head(10)
)


print("\nDone!")
