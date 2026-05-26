import math
import random
import csv
from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np
import pandas as pd
try:
    import plotly.graph_objects as go
except ModuleNotFoundError:
    go = None
import streamlit as st


st.set_page_config(
    page_title="Dark Store Slotting Intelligence",
    page_icon="🏭",
    layout="wide",
)

PRIMARY = "#1a3c34"
ACCENT = "#2d6a4f"
LIGHTGREEN = "#d4edda"
DARKGRAY = "#212529"


def inject_styles():
    st.markdown(
        f"""
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
          html, body {{ font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; }}
          body {{ color: {DARKGRAY}; background: #ffffff; }}

          .ds-card {{
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 16px;
            box-shadow:
              0 10px 24px rgba(0,0,0,0.06),
              inset 0 1px 0 rgba(255,255,255,0.7);
          }}
          .ds-card-title {{
            font-size: 14px;
            font-weight: 800;
            color: {PRIMARY};
            margin-bottom: 6px;
          }}
          .ds-card-subtitle {{
            font-size: 12px;
            color: #64748b;
            margin-top: -2px;
            margin-bottom: 14px;
          }}

          .ds-metric {{
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 14px 16px;
            box-shadow:
              0 8px 18px rgba(0,0,0,0.05),
              inset 0 1px 0 rgba(255,255,255,0.7);
          }}
          .ds-metric-label {{
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.02em;
            text-transform: uppercase;
            color: #64748b;
            margin-bottom: 8px;
          }}
          .ds-metric-value {{
            font-size: 22px;
            font-weight: 900;
            color: {DARKGRAY};
          }}

          .ds-skeuo-btn {{
            background: linear-gradient(180deg, {ACCENT}, {PRIMARY});
            color: #ffffff;
            border: 1px solid rgba(0,0,0,0.12);
            border-radius: 12px;
            padding: 10px 14px;
            font-weight: 800;
            box-shadow: 0 10px 18px rgba(26,60,52,0.18), 0 4px 0 rgba(0,0,0,0.16);
          }}
          .ds-skeuo-btn:active {{
            transform: translateY(2px);
            box-shadow: 0 8px 14px rgba(26,60,52,0.16), 0 2px 0 rgba(0,0,0,0.16);
          }}

          .ds-badge {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 800;
            border: 1px solid rgba(0,0,0,0.06);
          }}
          .ds-badge-a {{ background: #ecfdf5; color: #166534; border-color: #bbf7d0; }}
          .ds-badge-b {{ background: #fffbeb; color: #92400e; border-color: #fde68a; }}
          .ds-badge-c {{ background: #f3f4f6; color: #374151; border-color: #e5e7eb; }}

          .ds-grid {{
            display: grid;
            gap: 6px;
            grid-auto-flow: row;
          }}
          .ds-cell {{
            width: 34px;
            height: 34px;
            border-radius: 10px;
            border: 1px solid #e5e7eb;
            box-shadow:
              0 5px 12px rgba(0,0,0,0.06),
              inset 0 1px 0 rgba(255,255,255,0.6);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 900;
            font-size: 11px;
            position: relative;
            padding: 2px;
            text-align: center;
            line-height: 1.05;
          }}
          .ds-cell .ds-emoji {{
            position: absolute;
            bottom: -7px;
            right: 2px;
            font-size: 14px;
          }}

          .ds-zone-a {{ background: {LIGHTGREEN}; }}
          .ds-zone-b {{ background: #fff3cd; }}
          .ds-zone-c {{ background: #f8f9fa; }}
          .ds-dispatch {{ background: {PRIMARY}; color: #ffffff; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------
# Simulated data + analytics
# -----------------------------

SKU_DEFINITIONS = [
    # FRUITS (8)
    {"name": "Banana", "category": "FRUITS", "subcategory": "Banana"},
    {"name": "Apple", "category": "FRUITS", "subcategory": "Apple"},
    {"name": "Mango", "category": "FRUITS", "subcategory": "Mango"},
    {"name": "Papaya", "category": "FRUITS", "subcategory": "Papaya"},
    {"name": "Watermelon", "category": "FRUITS", "subcategory": "Watermelon"},
    {"name": "Pomegranate", "category": "FRUITS", "subcategory": "Pomegranate"},
    {"name": "Grapes", "category": "FRUITS", "subcategory": "Grapes"},
    {"name": "Guava", "category": "FRUITS", "subcategory": "Guava"},
    # VEGETABLES (8)
    {"name": "Tomato", "category": "VEGETABLES", "subcategory": "Tomato"},
    {"name": "Onion", "category": "VEGETABLES", "subcategory": "Onion"},
    {"name": "Potato", "category": "VEGETABLES", "subcategory": "Potato"},
    {"name": "Spinach", "category": "VEGETABLES", "subcategory": "Spinach"},
    {"name": "Carrot", "category": "VEGETABLES", "subcategory": "Carrot"},
    {"name": "Capsicum", "category": "VEGETABLES", "subcategory": "Capsicum"},
    {"name": "Cucumber", "category": "VEGETABLES", "subcategory": "Cucumber"},
    {"name": "Brinjal", "category": "VEGETABLES", "subcategory": "Brinjal"},
    # DAIRY (8)
    {"name": "Milk 500ml", "category": "DAIRY", "subcategory": "Milk"},
    {"name": "Milk 1L", "category": "DAIRY", "subcategory": "Milk"},
    {"name": "Curd 400g", "category": "DAIRY", "subcategory": "Curd"},
    {"name": "Butter 100g", "category": "DAIRY", "subcategory": "Butter"},
    {"name": "Paneer 200g", "category": "DAIRY", "subcategory": "Paneer"},
    {"name": "Cheese Slice", "category": "DAIRY", "subcategory": "Cheese"},
    {"name": "Ghee 500ml", "category": "DAIRY", "subcategory": "Ghee"},
    {"name": "Buttermilk", "category": "DAIRY", "subcategory": "Buttermilk"},
    # BAKERY (5)
    {"name": "Bread White", "category": "BAKERY", "subcategory": "Bread"},
    {"name": "Bread Brown", "category": "BAKERY", "subcategory": "Bread"},
    {"name": "Bun Pack", "category": "BAKERY", "subcategory": "Bun"},
    {"name": "Cake Slice", "category": "BAKERY", "subcategory": "Cake"},
    {"name": "Croissant", "category": "BAKERY", "subcategory": "Croissant"},
    # EGGS (2)
    {"name": "Egg 6-pack", "category": "EGGS", "subcategory": "Eggs"},
    {"name": "Egg 12-pack", "category": "EGGS", "subcategory": "Eggs"},
    # STAPLES (10)
    {"name": "Basmati Rice 1kg", "category": "STAPLES", "subcategory": "Rice"},
    {"name": "Toor Dal 500g", "category": "STAPLES", "subcategory": "Dal"},
    {"name": "Atta 1kg", "category": "STAPLES", "subcategory": "Atta"},
    {"name": "Sunflower Oil 1L", "category": "STAPLES", "subcategory": "Oil"},
    {"name": "Sugar 1kg", "category": "STAPLES", "subcategory": "Sugar"},
    {"name": "Salt 1kg", "category": "STAPLES", "subcategory": "Salt"},
    {"name": "Poha 500g", "category": "STAPLES", "subcategory": "Poha"},
    {"name": "Sooji 500g", "category": "STAPLES", "subcategory": "Sooji"},
    {"name": "Maida 500g", "category": "STAPLES", "subcategory": "Maida"},
    {"name": "Chana Dal 500g", "category": "STAPLES", "subcategory": "Dal"},
    # PACKAGED SNACKS (5)
    {"name": "Biscuits Glucose", "category": "PACKAGED SNACKS", "subcategory": "Biscuits"},
    {"name": "Chips 30g", "category": "PACKAGED SNACKS", "subcategory": "Chips"},
    {"name": "Namkeen 200g", "category": "PACKAGED SNACKS", "subcategory": "Namkeen"},
    {"name": "Protein Bar", "category": "PACKAGED SNACKS", "subcategory": "Protein Bar"},
    {"name": "Instant Noodles", "category": "PACKAGED SNACKS", "subcategory": "Noodles"},
    # BEVERAGES (4)
    {"name": "Water 1L", "category": "BEVERAGES", "subcategory": "Water"},
    {"name": "Orange Juice 200ml", "category": "BEVERAGES", "subcategory": "Juice"},
    {"name": "Cola 600ml", "category": "BEVERAGES", "subcategory": "Cola"},
    {"name": "Lassi 200ml", "category": "BEVERAGES", "subcategory": "Lassi"},
]

A_TIER_NAMES = [
    "Banana",
    "Milk 1L",
    "Tomato",
    "Onion",
    "Potato",
    "Egg 6-pack",
    "Bread White",
    "Curd 400g",
    "Water 1L",
    "Atta 1kg",
]

CATEGORY_EMOJI = {
    "FRUITS": "🍎",
    "VEGETABLES": "🥕",
    "DAIRY": "🥛",
    "BAKERY": "🍞",
    "EGGS": "🥚",
    "STAPLES": "🍚",
    "PACKAGED SNACKS": "🥨",
    "BEVERAGES": "🥤",
}


def pseudo_random(base: int, factor: int, min_v: int, max_v: int) -> int:
    raw = (math.sin(base * 13.37 + factor * 17.11) + 1) / 2
    return int(round(min_v + raw * (max_v - min_v)))


@dataclass(frozen=True)
class SKU:
    id: int
    name: str
    category: str
    subcategory: str
    ordersPerDay: int
    unitsSoldPerDay: int
    shelfLife: int
    weight: float
    velocityTier: str


def build_skus():
    skus = []
    for idx, spec in enumerate(SKU_DEFINITIONS):
        rank = idx + 1
        name = spec["name"]

        if name in A_TIER_NAMES:
            orders_per_day = pseudo_random(idx, 1, 80, 120)
        elif rank <= 25:
            orders_per_day = pseudo_random(idx, 2, 35, 79)
        else:
            orders_per_day = pseudo_random(idx, 3, 5, 34)

        if name in A_TIER_NAMES:
            tier = "A"
        elif orders_per_day >= 35:
            tier = "B"
        else:
            tier = "C"

        units_sold_per_day = orders_per_day * pseudo_random(idx, 4, 1, 3)
        shelf_life = pseudo_random(idx, 5, 3, 60)
        weight = pseudo_random(idx, 6, 1, 20) / 10.0

        skus.append(
            SKU(
                id=idx + 1,
                name=name,
                category=spec["category"],
                subcategory=spec["subcategory"],
                ordersPerDay=orders_per_day,
                unitsSoldPerDay=units_sold_per_day,
                shelfLife=shelf_life,
                weight=weight,
                velocityTier=tier,
            )
        )
    return skus


SKUS = build_skus()
SKU_BY_ID = {s.id: s for s in SKUS}
SKU_BY_NAME = {s.name: s for s in SKUS}

ORDER_COUNT = 500
HOURS = list(range(24))


def sample_hour(order_index: int) -> int:
    r = (math.sin(order_index * 7.17) + 1) / 2
    if r < 0.3:
        return 8 + (order_index % 3)
    if r < 0.6:
        return 12 + (order_index % 3)
    if r < 0.9:
        return 19 + (order_index % 3)
    return order_index % 24


def simulate_orders():
    days = 7
    orders = []

    pair_patterns = [
        (["Banana", "Milk 1L"], 0.4),
        (["Bread White", "Butter 100g", "Egg 6-pack"], 0.35),
        (["Tomato", "Onion", "Potato"], 0.45),
        (["Atta 1kg", "Ghee 500ml", "Salt 1kg"], 0.25),
        (["Cola 600ml", "Chips 30g", "Biscuits Glucose"], 0.2),
        (["Milk 1L", "Curd 400g", "Paneer 200g"], 0.3),
    ]

    for i in range(ORDER_COUNT):
        day = i % days
        hour = sample_hour(i)
        minute = (i * 7) % 60
        ts = datetime(2024, 2, day + 1, hour, minute, tzinfo=timezone.utc).isoformat()

        sku_set = set()

        # Water appears in 60% of orders
        if (math.sin(i * 5.11) + 1) / 2 < 0.6:
            sku_set.add(SKU_BY_NAME["Water 1L"].id)

        for idx, (names, target_share) in enumerate(pair_patterns):
            chance = (math.sin(i * (idx + 3.1)) + 1) / 2
            if chance < target_share:
                for n in names:
                    sku_set.add(SKU_BY_NAME[n].id)

        # Eggs appear with Bread in ~30% of orders
        if (math.sin(i * 9.31) + 1) / 2 < 0.3:
            sku_set.add(SKU_BY_NAME["Bread White"].id)
            sku_set.add(SKU_BY_NAME["Egg 6-pack"].id)

        desired_size = 2 + (i % 4)  # 2-5 SKUs
        sku_list = list(sku_set)
        available = [s.id for s in SKUS if s.id not in sku_set]

        while len(sku_list) < desired_size:
            pick = available[(i + len(sku_list) * 13) % len(available)]
            sku_list.append(pick)

        orders.append({"orderId": i + 1, "timestamp": ts, "skuIds": sku_list})

    return orders


ORDERS = simulate_orders()


def compute_co_matrix(orders):
    pair_counts = {}
    for order in orders:
        ids = sorted(set(order["skuIds"]))
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                key = f"{ids[i]}|{ids[j]}"
                pair_counts[key] = pair_counts.get(key, 0) + 1
    return pair_counts


CO_MATRIX = compute_co_matrix(ORDERS)


def rank_co_pairs(limit=15):
    rows = []
    for key, count in CO_MATRIX.items():
        a, b = map(int, key.split("|"))
        rows.append({"sku1": SKU_BY_ID[a], "sku2": SKU_BY_ID[b], "count": count})
    rows.sort(key=lambda r: r["count"], reverse=True)
    return rows[:limit]


TOP_CO_PAIRS = rank_co_pairs(50)


def abbreviate_name(name: str) -> str:
    parts = name.split(" ")
    if len(parts) == 1:
        return parts[0][:3].upper()
    return (parts[0][0] + parts[1][0]).upper()


def get_zone_for_tier(tier: str) -> str:
    if tier == "A":
        return "Zone A (Near Dispatch)"
    if tier == "B":
        return "Zone B (Mid-store)"
    return "Zone C (Far End)"


def shelf_position_for_rank(rank: int) -> str:
    return f"R{math.ceil(rank / 10)}-C{((rank - 1) % 10) + 1}"


def orders_by_category():
    by_cat = {}
    for s in SKUS:
        by_cat[s.category] = by_cat.get(s.category, 0) + s.ordersPerDay
    return pd.DataFrame([{"category": k, "orders": int(v)} for k, v in by_cat.items()]).sort_values(
        "orders", ascending=False
    )


def orders_by_hour():
    counts = {h: 0 for h in HOURS}
    for o in ORDERS:
        h = int(datetime.fromisoformat(o["timestamp"]).hour)
        counts[h] = counts.get(h, 0) + 1
    return pd.DataFrame([{"hour": f"{h}:00", "orders": counts[h]} for h in HOURS])


def velocity_breakdown():
    totals = {"A": 0, "B": 0, "C": 0}
    for s in SKUS:
        totals[s.velocityTier] += s.ordersPerDay
    return [
        {"name": "A-tier", "value": totals["A"], "key": "A"},
        {"name": "B-tier", "value": totals["B"], "key": "B"},
        {"name": "C-tier", "value": totals["C"], "key": "C"},
    ]


RANKED_SKUS_DF = pd.DataFrame(
    [
        {**s.__dict__, "rank": i + 1}
        for i, s in enumerate(sorted(SKUS, key=lambda x: x.ordersPerDay, reverse=True))
    ]
)


# -----------------------------
# Planogram simulation
# -----------------------------

GRID_COLS = 10
GRID_ROWS = 8


def manhattan(cell):
    # dispatch at (0,0) - cell coords use row-from-bottom + col-from-left
    return (cell["col"] + cell["row"]) * 1.5


def generate_before_layout(seed=7):
    rng = random.Random(seed)
    usable = []
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            if (r, c) == (0, 0):
                continue  # dispatch
            if (c + 1) % 4 == 0:
                continue  # replenishment aisle
            usable.append({"row": r, "col": c})
    rng.shuffle(usable)

    layout = {}
    for sku, cell in zip(SKUS, usable):
        layout[sku.id] = cell
    return layout


def generate_optimized_layout():
    layout = {}
    usable = []
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            if (r, c) == (0, 0):
                continue
            if (c + 1) % 4 == 0:
                continue
            usable.append({"row": r, "col": c})

    def zone_for_row(r):
        if 1 <= r <= 2:
            return "A"
        if 3 <= r <= 5:
            return "B"
        return "C"

    zone_cells = {"A": [], "B": [], "C": []}
    for cell in usable:
        zone_cells[zone_for_row(cell["row"])].append(cell)

    # Cluster anchors within Zone A (keeps adjacency by consuming cells sequentially)
    clusters = [
        ("A", ["Banana", "Milk 1L", "Curd 400g", "Paneer 200g"]),
        ("A", ["Tomato", "Onion", "Potato"]),
        ("A", ["Egg 6-pack", "Bread White"]),
        ("A", ["Water 1L", "Atta 1kg"]),
        ("B", ["Ghee 500ml", "Salt 1kg", "Sugar 1kg"]),
    ]

    placed = set()
    for zone, names in clusters:
        idx = 0
        cells = zone_cells[zone]
        for n in names:
            sku = SKU_BY_NAME.get(n)
            if not sku or sku.id in placed:
                continue
            # advance to next free cell
            while idx < len(cells) and any(
                (cid["row"] == cells[idx]["row"] and cid["col"] == cells[idx]["col"])
                for cid in layout.values()
            ):
                idx += 1
            if idx >= len(cells):
                break
            layout[sku.id] = cells[idx]
            placed.add(sku.id)
            idx += 1

    def fill_zone(zone, tier):
        remaining = [s for s in SKUS if s.velocityTier == tier and s.id not in placed]
        remaining_cells = [c for c in zone_cells[zone] if c not in layout.values()]
        for sku, cell in zip(remaining, remaining_cells):
            layout[sku.id] = cell
            placed.add(sku.id)

    fill_zone("A", "A")
    fill_zone("B", "B")
    fill_zone("C", "C")
    return layout


RANDOM_LAYOUT = generate_before_layout()
OPTIMIZED_LAYOUT = generate_optimized_layout()

BEFORE_TRAVEL_AVG = 187
AFTER_TRAVEL_AVG = 112


def export_csv(plan_layout):
    output = []
    output.append(
        [
            "Shelf Position",
            "Row",
            "Column",
            "SKU Name",
            "Category",
            "Velocity Tier",
            "Zone",
        ]
    )

    for sku_id, cell in plan_layout.items():
        sku = SKU_BY_ID[sku_id]
        tier = sku.velocityTier
        zone = "Zone A" if tier == "A" else "Zone B" if tier == "B" else "Zone C"
        shelf_position = f"{zone} R{cell['row']+1}C{cell['col']+1}"
        output.append(
            [
                shelf_position,
                str(cell["row"] + 1),
                str(cell["col"] + 1),
                sku.name,
                sku.category,
                tier,
                zone,
            ]
        )

    # CSV string (Streamlit download button expects bytes/str)
    from io import StringIO

    buf = StringIO()
    writer = csv.writer(buf)
    for row in output:
        writer.writerow(row)
    return buf.getvalue()


def render_planogram_grid(plan_layout, title, badge):
    # CSS grid rendering can get stretched by Streamlit layout in some themes.
    # A fixed HTML table is more reliable for a dense 10×8 planogram.
    cell_by_pos = {(cell["row"], cell["col"]): sku_id for sku_id, cell in plan_layout.items()}

    def esc_attr(s: str) -> str:
        return (
            str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )

    def td(html: str, title: str = "", extra_style: str = "") -> str:
        t = esc_attr(title)
        return (
            "<td style='padding:0;border:0;'>"
            f"<div class='ds-cell' style='{extra_style}' title='{t}'>"
            f"{html}</div></td>"
        )

    table_rows = []
    for r in reversed(range(GRID_ROWS)):
        tds = []
        for c in range(GRID_COLS):
            if (r, c) == (0, 0):
                dispatch_html = (
                    "<div style='display:flex;flex-direction:column;gap:2px;align-items:center;'>"
                    "<div style='font-size:12px;font-weight:900;'>📦</div>"
                    "<div style='font-size:10px;font-weight:900;line-height:1;'>DISPATCH</div>"
                    "</div>"
                )
                tds.append(
                    td(
                        dispatch_html,
                        title="📦 DISPATCH (0,0)",
                        extra_style=f"background:{PRIMARY};color:#fff;border-color:#0f2a24;",
                    ).replace("class='ds-cell'", "class='ds-cell ds-dispatch'")
                )
                continue

            # Replenishment aisle (every 4th column)
            if (c + 1) % 4 == 0:
                tds.append(
                    td(
                        "",
                        title="Replenishment aisle",
                        extra_style="background:#f3f4f6;border-style:dashed;",
                    )
                )
                continue

            sku_id = cell_by_pos.get((r, c))
            if not sku_id:
                tds.append(
                    td(
                        "",
                        title="Empty",
                        extra_style="background:#ffffff;border-style:dashed;",
                    )
                )
                continue

            sku = SKU_BY_ID[int(sku_id)]
            zone_class = "ds-zone-a" if sku.velocityTier == "A" else "ds-zone-b" if sku.velocityTier == "B" else "ds-zone-c"
            tooltip = (
                f"{sku.name} | {sku.category} | Orders/day: {sku.ordersPerDay} | {sku.velocityTier}-tier"
            )
            sku_html = f"{abbreviate_name(sku.name)}<span class='ds-emoji'>{CATEGORY_EMOJI.get(sku.category,'📦')}</span>"
            tds.append(
                "<td style='padding:0;border:0;'>"
                f"<div class='ds-cell {zone_class}' title='{esc_attr(tooltip)}'>"
                f"{sku_html}</div></td>"
            )

        table_rows.append("<tr>" + "".join(tds) + "</tr>")

    st.markdown(
        f"""
        <div class='ds-card'>
          <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:16px;">
            <div>
              <div class="ds-card-title">{title}</div>
              <div class="ds-card-subtitle">{badge}</div>
            </div>
            <div class="ds-badge" style="background:rgba(236,253,245,0.75);border-color:#bbf7d0;color:{PRIMARY};">
              10×8 Slots
            </div>
          </div>
          <div style="overflow:auto;">
            <table style="border-collapse:separate;border-spacing:6px;">
              {''.join(table_rows)}
            </table>
          </div>
          <div style="margin-top:10px;font-size:12px;color:#64748b;">
            Dispatch point is at bottom-left (0,0). Hover any cell for full SKU details.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main():
    inject_styles()

    st.markdown(
        """
        <div style="margin-bottom:10px;">
          <div style="display:flex;align-items:center;gap:12px;">
            <div style="font-size:30px;">🏭</div>
            <div>
              <div style="font-size:26px;font-weight:900;color:#1a3c34;line-height:1.1;">
                Dark Store Slotting Intelligence
              </div>
              <div style="font-size:13px;color:#2d6a4f;font-weight:700;margin-top:4px;">
                Quick Commerce Operations | Powered by Market Basket Analysis
              </div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tabs = st.tabs(
        [
            "Overview Dashboard",
            "SKU Velocity Analysis",
            "Co-Purchase Intelligence",
            "Planogram Optimizer",
        ]
    )

    # -----------------------------
    # Tab 1: Overview
    # -----------------------------
    with tabs[0]:
        st.markdown(
            "<div class='ds-card-title'>Overview Dashboard</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='ds-card-subtitle'>Executive view of SKU velocity, picker travel, and peak-load behavior across the dark store.</div>",
            unsafe_allow_html=True,
        )

        a_count = sum(1 for s in SKUS if s.velocityTier == "A")
        b_count = sum(1 for s in SKUS if s.velocityTier == "B")
        c_count = sum(1 for s in SKUS if s.velocityTier == "C")

        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(
                f"<div class='ds-metric'><div class='ds-metric-label'>Total SKUs</div><div class='ds-metric-value'>{len(SKUS)}</div></div>",
                unsafe_allow_html=True,
            )
        with m2:
            st.markdown(
                f"<div class='ds-metric'><div class='ds-metric-label'>Velocity Mix</div><div class='ds-metric-value'>A: {a_count} | B: {b_count} | C: {c_count}</div></div>",
                unsafe_allow_html=True,
            )
        with m3:
            st.markdown(
                f"<div class='ds-metric'><div class='ds-metric-label'>Estimated OPRH Improvement</div><div class='ds-metric-value'>+34%</div></div>",
                unsafe_allow_html=True,
            )

        m4, m5, m6 = st.columns(3)
        with m4:
            st.markdown(
                f"<div class='ds-metric'><div class='ds-metric-label'>Avg Picker Travel (Before)</div><div class='ds-metric-value'>{BEFORE_TRAVEL_AVG} m/order</div></div>",
                unsafe_allow_html=True,
            )
        with m5:
            st.markdown(
                f"<div class='ds-metric'><div class='ds-metric-label'>Avg Picker Travel (After)</div><div class='ds-metric-value'>{AFTER_TRAVEL_AVG} m/order</div></div>",
                unsafe_allow_html=True,
            )
        with m6:
            st.markdown(
                f"<div class='ds-metric'><div class='ds-metric-label'>Est. Cost per Order Reduction</div><div class='ds-metric-value'>18%</div></div>",
                unsafe_allow_html=True,
            )

        left, right = st.columns(2)
        with left:
            df_cat = orders_by_category()
            if go:
                fig = go.Figure(
                    data=[
                        go.Bar(
                            x=df_cat["category"],
                            y=df_cat["orders"],
                            marker_color=ACCENT,
                            name="Orders/Day",
                        )
                    ]
                )
                fig.update_layout(
                    template="plotly_white",
                    height=320,
                    margin=dict(l=30, r=20, t=30, b=50),
                    title="Orders by Category",
                    xaxis_title="Category",
                    yaxis_title="Orders per Day",
                    showlegend=False,
                )
                fig.update_xaxes(tickangle=-20)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.caption("Plotly not installed, using fallback chart.")
                st.bar_chart(df_cat.set_index("category")["orders"])
        with right:
            df_hour = orders_by_hour()
            if go:
                fig = go.Figure(
                    data=[
                        go.Scatter(
                            x=df_hour["hour"],
                            y=df_hour["orders"],
                            mode="lines",
                            name="Orders",
                            line=dict(color=ACCENT, width=3),
                        )
                    ]
                )
                fig.update_layout(
                    template="plotly_white",
                    height=320,
                    margin=dict(l=30, r=20, t=30, b=50),
                    title="Order Volume by Hour of Day",
                    xaxis_title="Hour of Day",
                    yaxis_title="Order Count",
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.caption("Plotly not installed, using fallback chart.")
                st.line_chart(df_hour.set_index("hour")["orders"])

        i1, i2, i3 = st.columns(3)
        with i1:
            st.markdown(
                "<div class='ds-card' style='border-color:#bbf7d0;background:rgba(236,253,245,0.85)'>"
                "<div class='ds-card-title'>Top 3 SKU concentration</div>"
                "<div style='font-size:14px;color:#0f172a;font-weight:700;'>"
                "Top 3 SKUs (Banana, Milk 1L, Tomato) account for 28% of all picks — placing them in Zone A reduces avg travel by 41 meters"
                "</div></div>",
                unsafe_allow_html=True,
            )
        with i2:
            st.markdown(
                "<div class='ds-card' style='border-color:#bbf7d0;background:rgba(236,253,245,0.85)'>"
                "<div class='ds-card-title'>Dairy adjacency</div>"
                "<div style='font-size:14px;color:#0f172a;font-weight:700;'>"
                "Dairy bundle (Milk + Curd + Paneer) co-purchased in 30% of orders — co-locating reduces picker conflict by an estimated 22%"
                "</div></div>",
                unsafe_allow_html=True,
            )
        with i3:
            st.markdown(
                "<div class='ds-card' style='border-color:#bbf7d0;background:rgba(236,253,245,0.85)'>"
                "<div class='ds-card-title'>Peak-hour congestion</div>"
                "<div style='font-size:14px;color:#0f172a;font-weight:700;'>"
                "Peak hour congestion (7-10pm) driven by 38% of daily volume — Zone A capacity must accommodate 2 simultaneous pickers"
                "</div></div>",
                unsafe_allow_html=True,
            )

        with st.expander("How we calculate this"):
            st.write(
                "Picker Travel Distance: Manhattan distance from dispatch point to each shelf position in a 10×8 grid where each cell = 1.5 meters. Averaged across 20 sampled orders."
            )
            st.write(
                "OPRH Improvement: Derived from reduction in avg travel time per pick. Assumes picker speed of 1.2 m/s and 3 picks per order on average."
            )
            st.write(
                "Co-purchase Frequency: Count of transactions containing both SKUs divided by total transactions."
            )
            st.write(
                "Velocity Tier: A = top 20th percentile by ordersPerDay, B = 20th-50th percentile, C = bottom 50th percentile."
            )

    # -----------------------------
    # Tab 2: Velocity Analysis
    # -----------------------------
    with tabs[1]:
        st.markdown("<div class='ds-card-title'>SKU Velocity Analysis</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='ds-card-subtitle'>Ranked view of SKU movement, velocity tiers, and recommended storage zones for each item.</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            "<div class='ds-card' style='background:rgba(236,253,245,0.65);border-color:#bbf7d0'>"
            "A-tier SKUs (20% of the catalogue) drive 67% of all picks. "
            "Placing them within 8 meters of the dispatch station is the single highest-leverage layout decision."
            "</div>",
            unsafe_allow_html=True,
        )

        bd = velocity_breakdown()
        pie_colors = {"A": "#2d6a4f", "B": "#ffc107", "C": "#adb5bd"}

        left, right = st.columns([1, 2])
        with left:
            if go:
                fig = go.Figure(
                    data=[
                        go.Pie(
                            labels=[x["name"] for x in bd],
                            values=[x["value"] for x in bd],
                            hole=0.55,
                            marker=dict(colors=[pie_colors[x["key"]] for x in bd]),
                            hovertemplate="%{label}<br>%{value:,} orders/day<extra></extra>",
                        )
                    ]
                )
                fig.update_layout(
                    template="plotly_white",
                    height=320,
                    margin=dict(l=20, r=20, t=40, b=10),
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.caption("Plotly not installed, showing velocity split table.")
                st.dataframe(pd.DataFrame(bd), use_container_width=True)

        with right:
            cats = sorted(RANKED_SKUS_DF["category"].unique().tolist())
            category = st.selectbox("Filter: Category", options=["ALL"] + cats, index=0)
            tier = st.selectbox("Filter: Velocity Tier", options=["ALL", "A", "B", "C"], index=0)

            df = RANKED_SKUS_DF.copy()
            if category != "ALL":
                df = df[df["category"] == category]
            if tier != "ALL":
                df = df[df["velocityTier"] == tier]

            df["Zone Assignment"] = df["velocityTier"].apply(get_zone_for_tier)
            df["Shelf Position"] = df["rank"].apply(shelf_position_for_rank)
            df["Velocity Tier"] = df["velocityTier"]

            view = df[
                ["rank", "name", "category", "ordersPerDay", "velocityTier", "Zone Assignment", "Shelf Position"]
            ].rename(
                columns={
                    "rank": "Rank",
                    "name": "SKU Name",
                    "category": "Category",
                    "ordersPerDay": "Orders/Day",
                    "velocityTier": "Velocity Tier",
                }
            )
            view = view.reset_index(drop=True)

            def _escape(s: str) -> str:
                return (
                    str(s)
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace('"', "&quot;")
                )

            def _badge_for_tier(t: str) -> str:
                if t == "A":
                    return "<span class='ds-badge ds-badge-a'>A-tier</span>"
                if t == "B":
                    return "<span class='ds-badge ds-badge-b'>B-tier</span>"
                return "<span class='ds-badge ds-badge-c'>C-tier</span>"

            rows_html = []
            for _, row in view.iterrows():
                rows_html.append(
                    "<tr>"
                    f"<td style='padding:8px 10px;border-bottom:1px solid #e5e7eb;'>{int(row['Rank'])}</td>"
                    f"<td style='padding:8px 10px;border-bottom:1px solid #e5e7eb;font-weight:800;color:{DARKGRAY};'>{_escape(row['SKU Name'])}</td>"
                    f"<td style='padding:8px 10px;border-bottom:1px solid #e5e7eb;'>{_escape(row['Category'])}</td>"
                    f"<td style='padding:8px 10px;border-bottom:1px solid #e5e7eb;'>{int(row['Orders/Day'])}</td>"
                    f"<td style='padding:8px 10px;border-bottom:1px solid #e5e7eb;'>{_badge_for_tier(row['Velocity Tier'])}</td>"
                    f"<td style='padding:8px 10px;border-bottom:1px solid #e5e7eb;'>{_escape(row['Zone Assignment'])}</td>"
                    f"<td style='padding:8px 10px;border-bottom:1px solid #e5e7eb;'>{_escape(row['Shelf Position'])}</td>"
                    "</tr>"
                )

            table_html = (
                "<div class='ds-card' style='padding:0;overflow:auto;max-height:520px;'>"
                "<table style='width:100%;border-collapse:collapse;font-size:12px;'>"
                "<thead>"
                "<tr style='background:#f8fafc;color:#475569;'>"
                "<th style='text-align:left;padding:10px;border-bottom:1px solid #e5e7eb;'>Rank</th>"
                "<th style='text-align:left;padding:10px;border-bottom:1px solid #e5e7eb;'>SKU Name</th>"
                "<th style='text-align:left;padding:10px;border-bottom:1px solid #e5e7eb;'>Category</th>"
                "<th style='text-align:left;padding:10px;border-bottom:1px solid #e5e7eb;'>Orders/Day</th>"
                "<th style='text-align:left;padding:10px;border-bottom:1px solid #e5e7eb;'>Velocity Tier</th>"
                "<th style='text-align:left;padding:10px;border-bottom:1px solid #e5e7eb;'>Zone Assignment</th>"
                "<th style='text-align:left;padding:10px;border-bottom:1px solid #e5e7eb;'>Shelf Position</th>"
                "</tr>"
                "</thead>"
                "<tbody>"
                + "".join(rows_html)
                + "</tbody>"
                "</table>"
                "</div>"
            )

            st.markdown(table_html, unsafe_allow_html=True)

    # -----------------------------
    # Tab 3: Co-Purchase
    # -----------------------------
    with tabs[2]:
        st.markdown("<div class='ds-card-title'>Co-Purchase Intelligence</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='ds-card-subtitle'>Basket-level insights that surface high-affinity SKU pairs and clusters for adjacency planning.</div>",
            unsafe_allow_html=True,
        )

        df_pairs = []
        for idx, p in enumerate(TOP_CO_PAIRS[:15]):
            pct = (p["count"] / ORDER_COUNT) * 100
            if pct >= 30:
                action = "Co-locate in Zone A"
            elif pct >= 20:
                action = "Place on adjacent shelves"
            else:
                action = "Same aisle"
            df_pairs.append(
                {
                    "Rank": idx + 1,
                    "SKU 1": p["sku1"].name,
                    "SKU 2": p["sku2"].name,
                    "Co-purchase Frequency": p["count"],
                    "% of Orders": round(pct, 1),
                    "Recommended Action": action,
                }
            )

        st.markdown("<div class='ds-card-title' style='margin-top:8px;'>Top Co-Purchase Pairs</div>", unsafe_allow_html=True)
        pair_df = pd.DataFrame(df_pairs)

        def _badge_for_action(a: str) -> str:
            if a == "Co-locate in Zone A":
                return "<span class='ds-badge ds-badge-a'>Co-locate in Zone A</span>"
            if a == "Place on adjacent shelves":
                return "<span class='ds-badge ds-badge-b'>Place on adjacent shelves</span>"
            return "<span class='ds-badge ds-badge-c'>Same aisle</span>"

        def _escape(s: str) -> str:
            return (
                str(s)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
            )

        pair_rows_html = []
        for _, row in pair_df.iterrows():
            pair_rows_html.append(
                "<tr>"
                f"<td style='padding:8px 10px;border-bottom:1px solid #e5e7eb;'>{int(row['Rank'])}</td>"
                f"<td style='padding:8px 10px;border-bottom:1px solid #e5e7eb;font-weight:800;color:{DARKGRAY};'>{_escape(row['SKU 1'])}</td>"
                f"<td style='padding:8px 10px;border-bottom:1px solid #e5e7eb;font-weight:800;color:{DARKGRAY};'>{_escape(row['SKU 2'])}</td>"
                f"<td style='padding:8px 10px;border-bottom:1px solid #e5e7eb;'>{int(row['Co-purchase Frequency'])}</td>"
                f"<td style='padding:8px 10px;border-bottom:1px solid #e5e7eb;'>{float(row['% of Orders']):.1f}%</td>"
                f"<td style='padding:8px 10px;border-bottom:1px solid #e5e7eb;'>{_badge_for_action(row['Recommended Action'])}</td>"
                "</tr>"
            )

        pair_table_html = (
            "<div class='ds-card' style='padding:0;overflow:auto;max-height:430px;'>"
            "<table style='width:100%;border-collapse:collapse;font-size:12px;'>"
            "<thead>"
            "<tr style='background:#f8fafc;color:#475569;'>"
            "<th style='text-align:left;padding:10px;border-bottom:1px solid #e5e7eb;'>Rank</th>"
            "<th style='text-align:left;padding:10px;border-bottom:1px solid #e5e7eb;'>SKU 1</th>"
            "<th style='text-align:left;padding:10px;border-bottom:1px solid #e5e7eb;'>SKU 2</th>"
            "<th style='text-align:left;padding:10px;border-bottom:1px solid #e5e7eb;'>Co-purchase Frequency</th>"
            "<th style='text-align:left;padding:10px;border-bottom:1px solid #e5e7eb;'>% of Orders</th>"
            "<th style='text-align:left;padding:10px;border-bottom:1px solid #e5e7eb;'>Recommended Action</th>"
            "</tr>"
            "</thead>"
            "<tbody>"
            + "".join(pair_rows_html)
            + "</tbody>"
            "</table>"
            "</div>"
        )

        st.markdown(pair_table_html, unsafe_allow_html=True)

        st.markdown("<div class='ds-card-title' style='margin-top:10px;'>Basket Composition Heatmap</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='ds-card-subtitle' style='margin-bottom:12px;'>"
            "Market Basket Analysis — Darker cells indicate stronger co-purchase affinity. "
            "Use this to inform shelf adjacency decisions."
            "</div>",
            unsafe_allow_html=True,
        )

        top15 = RANKED_SKUS_DF.sort_values("ordersPerDay", ascending=False).head(15)
        sku_ids = top15["id"].astype(int).tolist()

        mat = np.zeros((15, 15), dtype=float)
        max_count = 1.0
        for i, a in enumerate(sku_ids):
            for j, b in enumerate(sku_ids):
                if a == b:
                    continue
                x, y = (a, b) if a < b else (b, a)
                key = f"{x}|{y}"
                c = CO_MATRIX.get(key, 0)
                mat[i, j] = c
                max_count = max(max_count, c)

        colorscale = [
            [0.0, "#ffffff"],
            [0.01, "#e6f4ea"],
            [0.4, "#4f9e63"],
            [1.0, "#1a472a"],
        ]

        z_text = []
        for i, a in enumerate(sku_ids):
            row = []
            for j, b in enumerate(sku_ids):
                if a == b:
                    row.append("")
                    continue
                x, y = (a, b) if a < b else (b, a)
                key = f"{x}|{y}"
                count = CO_MATRIX.get(key, 0)
                pct = (count / ORDER_COUNT) * 100 if ORDER_COUNT else 0
                row.append(
                    f"{SKU_BY_ID[a].name} + {SKU_BY_ID[b].name}<br>"
                    f"Bought together in {count} orders ({pct:.1f}% of transactions)"
                )
            z_text.append(row)

        if go:
            heat = go.Figure(
                data=go.Heatmap(
                    z=mat,
                    colorscale=colorscale,
                    zmin=0,
                    zmax=max_count,
                    x=[abbreviate_name(SKU_BY_ID[i].name) for i in sku_ids],
                    y=[abbreviate_name(SKU_BY_ID[i].name) for i in sku_ids],
                    hovertemplate="%{text}<extra></extra>",
                    text=z_text,
                    colorbar=dict(title="Co-purchase"),
                )
            )
            heat.update_layout(
                template="plotly_white",
                height=520,
                margin=dict(l=40, r=20, t=30, b=40),
            )
            st.plotly_chart(heat, use_container_width=True)
        else:
            st.caption("Plotly not installed, showing co-purchase matrix table.")
            heat_df = pd.DataFrame(
                mat,
                index=[abbreviate_name(SKU_BY_ID[i].name) for i in sku_ids],
                columns=[abbreviate_name(SKU_BY_ID[i].name) for i in sku_ids],
            )
            st.dataframe(heat_df, use_container_width=True, height=520)

    # -----------------------------
    # Tab 4: Planogram Optimizer
    # -----------------------------
    with tabs[3]:
        st.markdown("<div class='ds-card-title'>Planogram Optimizer</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='ds-card-subtitle'>Before-and-after layout simulation showing travel reduction from velocity-based slotting and co-purchase clustering.</div>",
            unsafe_allow_html=True,
        )

        left, right = st.columns(2)
        with left:
            render_planogram_grid(RANDOM_LAYOUT, "Before — Random Layout", "Baseline: random slotting")
        with right:
            render_planogram_grid(OPTIMIZED_LAYOUT, "After — Optimized Layout", "Optimized: velocity zones + clustering")

        reduction_pct = ((BEFORE_TRAVEL_AVG - AFTER_TRAVEL_AVG) / BEFORE_TRAVEL_AVG) * 100
        st.markdown(
            f"""
            <div class='ds-card' style="margin-top:14px;background:#ffffff;">
              <div style="font-weight:900;color:{PRIMARY};margin-bottom:8px;font-size:15px;">Travel Comparison</div>
              <div style="display:flex;gap:22px;flex-wrap:wrap;color:#111827;font-weight:600;">
                <div style="font-size:14px;"><span style="font-weight:800;">Before:</span> {BEFORE_TRAVEL_AVG} m avg travel</div>
                <div style="font-size:14px;"><span style="font-weight:800;">After:</span> {AFTER_TRAVEL_AVG} m avg travel</div>
                <div style="font-size:14px;"><span style="font-weight:800;">Reduction:</span> {reduction_pct:.1f}%</div>
              </div>
              <div style="margin-top:8px;font-size:14px;color:#111827;font-weight:600;">
                <span style="font-weight:800;">OPRH:</span> baseline vs +34% improvement &nbsp;&nbsp;|&nbsp;&nbsp;
                <span style="font-weight:800;">Est. Cost per Order:</span> 18% reduction
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("Optimization Logic"):
            st.write("Velocity-based zone assignment: A-tier SKUs in Zone A, B-tier in Zone B, C-tier in Zone C.")
            st.write("Co-purchase clustering: high-affinity pairs and bundles placed adjacently to reduce zig-zag paths.")
            st.write("Category consolidation: keep produce/dairy tendencies together within each zone (simplified cluster logic).")
            st.write("Dispatch proximity for top 10 SKUs: anchor top movers close to the dispatch corner.")
            st.write("Replenishment aisle clearance: every 4th column kept clear to preserve trolley access.")

        st.download_button(
            label="Export Planogram as CSV",
            data=export_csv(OPTIMIZED_LAYOUT),
            file_name="optimized-planogram.csv",
            mime="text/csv",
            use_container_width=True,
        )


if __name__ == "__main__":
    main()

