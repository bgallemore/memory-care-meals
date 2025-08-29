# /Projects/memory_care_meals/generate_plate_counts.py
import pandas as pd
import numpy as np

BASE = "/Projects/memory_care_meals"

# --- Load base data ---
menu = pd.read_csv(f"{BASE}/menu_calendar.csv")
residents = pd.read_csv(f"{BASE}/residents.csv")

# Reproducibility
SEED = 42
rng = np.random.default_rng(SEED)

# --- Tunable knobs (adjust to taste) ---
OVERPREP_BASE = 0.08   # 8% over-prep baseline
OVERPREP_JITTER = 0.04 # +/- range around baseline
WASTE_TARGET_MIN = 0.05  # 5%
WASTE_TARGET_MAX = 0.15  # 15%

# Attendance by meal (avg fraction of census)
MEAL_ATTENDANCE = {
    "breakfast": 0.85,
    "lunch":     0.92,
    "dinner":    0.90,
}

# Weekday effect on attendance (Mon=0 ... Sun=6)
# Positive values increase attendance, negative decrease
DOW_ATTENDANCE_ADJ = {
    0: -0.01,  # Mon
    1:  0.00,  # Tue
    2:  0.00,  # Wed
    3:  0.01,  # Thu
    4:  0.02,  # Fri (slightly better attendance)
    5: -0.02,  # Sat
    6: -0.03,  # Sun (family visits may skew)
}

# Occasional “event” days (e.g., BBQ, special menu) modestly impact waste
# Positive = more waste, negative = less waste (residents like it!)
EVENT_PROB = 0.08
EVENT_WASTE_ADJ_RANGE = (-0.04, 0.06)

# --- Helper ---
def clamp(x, lo, hi):
    return max(lo, min(hi, x))

# --- Prepare dates ---
menu["date"] = pd.to_datetime(menu["date"], errors="coerce")
N = len(residents)

rows = []
for _, r in menu.iterrows():
    meal = str(r.get("meal_type", "lunch")).lower()
    date = r["date"]
    rid  = int(r["recipe_id"])

    # Attendance expectation
    base_att = MEAL_ATTENDANCE.get(meal, 0.90)
    dow_adj = DOW_ATTENDANCE_ADJ.get(date.weekday(), 0.0)
    att = clamp(base_att + dow_adj + rng.normal(0, 0.015), 0.75, 0.98)

    # Over-prep factor: baseline 8% +/- jitter
    overprep = clamp(OVERPREP_BASE + rng.uniform(-OVERPREP_JITTER, OVERPREP_JITTER), 0.02, 0.18)

    # Target waste band (5–15%), plus small jitter
    waste_target = clamp(rng.uniform(WASTE_TARGET_MIN, WASTE_TARGET_MAX) + rng.normal(0, 0.005), 0.02, 0.20)

    # Occasionally apply an “event” effect on waste
    if rng.random() < EVENT_PROB:
        waste_target = clamp(waste_target + rng.uniform(*EVENT_WASTE_ADJ_RANGE), 0.01, 0.25)

    # Compute prepared & served
    # Start from census-based expected diners; chef prepares a bit extra (overprep)
    expected_diners = int(round(N * att))
    prepared = int(round(expected_diners * (1 + overprep)))
    prepared = max(prepared, 0)

    # Waste ≈ target% of prepared (integer plates)
    leftover = int(round(prepared * waste_target))
    leftover = clamp(leftover, 0, prepared)

    served = prepared - leftover
    # Never exceed expected diners by too much; adjust leftovers if needed
    if served > expected_diners + int(0.05 * N):
        served = expected_diners + int(0.05 * N)
        leftover = prepared - served

    rows.append([
        date.date().isoformat(),
        meal,
        rid,
        prepared,
        served,
        leftover
    ])

plates = pd.DataFrame(rows, columns=["date","meal_type","recipe_id","prepared","served","leftover"])
plates.to_csv(f"{BASE}/plate_counts.csv", index=False)
print("✅ Wrote", f"{BASE}/plate_counts.csv")
print(plates.head())
