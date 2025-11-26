import sqlite3
import os
import pandas as pd
from datetime import datetime


DB_FILE = "printforge.db"


# ------------------------------------------------
# Connection
# ------------------------------------------------
def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


# ------------------------------------------------
# Schema Setup
# ------------------------------------------------
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript(
        """
    CREATE TABLE IF NOT EXISTS spools (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand TEXT,
        spool_type TEXT,
        color TEXT,
        cost_per_kg REAL,
        cost_per_g REAL,
        current_weight_g REAL,
        weight_no_spool_g REAL
    );

    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        shipping_info TEXT,
        shipping_weight_g REAL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        variant_name TEXT NOT NULL,
        material TEXT,
        color TEXT,
        nozzle_size REAL,
        layer_height REAL,
        print_temp REAL,
        bed_temp REAL,
        infill REAL,
        notes TEXT,
        quantity_on_hand INTEGER DEFAULT 0,
        FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS parts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        unit TEXT,
        unit_cost REAL,
        quantity_on_hand REAL DEFAULT 0,
        notes TEXT
    );
    

CREATE TABLE IF NOT EXISTS product_bom (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    variant_id INTEGER,
    item_type TEXT NOT NULL,
    spool_id INTEGER,
    part_id INTEGER,
    grams REAL DEFAULT 0,
    quantity REAL DEFAULT 0,
    notes TEXT
);

    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        job_name TEXT,
        customer_name TEXT,
        customer_email TEXT,
        product_id INTEGER,
        variant_id INTEGER,
        quantity REAL DEFAULT 0,
        material_cost_per_unit REAL DEFAULT 0,
        labor_cost_total REAL DEFAULT 0,
        electricity_cost_total REAL DEFAULT 0,
        wear_and_tear_total REAL DEFAULT 0,
        extra_overhead_total REAL DEFAULT 0,
        overhead_total REAL DEFAULT 0,
        margin_percent REAL DEFAULT 0,
        price_per_unit REAL DEFAULT 0,
        total_price REAL DEFAULT 0,
        notes TEXT,
        internal_invoice TEXT,
        customer_invoice TEXT
    );
"""
    )

    conn.commit()
    conn.close()


# ------------------------------------------------
# BASIC GETTERS
# ------------------------------------------------
def get_all_spools():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM spools ORDER BY id").fetchall()
    conn.close()
    return [
        (r["id"], r["brand"], r["color"], r["cost_per_g"], r["current_weight_g"])
        for r in rows
    ]


def get_all_products():
    """
    Return a simple list of (id, name) for all products,
    used by UI pages that just need a dropdown or table.
    """
    conn = get_connection()
    rows = conn.execute("SELECT id, name FROM products ORDER BY name").fetchall()
    conn.close()
    return [(r["id"], r["name"]) for r in rows]

def get_all_products_full():
    """Return all products as sqlite3.Row list."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM products ORDER BY name").fetchall()
    conn.close()
    return rows


    rows = conn.execute("SELECT * FROM products ORDER BY name").fetchall()
    conn.close()
    # Placeholder: only id + name currently used in UI
    return [(r["id"], r["name"]) for r in rows]


def get_product_detail(product_id):
    conn = get_connection()
    product = conn.execute(
        "SELECT * FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    variants = conn.execute(
        "SELECT * FROM stock WHERE product_id = ? ORDER BY variant_name",
        (product_id,),
    ).fetchall()
    conn.close()
    return product, variants


# ------------------------------------------------
# PRODUCT CRUD
# ------------------------------------------------
def create_product(name, shipping_info="", shipping_weight_g=0):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO products(name, shipping_info, shipping_weight_g)
        VALUES (?, ?, ?)
    """,
        (name, shipping_info, shipping_weight_g),
    )

    conn.commit()
    conn.close()


def update_product(product_id, name, shipping_info, shipping_weight_g):
    conn = get_connection()
    conn.execute(
        """
        UPDATE products
        SET name = ?, shipping_info = ?, shipping_weight_g = ?
        WHERE id = ?
    """,
        (name, shipping_info, shipping_weight_g, product_id),
    )
    conn.commit()
    conn.close()


