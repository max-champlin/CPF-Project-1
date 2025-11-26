
import os
import sys

from db import (
    init_db,
    force_unlock,
    import_spools_from_excel,
    import_parts_from_excel,
    import_products_and_variants_from_excel,
    import_bom_from_excel,
)


# Default dataset shipped with the app
EXCEL_FILE = "Printforge_SHEETS_Level4_Clean_A3.xlsx"

SPOOLS_SHEET = "Spools"
PARTS_SHEET = "Other Parts"
STOCK_SHEET = "Stock"


def main():
    print("\n=== PrintForge Desktop – Database Reset ===\n")

    # ensure any -journal lock files are cleared
    force_unlock()

    db_file = "printforge.db"
    if os.path.exists(db_file):
        print(f"Removing existing database file: {db_file}")
        try:
            os.remove(db_file)
        except Exception as e:
            print(f"Could not remove {db_file}: {e}")
            sys.exit(1)

    print("Creating fresh database schema...")
    init_db()

    print()
    if not os.path.exists(EXCEL_FILE):
        print(f"⚠ Excel dataset not found: {EXCEL_FILE}")
        print("   Place the Excel file next to reset_db.py and run again.")
        sys.exit(1)

    print(f"Using Excel dataset: {EXCEL_FILE}\n")

    # Spools
    try:
        print("Importing spools from sheet 'Spools'...")
        import_spools_from_excel(EXCEL_FILE, sheet_name=SPOOLS_SHEET)
        print("Imported spools from Excel.\n")
    except Exception as e:
        print(f"⚠ Error importing spools: {e}\n")

    # Parts
    try:
        print("Importing parts from sheet 'Other Parts'...")
        import_parts_from_excel(EXCEL_FILE, sheet_name=PARTS_SHEET)
        print("Imported parts from Excel.\n")
    except Exception as e:
        print(f"⚠ Error importing parts: {e}\n")

    # Products + variants
    try:
        print("Importing products & variants from sheet 'Stock'...")
        import_products_and_variants_from_excel(EXCEL_FILE, sheet_name=STOCK_SHEET)
        print("Imported products and variants from Excel.\n")
    except Exception as e:
        print(f"⚠ Error importing products/variants: {e}\n")


    # BOM (per-product sheets)
    try:
        print("Importing BOM rows from product sheets...")
        inserted = import_bom_from_excel(EXCEL_FILE)
        print(f"Imported {inserted} BOM rows from Excel.\n")
    except Exception as e:
        print(f"⚠ Error importing BOM rows: {e}\n")

    print("Database reset and fully rebuilt from Excel!\n")


if __name__ == "__main__":
    main()
