import pandas as pd
import re
from pathlib import Path


# ============================================================
# ECHOCHAIN - PRODUCT MASTER GENERATOR
# ============================================================

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "raw" / "Computer_prices_all.csv"
OUTPUT_DIR = BASE_DIR / "data" / "synthetic"
OUTPUT_FILE = OUTPUT_DIR / "products.csv"


# ============================================================
# 1. LOAD SOURCE DATA
# ============================================================

print("Loading computer dataset...")

df = pd.read_csv(INPUT_FILE)

print(f"Source records: {len(df):,}")


# ============================================================
# 2. KEEP LAPTOPS ONLY
# ============================================================

products = df[
    df["device_type"]
    .astype(str)
    .str.strip()
    .str.lower()
    .eq("laptop")
].copy()

print(f"Laptop records: {len(products):,}")


# ============================================================
# 3. CLEAN BRAND AND MODEL
# ============================================================

products["brand"] = (
    products["brand"]
    .astype(str)
    .str.strip()
)

products["model"] = (
    products["model"]
    .astype(str)
    .str.strip()
)


# ============================================================
# 4. CREATE PRODUCT FAMILY
# ============================================================

def create_product_family(row):
    """
    Creates a normalized product family.

    Example:
        Lenovo ThinkPad X1 Carbon Gen 9
        ->
        ThinkPad X1 Carbon
    """

    brand = row["brand"]
    model = row["model"]

    # Remove brand from the beginning of model
    family = re.sub(
        rf"^{re.escape(brand)}\s+",
        "",
        model,
        flags=re.IGNORECASE
    )

    # Remove generation-style identifiers
    family = re.sub(
        r"\b(gen(?:eration)?)[\s\-]*\d+\b",
        "",
        family,
        flags=re.IGNORECASE
    )

    # Remove trailing random model codes
    family = re.sub(
        r"\s+[A-Z0-9]{2,4}$",
        "",
        family
    )

    family = re.sub(r"\s+", " ", family).strip()

    return family


products["product_family"] = products.apply(
    create_product_family,
    axis=1
)


# ============================================================
# 5. CREATE ECHOCHAIN PRODUCT ID
# ============================================================

products = products.reset_index(drop=True)

products["product_id"] = (
    "P"
    + (products.index + 1)
    .astype(str)
    .str.zfill(6)
)


# ============================================================
# 6. CREATE UNIQUE ECHOCHAIN SKU
# ============================================================

def clean_sku_text(value):
    value = str(value).upper()

    value = re.sub(
        r"[^A-Z0-9]+",
        "-",
        value
    )

    value = re.sub(
        r"-+",
        "-",
        value
    )

    return value.strip("-")


def generate_sku(row):

    # Use the actual model instead of only product family
    model = clean_sku_text(row["model"])

    release_year = str(
        int(row["release_year"])
    )

    return f"LP-{model}-{release_year}"


products["sku"] = products.apply(
    generate_sku,
    axis=1
)

# ============================================================
# 7. SELECT ECHOCHAIN PRODUCT COLUMNS
# ============================================================

product_columns = [
    "product_id",
    "sku",
    "brand",
    "model",
    "product_family",
    "device_type",
    "release_year",
    "os",
    "form_factor",

    "cpu_brand",
    "cpu_model",
    "cpu_tier",
    "cpu_cores",
    "cpu_threads",
    "cpu_base_ghz",
    "cpu_boost_ghz",

    "gpu_brand",
    "gpu_model",
    "gpu_tier",
    "vram_gb",

    "ram_gb",
    "storage_type",
    "storage_gb",
    "storage_drive_count",

    "display_type",
    "display_size_in",
    "resolution",
    "refresh_hz",

    "battery_wh",
    "charger_watts",

    "weight_kg",
    "warranty_months",

    "price"
]


products = products[product_columns]


# ============================================================
# 8. RENAME MSRP
# ============================================================

products = products.rename(
    columns={
        "price": "msrp"
    }
)


# ============================================================
# 9. REMOVE DUPLICATE PRODUCTS
# ============================================================

before = len(products)

products = products.drop_duplicates(
    subset=["brand", "model"],
    keep="first"
)

after = len(products)

print(
    f"Removed duplicate product definitions: "
    f"{before - after:,}"
)


# ============================================================
# 10. REGENERATE PRODUCT IDs AFTER DEDUPLICATION
# ============================================================

products = products.reset_index(drop=True)

products["product_id"] = (
    "P"
    + (products.index + 1)
    .astype(str)
    .str.zfill(6)
)


# ============================================================
# 11. CREATE OUTPUT DIRECTORY
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# 12. SAVE PRODUCTS
# ============================================================

products.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# 13. VALIDATION
# ============================================================

print("\n======================================")
print("ECHOCHAIN PRODUCT MASTER CREATED")
print("======================================")

print(f"Products created : {len(products):,}")
print(f"Output file      : {OUTPUT_FILE}")

print("\nBrands:")
print(products["brand"].value_counts())

print("\nSample products:")
print(
    products[
        [
            "product_id",
            "sku",
            "brand",
            "model",
            "product_family",
            "release_year",
            "msrp"
        ]
    ].head(10).to_string(index=False)
)

print("\nDuplicate SKUs:")
print(
    products["sku"].duplicated().sum()
)

print("\nMissing values:")
print(
    products.isna().sum().sort_values(
        ascending=False
    ).head(10)
)

print("\nDone!")