def delete_product(product_id):
    conn = get_connection()
    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()


# ------------------------------------------------
# VARIANT / STOCK CRUD
# ------------------------------------------------

def get_stock_for_product(product_id):
    """Return all variant/stock rows for a given product_id."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM stock WHERE product_id = ? ORDER BY variant_name",
        (product_id,),
    ).fetchall()
    conn.close()
    return rows


def create_variant(
    product_id,
    variant_name,
    material,
    color,
    nozzle_size,
    layer_height,
    print_temp,
    bed_temp,
    infill,
    notes,
    quantity_on_hand=0,
):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO stock(
            product_id,
            variant_name,
            material,
            color,
            nozzle_size,
            layer_height,
            print_temp,
            bed_temp,
            infill,
            notes,
            quantity_on_hand
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            product_id,
            variant_name,
            material,
            color,
            nozzle_size,
            layer_height,
            print_temp,
            bed_temp,
            infill,
            notes,
            quantity_on_hand,
        ),
    )

    conn.commit()
    conn.close()


def update_variant(
    variant_id,
    variant_name,
    material,
    color,
    nozzle_size,
    layer_height,
    print_temp,
    bed_temp,
    infill,
    notes,
    quantity_on_hand,
):
    conn = get_connection()
    conn.execute(
        """
        UPDATE stock
        SET
            variant_name = ?,
            material = ?,
            color = ?,
            nozzle_size = ?,
            layer_height = ?,
            print_temp = ?,
            bed_temp = ?,
            infill = ?,
            notes = ?,
            quantity_on_hand = ?
        WHERE id = ?
    """,
        (
            variant_name,
            material,
            color,
            nozzle_size,
            layer_height,
            print_temp,
            bed_temp,
            infill,
            notes,
            quantity_on_hand,
            variant_id,
        ),
    )
    conn.commit()
    conn.close()


def update_variant_quantity(variant_id, qty):
    conn = get_connection()
    conn.execute(
        """
        UPDATE stock
        SET quantity_on_hand = ?
        WHERE id = ?
    """,
        (qty, variant_id),
    )
    conn.commit()
    conn.close()


def delete_variant(variant_id):
    conn = get_connection()
    conn.execute("DELETE FROM stock WHERE id = ?", (variant_id,))
    conn.commit()
    conn.close()


# ------------------------------------------------
# EXCEL IMPORTERS (Spools)
# ------------------------------------------------
def import_spools_from_excel(
    path,
    sheet_name="Spools",
    spool_weights_sheet="Spool_Weights",
):
    """
    Import spools from an Excel file into the `spools` table.

    - Reads the main spools sheet (default: 'Spools')
    - Optionally reads the spool weights sheet (default: 'Spool_Weights')
      to populate `weight_no_spool_g` using brand + spool type.
    - Derives Cost per G from Total cost per KG.
    """

    # ------------------------------
    # Load spools sheet
    # ------------------------------
    df = pd.read_excel(path, sheet_name=sheet_name)
    df = df.dropna(how="all")  # drop completely empty rows
    df.columns = [str(c).strip().lower() for c in df.columns]

    required_cols = [
        "brand",
        "spool type",
        "color",
        "total cost per kg",
        "current weight",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in '{sheet_name}' sheet: {missing}")

    # ------------------------------
    # Optional: load spool weights sheet
    # ------------------------------
    spool_weight_map = {}

    try:
        df_w = pd.read_excel(path, sheet_name=spool_weights_sheet)
        df_w = df_w.dropna(how="all")
        df_w.columns = [str(c).strip().lower() for c in df_w.columns]

        weight_required = ["brand", "spool mat.", "weight"]
        missing_w = [c for c in weight_required if c not in df_w.columns]

        if not missing_w:
            for _, row in df_w.iterrows():
                brand = str(row["brand"]).strip()
                mat = str(row["spool mat."]).strip()

                if not brand or not mat:
                    continue

                try:
                    weight = float(row["weight"])
                except (TypeError, ValueError):
                    continue

                key = (brand.lower(), mat.lower())
                spool_weight_map[key] = weight
        else:
            print(
                f"Spool weight sheet '{spool_weights_sheet}' missing columns: {missing_w}. "
                "Empty spool weights will default to 0."
            )
    except Exception as e:
        print(
            f"Could not load spool weights from sheet '{spool_weights_sheet}': {e}. "
            "Empty spool weights will default to 0."
        )
        spool_weight_map = {}

    # ------------------------------
    # Insert into database
    # ------------------------------
    conn = get_connection()
    cur = conn.cursor()

    # Clear existing spools
    cur.execute("DELETE FROM spools")

    for _, row in df.iterrows():
        try:
            brand = str(row["brand"]).strip()
            spool_type = str(row["spool type"]).strip()
            color = str(row["color"]).strip()

            raw_cost_per_kg = row["total cost per kg"]
            raw_current_weight = row["current weight"]

            try:
                cost_per_kg = (
                    float(raw_cost_per_kg) if pd.notna(raw_cost_per_kg) else 0.0
                )
            except (TypeError, ValueError):
                cost_per_kg = 0.0

            try:
                current_weight_g = (
                    float(raw_current_weight) if pd.notna(raw_current_weight) else 0.0
                )
            except (TypeError, ValueError):
                current_weight_g = 0.0

            cost_per_g = cost_per_kg / 1000.0 if cost_per_kg else 0.0

            key = (brand.lower(), spool_type.lower())
            weight_no_spool_g = float(spool_weight_map.get(key, 0.0))

            cur.execute(
                """
                INSERT INTO spools(
                    brand, spool_type, color,
                    cost_per_kg, cost_per_g,
                    current_weight_g, weight_no_spool_g
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    brand,
                    spool_type,
                    color,
                    cost_per_kg,
                    cost_per_g,
                    current_weight_g,
                    weight_no_spool_g,
                ),
            )
        except Exception as e:
            print(
                f"Skipping spool row (brand={row.get('brand', '')}, "
                f"color={row.get('color', '')}): {e}"
            )

    conn.commit()
    conn.close()


