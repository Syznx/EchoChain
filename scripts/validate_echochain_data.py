import pandas as pd
from pathlib import Path


# ============================================================
# ECHOCHAIN - DATASET RELATIONSHIP VALIDATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

PRODUCT_FILE = BASE_DIR / "data" / "synthetic" / "products.csv"
BOM_FILE = BASE_DIR / "data" / "synthetic" / "bom.csv"
REPAIR_FILE = BASE_DIR / "data" / "synthetic" / "warranty_repairs.csv"


print("=" * 60)
print("ECHOCHAIN DATA VALIDATION")
print("=" * 60)


# ============================================================
# 1. LOAD DATA
# ============================================================

print("\nLoading datasets...")

products = pd.read_csv(PRODUCT_FILE)
bom = pd.read_csv(BOM_FILE)
repairs = pd.read_csv(REPAIR_FILE)

print(f"Products : {len(products):,}")
print(f"BOM      : {len(bom):,}")
print(f"Repairs  : {len(repairs):,}")


# ============================================================
# 2. PRODUCT MASTER VALIDATION
# ============================================================

print("\n" + "=" * 60)
print("1. PRODUCT MASTER VALIDATION")
print("=" * 60)

duplicate_product_ids = products["product_id"].duplicated().sum()
duplicate_skus = products["sku"].duplicated().sum()

print(f"Duplicate product IDs : {duplicate_product_ids:,}")
print(f"Duplicate SKUs        : {duplicate_skus:,}")

if duplicate_product_ids == 0 and duplicate_skus == 0:
    print("PASS - Product master uniqueness is valid.")
else:
    print("FAIL - Duplicate products or SKUs detected.")


# ============================================================
# 3. BOM VALIDATION
# ============================================================

print("\n" + "=" * 60)
print("2. BOM VALIDATION")
print("=" * 60)

duplicate_bom_records = bom.duplicated().sum()

print(
    f"Duplicate BOM records : "
    f"{duplicate_bom_records:,}"
)

if duplicate_bom_records == 0:
    print("PASS - No duplicate BOM records.")
else:
    print("FAIL - Duplicate BOM records detected.")


# ============================================================
# 4. BOM COMPONENT COUNT
# ============================================================

print("\nChecking components per SKU...")

components_per_sku = (
    bom.groupby("sku")
    .size()
)

print(
    f"Minimum components per SKU : "
    f"{components_per_sku.min()}"
)

print(
    f"Maximum components per SKU : "
    f"{components_per_sku.max()}"
)

invalid_component_counts = (
    components_per_sku != 6
).sum()

print(
    f"SKUs not having 6 components : "
    f"{invalid_component_counts:,}"
)

if invalid_component_counts == 0:
    print("PASS - Every SKU has exactly 6 BOM components.")
else:
    print("FAIL - Some SKUs do not have exactly 6 components.")


# ============================================================
# 5. BOM SKU → PRODUCT VALIDATION
# ============================================================

print("\nChecking BOM SKUs against product master...")

product_skus = set(products["sku"])
bom_skus = set(bom["sku"])

orphan_bom_skus = bom_skus - product_skus

print(
    f"BOM SKUs without product master match : "
    f"{len(orphan_bom_skus):,}"
)

if len(orphan_bom_skus) == 0:
    print("PASS - Every BOM SKU exists in product master.")
else:
    print("FAIL - Orphan BOM SKUs detected.")


# ============================================================
# 6. REPAIR PRODUCT VALIDATION
# ============================================================

print("\n" + "=" * 60)
print("3. WARRANTY / REPAIR VALIDATION")
print("=" * 60)

product_ids = set(products["product_id"])

invalid_repair_products = (
    ~repairs["product_id"].isin(product_ids)
).sum()

print(
    f"Repairs with invalid product_id : "
    f"{invalid_repair_products:,}"
)

if invalid_repair_products == 0:
    print("PASS - All repair product IDs exist.")
else:
    print("FAIL - Invalid repair product IDs found.")


# ============================================================
# 7. REPAIR SKU VALIDATION
# ============================================================

invalid_repair_skus = (
    ~repairs["sku"].isin(product_skus)
).sum()

print(
    f"Repairs with invalid SKU : "
    f"{invalid_repair_skus:,}"
)

if invalid_repair_skus == 0:
    print("PASS - All repair SKUs exist.")
else:
    print("FAIL - Invalid repair SKUs found.")


# ============================================================
# 8. REPAIR COMPONENT VALIDATION
# ============================================================

bom_components = set(bom["component_id"])

invalid_repair_components = (
    ~repairs["component_id"]
    .isin(bom_components)
).sum()

