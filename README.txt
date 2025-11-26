
PrintForge Desktop – Unified DB/BOM/Import Update Pack

This pack contains drop-in replacements for:
  • db.py
  • reset_db.py

What's included:
  • Full database schema for:
      - spools
      - products
      - stock (variants)
      - parts
      - product_bom (for filament + non-printed parts)
  • BOM helper functions:
      - add_bom_item(...)
      - update_bom_item(...)
      - delete_bom_item(...)
      - get_bom_rows(...)
      - get_effective_bom_for_product(product_id, variant_id=None)
  • Extra product helpers:
      - get_all_products_full()
      - get_stock_for_product(product_id)
  • Excel import helpers:
      - import_spools_from_excel(...)
      - import_parts_from_excel(...)
      - import_products_and_variants_from_excel(...)
  • reset_db.py now:
      - Deletes printforge.db
      - Calls init_db() to create all tables (including product_bom)
      - Imports spools from 'Spools'
      - Imports parts from 'Other Parts'
      - Imports products & variants from 'Stock'

How to use:
  1. BACK UP your current db.py and reset_db.py (e.g. copy them to db_backup.py, reset_db_backup.py).
  2. Extract these db.py and reset_db.py into your project folder, overwriting the originals.
  3. Make sure Printforge_SHEETS_Level4_Clean_A3.xlsx is in the same folder.
  4. Run:
       python reset_db.py
  5. Then run:
       python main.py

The UI code you already have (including the Print Jobs page) should now find:
  - db.get_effective_bom_for_product(...)
  - the product_bom table in the database
  - spools, parts, products, and variants imported from Excel.