# ------------------------------------------------
# SPOOLS CRUD HELPERS FOR UI
# ------------------------------------------------
def get_spool_by_id(spool_id):
    """Return a single spool row (sqlite Row) or None."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM spools WHERE id = ?", (spool_id,)).fetchone()
    conn.close()
    return row


def create_spool(
    brand, spool_type, color, cost_per_kg, current_weight_g, weight_no_spool_g
):
    """Create a new spool and return its ID."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        cpk = float(cost_per_kg) if cost_per_kg is not None else 0.0
    except (TypeError, ValueError):
        cpk = 0.0

    try:
        current_weight = (
            float(current_weight_g) if current_weight_g is not None else 0.0
        )
    except (TypeError, ValueError):
        current_weight = 0.0

    try:
        empty_weight = (
            float(weight_no_spool_g) if weight_no_spool_g is not None else 0.0
        )
    except (TypeError, ValueError):
        empty_weight = 0.0

    cost_per_g = cpk / 1000.0 if cpk else 0.0

    cur.execute(
        """
        INSERT INTO spools (
            brand, spool_type, color,
            cost_per_kg, cost_per_g,
            current_weight_g, weight_no_spool_g
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (brand, spool_type, color, cpk, cost_per_g, current_weight, empty_weight),
    )

    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def update_spool(
    spool_id,
    brand,
    spool_type,
    color,
    cost_per_kg,
    current_weight_g,
    weight_no_spool_g,
):
    """Update an existing spool."""
    conn = get_connection()

    try:
        cpk = float(cost_per_kg) if cost_per_kg is not None else 0.0
    except (TypeError, ValueError):
        cpk = 0.0

    try:
        current_weight = (
            float(current_weight_g) if current_weight_g is not None else 0.0
        )
    except (TypeError, ValueError):
        current_weight = 0.0

    try:
        empty_weight = (
            float(weight_no_spool_g) if weight_no_spool_g is not None else 0.0
        )
    except (TypeError, ValueError):
        empty_weight = 0.0

    cost_per_g = cpk / 1000.0 if cpk else 0.0

    conn.execute(
        """
        UPDATE spools
        SET brand = ?, spool_type = ?, color = ?,
            cost_per_kg = ?, cost_per_g = ?,
            current_weight_g = ?, weight_no_spool_g = ?
        WHERE id = ?
    """,
        (brand, spool_type, color, cpk, cost_per_g, current_weight, empty_weight, spool_id),
    )
    conn.commit()
    conn.close()


def delete_spool(spool_id):
    """Delete a spool by ID."""
    conn = get_connection()
    conn.execute("DELETE FROM spools WHERE id = ?", (spool_id,))
    conn.commit()
    conn.close()


# ------------------------------------------------
# PARTS CRUD HELPERS
# ------------------------------------------------
def get_all_parts():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM parts ORDER BY name").fetchall()
    conn.close()
    return rows


def get_part_by_id(part_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM parts WHERE id = ?", (part_id,)).fetchone()
    conn.close()
    return row


def create_part(name, category, unit, unit_cost, quantity_on_hand, notes):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cost = float(unit_cost) if unit_cost is not None else 0.0
    except (TypeError, ValueError):
        cost = 0.0

    try:
        qty = float(quantity_on_hand) if quantity_on_hand is not None else 0.0
    except (TypeError, ValueError):
        qty = 0.0

    cur.execute(
        """
        INSERT INTO parts (name, category, unit, unit_cost, quantity_on_hand, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (name, category, unit, cost, qty, notes),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def update_part(part_id, name, category, unit, unit_cost, quantity_on_hand, notes):
    conn = get_connection()

    try:
        cost = float(unit_cost) if unit_cost is not None else 0.0
    except (TypeError, ValueError):
        cost = 0.0

    try:
        qty = float(quantity_on_hand) if quantity_on_hand is not None else 0.0
    except (TypeError, ValueError):
        qty = 0.0

    conn.execute(
        """
        UPDATE parts
        SET name = ?, category = ?, unit = ?, unit_cost = ?, quantity_on_hand = ?, notes = ?
        WHERE id = ?
    """,
        (name, category, unit, cost, qty, notes, part_id),
    )
    conn.commit()
    conn.close()


def delete_part(part_id):
    conn = get_connection()
    conn.execute("DELETE FROM parts WHERE id = ?", (part_id,))
    conn.commit()
    conn.close()


# ------------------------------------------------
# DATABASE RESET UTIL
# ------------------------------------------------
def force_unlock():
    """Used for Windows to delete pending lock files."""
    try:
        if os.path.exists(DB_FILE + "-journal"):
            os.remove(DB_FILE + "-journal")
    except Exception:
        pass


# ------------------------------------------------
# BOM HELPERS
# ------------------------------------------------
def add_bom_item(
    product_id,
    item_type,
    grams=0.0,
    quantity=0.0,
    variant_id=None,
    spool_id=None,
    part_id=None,
    notes=None,
):
    """Insert a single BOM row for either filament or part."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO product_bom (
            product_id,
            variant_id,
            item_type,
            spool_id,
            part_id,
            grams,
            quantity,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
    , (product_id, variant_id, item_type, spool_id, part_id, grams, quantity, notes))
    conn.commit()
    conn.close()


def update_bom_item(
    bom_id,
    item_type,
    spool_id=None,
    part_id=None,
    grams=0.0,
    quantity=0.0,
    notes=None,
):
    """Update a BOM row by ID."""
    conn = get_connection()
    conn.execute(
        """
        UPDATE product_bom
        SET item_type = ?,
            spool_id = ?,
            part_id = ?,
            grams = ?,
            quantity = ?,
            notes = ?
        WHERE id = ?
        """
    , (item_type, spool_id, part_id, grams, quantity, notes, bom_id))
    conn.commit()
    conn.close()


def delete_bom_item(bom_id):
    """Delete a BOM row by ID."""
    conn = get_connection()
    conn.execute("DELETE FROM product_bom WHERE id = ?", (bom_id,))
    conn.commit()
    conn.close()


def get_bom_rows(product_id, variant_id=None):
    """Return BOM rows for a product/variant without inheritance."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if variant_id is None:
        cur.execute(
            "SELECT * FROM product_bom WHERE product_id = ? AND variant_id IS NULL ORDER BY id",
            (product_id,),
        )
    else:
        cur.execute(
            "SELECT * FROM product_bom WHERE product_id = ? AND variant_id = ? ORDER BY id",
            (product_id, variant_id),
        )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_effective_bom_for_product(product_id, variant_id=None):
    """Return BOM rows applying variant override logic.

    If a variant_id is provided and has BOM rows, those are returned.
    Otherwise, the product-level (variant_id IS NULL) BOM is returned.
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = []
    if variant_id is not None:
        cur.execute(
            "SELECT * FROM product_bom WHERE product_id = ? AND variant_id = ? ORDER BY id",
            (product_id, variant_id),
        )
        rows = cur.fetchall()

    if not rows:
        cur.execute(
            "SELECT * FROM product_bom WHERE product_id = ? AND variant_id IS NULL ORDER BY id",
            (product_id,),
        )
        rows = cur.fetchall()

    conn.close()
    return rows






# ------------------------------------------------
# BOM material cost + Excel BOM import
# ------------------------------------------------

def calculate_material_cost_per_unit(product_id, variant_id=None):
    """
    Calculate the total material cost per unit for a product/variant
    based on its effective BOM.

    Uses:
      - get_effective_bom_for_product(product_id, variant_id)
      - spools.cost_per_g for filament rows
      - parts.unit_cost for part rows

    Returns:
        (total_cost_per_unit, breakdown)

        - total_cost_per_unit: float (dollars)
        - breakdown: list of dicts:
            {
                "type": "filament" | "part",
                "label": str,
                "grams": float,
                "quantity": float,
                "line_cost": float,
            }
    """
    bom_rows = get_effective_bom_for_product(product_id, variant_id)
    if not bom_rows:
        return 0.0, []

    total = 0.0
    breakdown = []

    for row in bom_rows:
        item_type = row["item_type"]
        grams = float(row["grams"] or 0.0)
        qty = float(row["quantity"] or 0.0)

        line_cost = 0.0
        label = ""

        if item_type == "filament":
            spool_id = row["spool_id"]
            if not spool_id or grams <= 0:
                continue

            spool = get_spool_by_id(spool_id)
            if spool is None:
                continue

            cost_per_g = float(spool["cost_per_g"] or 0.0)
            label = f"{spool['brand'] or 'Spool'} {spool['color'] or ''}".strip()
            line_cost = cost_per_g * grams

        elif item_type == "part":
            part_id = row["part_id"]
            if not part_id or qty <= 0:
                continue

            part = get_part_by_id(part_id)
            if part is None:
                continue

            unit_cost = float(part["unit_cost"] or 0.0)
            label = part["name"] or "Part"
            line_cost = unit_cost * qty

        else:
            # Unknown item_type – ignore
            continue

        total += line_cost
        breakdown.append(
            {
                "type": item_type,
                "label": label,
                "grams": grams,
                "quantity": qty,
                "line_cost": line_cost,
            }
        )

    return total, breakdown


def import_bom_from_excel(excel_path):
    """
    Import BOM rows from per-product sheets in the Excel workbook.

    Expected pattern in the workbook:
      - Standard sheets:
          'Spools', 'Stock', 'Other Parts', 'Spool_Weights',
          'Dashboard', 'Sheet1', '_Product Template'
      - Additional sheets with a 'Parts' column are treated as
        product BOM sheets, named after the product, e.g.
          'Mushroom Light', 'Dumpster Fire', etc.

    Each BOM sheet should have columns (case-insensitive):
      - Parts   : name of the printed part or other part
      - Quanity : quantity per unit (may be blank -> treated as 1)
      - Weight  : filament weight in grams (for filament lines)
      - Color   : text containing brand/color for filament lines

    Heuristics:
      - If Color is non-empty and Weight > 0, treat as a filament row
        and attempt to map Color to a spool (brand + color).
      - Otherwise treat as a non-printed part row and attempt to map
        Parts to an entry in the 'parts' table.

    All imported BOM rows are stored at the product level
    (variant_id is left as NULL). Variant-specific overrides can still
    be edited later via the UI if needed.

    Returns:
        int: number of BOM rows inserted.
    """
    if not os.path.exists(excel_path):
        raise FileNotFoundError("Excel file not found: %s" % excel_path)

    # Helper for fuzzy matching
    def _norm(s):
        return "".join(ch.lower() for ch in str(s) if ch.isalnum())

    # Sheets that are *not* BOM definitions
    skip_sheets = {
        "spools",
        "stock",
        "other parts",
        "spool_weights",
        "dashboard",
        "sheet1",
        "_product template",
    }

    # Preload products, spools, and parts from the DB for matching
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    products = cur.execute("SELECT id, name FROM products").fetchall()
    spools = cur.execute("SELECT id, brand, color FROM spools").fetchall()
    parts = cur.execute("SELECT id, name FROM parts").fetchall()
    conn.close()

    def _find_product_id_for_sheet(sheet_name):
        key = _norm(sheet_name)
        if not key:
            return None

        best_id = None
        best_score = 0

        for row in products:
            pname = row["name"] or ""
            pkey = _norm(pname)
            if not pkey:
                continue

            score = 0
            if key == pkey:
                score = 3
            elif key in pkey or pkey in key:
                score = 2

            if score > best_score:
                best_score = score
                best_id = row["id"]

        return best_id

    def _find_spool_id(color_text):
        text = _norm(color_text)
        if not text:
            return None

        # Pass 1: brand + color both appear
        for s in spools:
            brand = _norm(s["brand"] or "")
            scolor = _norm(s["color"] or "")
            if brand and brand in text and scolor and (scolor in text or text in scolor):
                return s["id"]

        # Pass 2: color alone
        for s in spools:
            scolor = _norm(s["color"] or "")
            if scolor and (scolor in text or text in scolor):
                return s["id"]

        return None

    def _find_part_id(part_name):
        if not part_name:
            return None
        key = _norm(part_name)
        if not key:
            return None

        # Simple synonym map for slightly different naming
        synonyms = {
            "candle": "tealight",  # Excel uses "Candle", parts sheet uses "Tea Light"
        }
        key = synonyms.get(key, key)

        # Exact match
        for p in parts:
            if _norm(p["name"]) == key:
                return p["id"]

        # Fuzzy contains match
        for p in parts:
            pname_norm = _norm(p["name"])
            if key in pname_norm or pname_norm in key:
                return p["id"]

        return None

    total_inserted = 0

    xls = pd.ExcelFile(excel_path)
    for sheet_name in xls.sheet_names:
        if _norm(sheet_name) in skip_sheets:
            continue

        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        if df.empty:
            continue

        # Standardise columns
        df.columns = [str(c).strip().lower() for c in df.columns]
        if "parts" not in df.columns:
            # Not a BOM-style sheet
            continue

        product_id = _find_product_id_for_sheet(sheet_name)
        if product_id is None:
            # No matching product found – skip this sheet
            continue

        for _, row in df.iterrows():
            part_label = str(row.get("parts") or "").strip()
            if not part_label:
                continue

            # Skip template/instruction rows
            lower_label = part_label.lower()
            if lower_label.startswith("→ duplicate") or lower_label.startswith("- "):
                continue

            qty_val = row.get("quanity")
            if qty_val is None:
                qty_val = row.get("quantity")
            weight_val = row.get("weight")
            color_val = row.get("color")

            try:
                qty = float(qty_val) if qty_val is not None and not pd.isna(qty_val) else 0.0
            except (TypeError, ValueError):
                qty = 0.0

            try:
                grams = float(weight_val) if weight_val is not None and not pd.isna(weight_val) else 0.0
            except (TypeError, ValueError):
                grams = 0.0

            color_text = str(color_val or "").strip()

            # Decide if this is a filament row or a non-printed part row
            if color_text and grams > 0:
                spool_id = _find_spool_id(color_text)
                if spool_id is None:
                    # Can't map to a known spool – skip for now
                    continue

                add_bom_item(
                    product_id=product_id,
                    item_type="filament",
                    grams=grams,
                    quantity=qty if qty > 0 else 1.0,
                    variant_id=None,
                    spool_id=spool_id,
                    part_id=None,
                    notes=None,
                )
                total_inserted += 1
            else:
                part_id = _find_part_id(part_label)
                if part_id is None:
                    # Unknown part, skip silently
                    continue

                add_bom_item(
                    product_id=product_id,
                    item_type="part",
                    grams=grams,
                    quantity=qty if qty > 0 else 1.0,
                    variant_id=None,
                    spool_id=None,
                    part_id=part_id,
                    notes=None,
                )
                total_inserted += 1

    return total_inserted

# ------------------------------------------------
# EXCEL IMPORT – PARTS & PRODUCTS
# ------------------------------------------------
def import_parts_from_excel(excel_path, sheet_name="Other Parts"):
    """Import non-printed parts from the 'Other Parts' sheet into the parts table."""
    if not os.path.exists(excel_path):
        raise FileNotFoundError("Excel file not found: %s" % excel_path)

    df = pd.read_excel(excel_path, sheet_name=sheet_name)
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Expect at minimum: part, cost, quanity
    if "part" not in df.columns or "cost" not in df.columns or "quanity" not in df.columns:
        # fall back silently if sheet isn't present / structured
        return

    conn = get_connection()
    cur = conn.cursor()

    for _, row in df.iterrows():
        name = str(row.get("part", "")).strip()
        if not name:
            continue

        try:
            total_cost = float(row.get("cost", 0) or 0)
        except (TypeError, ValueError):
            total_cost = 0.0

        try:
            qty = float(row.get("quanity", 0) or 0)
        except (TypeError, ValueError):
            qty = 0.0

        unit_cost = total_cost / qty if qty else 0.0

        notes_parts = []
        if "weight" in df.columns and not pd.isna(row.get("weight")):
            notes_parts.append("Weight: %s" % row.get("weight"))
        if "used" in df.columns and not pd.isna(row.get("used")):
            notes_parts.append("Used: %s" % row.get("used"))
        if "used.1" in df.columns and not pd.isna(row.get("used.1")):
            notes_parts.append("Used.1: %s" % row.get("used.1"))
        notes = "; ".join(notes_parts)

        cur.execute(
            """
            INSERT INTO parts (name, category, unit, unit_cost, quantity_on_hand, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, None, "pcs", unit_cost, qty, notes),
        )

    conn.commit()
    conn.close()


def import_products_and_variants_from_excel(excel_path, sheet_name="Stock"):
    """Import products and their stock variants from the 'Stock' sheet."""
    if not os.path.exists(excel_path):
        raise FileNotFoundError("Excel file not found: %s" % excel_path)

    df = pd.read_excel(excel_path, sheet_name=sheet_name)
    df.columns = [str(c).strip().lower() for c in df.columns]

    required_cols = ["product", "number onhand"]
    for col in required_cols:
        if col not in df.columns:
            # sheet not in expected shape
            return

    conn = get_connection()
    cur = conn.cursor()

    # group by product + color combos
    df["product"] = df["product"].astype(str).str.strip()
    if "color" in df.columns:
        df["color"] = df["color"].astype(str).str.strip()
    else:
        df["color"] = ""

    # create products first
    seen_products = {}
    for product_name, group in df.groupby("product"):
        if not product_name:
            continue

        # shipping info / weight from first non-empty row
        shipping_info = ""
        shipping_weight_g = 0.0

        if "shipping info" in group.columns:
            for val in group["shipping info"]:
                if isinstance(val, str) and val.strip():
                    shipping_info = val.strip()
                    break

        if "weight" in group.columns:
            for val in group["weight"]:
                if isinstance(val, str) and val.strip():
                    txt = val.strip().lower()
                    num_str = "".join(ch for ch in txt if (ch.isdigit() or ch == "." or ch == "-"))
                    try:
                        num = float(num_str)
                    except (TypeError, ValueError):
                        num = 0.0
                    if "oz" in txt:
                        shipping_weight_g = num * 28.3495
                    else:
                        shipping_weight_g = num
                    break

        cur.execute(
            "INSERT INTO products (name, shipping_info, shipping_weight_g) VALUES (?, ?, ?)",
            (product_name, shipping_info, shipping_weight_g),
        )
        product_id = cur.lastrowid
        seen_products[product_name] = product_id

        # now variants / stock rows for this product
        for _, row in group.iterrows():
            try:
                qty = int(row.get("number onhand", 0) or 0)
            except (TypeError, ValueError):
                qty = 0

            color = str(row.get("color", "") or "").strip()

            variant_name = color or "Default"

            cur.execute(
                """
                INSERT INTO stock (
                    product_id,
                    variant_name,
                    material,
                    color,
                    nozzle_size,
                    layer_height,
                    print_temp,
                    bed_temp,
                    infill,
                    notes,
                    quantity_on_hand
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    product_id,
                    variant_name,
                    None,
                    color,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    None,
                    qty,
                ),
            )

    conn.commit()
    conn.close()

# ------------------------------------------------
# Invoices / Jobs
# ------------------------------------------------

def create_invoice(
    job_name,
    customer_name,
    customer_email,
    product_id,
    variant_id,
    quantity,
    material_cost_per_unit,
    labor_cost_total,
    electricity_cost_total,
    wear_and_tear_total,
    extra_overhead_total,
    overhead_total,
    margin_percent,
    price_per_unit,
    total_price,
    notes,
    internal_invoice,
    customer_invoice,
    created_at=None,
):
    """
    Insert a saved job / invoice row and return its new id.

    All cost/quantity fields are coerced to float; None/invalid -> 0.0.
    created_at defaults to current local time ISO string.
    """

    def _f(value):
        try:
            return float(value) if value is not None else 0.0
        except (TypeError, ValueError):
            return 0.0

    qty = _f(quantity)
    mcpu = _f(material_cost_per_unit)
    labor = _f(labor_cost_total)
    electric = _f(electricity_cost_total)
    wear = _f(wear_and_tear_total)
    extra = _f(extra_overhead_total)
    overhead = _f(overhead_total)
    margin = _f(margin_percent)
    ppu = _f(price_per_unit)
    total = _f(total_price)

    if created_at is None:
        created_at = datetime.now().isoformat(timespec="seconds")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO invoices (
            created_at,
            job_name,
            customer_name,
            customer_email,
            product_id,
            variant_id,
            quantity,
            material_cost_per_unit,
            labor_cost_total,
            electricity_cost_total,
            wear_and_tear_total,
            extra_overhead_total,
            overhead_total,
            margin_percent,
            price_per_unit,
            total_price,
            notes,
            internal_invoice,
            customer_invoice
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            created_at,
            job_name,
            customer_name,
            customer_email,
            product_id,
            variant_id,
            qty,
            mcpu,
            labor,
            electric,
            wear,
            extra,
            overhead,
            margin,
            ppu,
            total,
            notes,
            internal_invoice,
            customer_invoice,
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def get_all_invoices():
    """
    Return all invoices/jobs, newest first.

    Each row is a sqlite3.Row with extra:
      - product_name
      - variant_color
    for easy display in the UI.
    """
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT i.*,
               p.name AS product_name,
               s.color AS variant_color
        FROM invoices AS i
        LEFT JOIN products AS p ON i.product_id = p.id
        LEFT JOIN stock AS s ON i.variant_id = s.id
        ORDER BY i.created_at DESC, i.id DESC
        """
    ).fetchall()
    conn.close()
    return rows


def get_invoice(invoice_id):
    """
    Fetch a single invoice/job by id (with product/variant names).
    """
    conn = get_connection()
    row = conn.execute(
        """
        SELECT i.*,
               p.name AS product_name,
               s.color AS variant_color
        FROM invoices AS i
        LEFT JOIN products AS p ON i.product_id = p.id
        LEFT JOIN stock AS s ON i.variant_id = s.id
        WHERE i.id = ?
        """,
        (invoice_id,),
    ).fetchone()
    conn.close()
    return row


def delete_invoice(invoice_id):
    """
    Permanently delete a saved invoice/job.
    """
    conn = get_connection()
    conn.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
    conn.commit()
    conn.close()