print(
    f"Repairs with invalid component_id : "
    f"{invalid_repair_components:,}"
)

if invalid_repair_components == 0:
    print("PASS - All repair components exist in BOM.")
else:
    print("FAIL - Invalid repair components found.")


# ============================================================
# 9. SKU + COMPONENT RELATIONSHIP
# ============================================================

print("\nChecking SKU + component relationships...")

valid_bom_pairs = set(
    zip(
        bom["sku"],
        bom["component_id"]
    )
)

repair_pairs = zip(
    repairs["sku"],
    repairs["component_id"]
)

invalid_pairs = sum(
    pair not in valid_bom_pairs
    for pair in repair_pairs
)

print(
    f"Repairs with invalid SKU/component pair : "
    f"{invalid_pairs:,}"
)

if invalid_pairs == 0:
    print(
        "PASS - Every repair component belongs "
        "to the corresponding product BOM."
    )
else:
    print(
        "FAIL - Invalid SKU/component relationships found."
    )


# ============================================================
# 10. REPAIR ID VALIDATION
# ============================================================

duplicate_repair_ids = (
    repairs["repair_id"]
    .duplicated()
    .sum()
)

print(
    f"\nDuplicate repair IDs : "
    f"{duplicate_repair_ids:,}"
)

if duplicate_repair_ids == 0:
    print("PASS - Repair IDs are unique.")
else:
    print("FAIL - Duplicate repair IDs detected.")


# ============================================================
# 11. DUPLICATE REPAIR RECORDS
# ============================================================

duplicate_repairs = repairs.duplicated().sum()

print(
    f"Duplicate repair records : "
    f"{duplicate_repairs:,}"
)

if duplicate_repairs == 0:
    print("PASS - No duplicate repair records.")
else:
    print("FAIL - Duplicate repair records detected.")


# ============================================================
# 12. NULL VALIDATION
# ============================================================

print("\nChecking missing values...")

missing_values = repairs.isna().sum()

total_missing = missing_values.sum()

print(
    f"Total missing values : "
    f"{total_missing:,}"
)

if total_missing == 0:
    print("PASS - No missing values in repair dataset.")
else:
    print("FAIL - Missing values detected.")


# ============================================================
# 13. COST VALIDATION
# ============================================================

print("\nChecking costs...")

negative_repair_costs = (
    repairs["repair_cost"] < 0
).sum()

negative_replacement_costs = (
    repairs["replacement_cost"] < 0
).sum()

print(
    f"Negative repair costs       : "
    f"{negative_repair_costs:,}"
)

print(
    f"Negative replacement costs  : "
    f"{negative_replacement_costs:,}"
)


# ============================================================
# 14. DOWNTIME VALIDATION
# ============================================================

negative_downtime = (
    repairs["downtime_days"] < 0
).sum()

print(
    f"Negative downtime values : "
    f"{negative_downtime:,}"
)


# ============================================================
# 15. WARRANTY VALIDATION
# ============================================================

print("\nWarranty claim distribution:")

print(
    repairs["warranty_claim"]
    .value_counts()
)


# ============================================================
# 16. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("FINAL VALIDATION SUMMARY")
print("=" * 60)

checks = {

    "Product IDs unique":
        duplicate_product_ids == 0,

    "SKUs unique":
        duplicate_skus == 0,

    "BOM records unique":
        duplicate_bom_records == 0,

    "Exactly 6 components per SKU":
        invalid_component_counts == 0,

    "All BOM SKUs valid":
        len(orphan_bom_skus) == 0,

    "All repair product IDs valid":
        invalid_repair_products == 0,

    "All repair SKUs valid":
        invalid_repair_skus == 0,

    "All repair components valid":
        invalid_repair_components == 0,

    "All SKU/component pairs valid":
        invalid_pairs == 0,

    "Repair IDs unique":
        duplicate_repair_ids == 0,

    "Repair records unique":
        duplicate_repairs == 0,

    "No missing repair values":
        total_missing == 0,

    "No negative repair costs":
        negative_repair_costs == 0,

    "No negative replacement costs":
        negative_replacement_costs == 0,

    "No negative downtime":
        negative_downtime == 0
}


passed = 0

for check, result in checks.items():

    status = "PASS" if result else "FAIL"

    print(f"{status:5} | {check}")

    if result:
        passed += 1


print("\n" + "-" * 60)

print(
    f"Validation checks passed: "
    f"{passed}/{len(checks)}"
)

if passed == len(checks):

    print("\nALL VALIDATIONS PASSED.")
    print("EchoChain datasets are structurally consistent.")

else:

    print("\nSOME VALIDATIONS FAILED.")
    print("Review the failures above before continuing.")

print("=" * 60)
