import pandas as pd, numpy as np
BASE = "/Projects/memory_care_meals"
residents = pd.read_csv(f"{BASE}/residents.csv")
recipes   = pd.read_csv(f"{BASE}/recipes.csv")
menu      = pd.read_csv(f"{BASE}/menu_calendar.csv")
standards = pd.read_csv(f"{BASE}/nutrition_standards_daily.csv")
plates    = pd.read_csv(f"{BASE}/plate_counts.csv")
for df in (recipes, menu, plates, standards):
    df.columns = [c.strip().lower() for c in df.columns]
for df in (menu, plates):
    if "recipe_id" in df.columns:
        df["recipe_id"] = pd.to_numeric(df["recipe_id"], errors="coerce")
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
menu_detail = menu.merge(recipes, on="recipe_id", how="left")
if "meal_type_x" in menu_detail.columns and "meal_type_y" in menu_detail.columns:
    menu_detail["meal_type"] = menu_detail["meal_type_x"].combine_first(menu_detail["meal_type_y"])
    menu_detail = menu_detail.drop(columns=["meal_type_x","meal_type_y"])
if "meal_type" not in plates.columns or plates["meal_type"].isna().any():
    plates = plates.merge(menu[["date","recipe_id","meal_type"]].drop_duplicates(), on=["date","recipe_id"], how="left")
merge_keys = ["date","recipe_id"]
plate_cols = ["date","recipe_id","prepared","served","leftover"]
if "meal_type" in plates.columns:
    plate_cols.insert(1, "meal_type")
detail = menu_detail.merge(plates[plate_cols], on=merge_keys, how="left", validate="m:1")
detail["cost_served"] = detail["estimated_cost_per_serving_usd"] * detail["served"]
detail["waste_pct"]   = np.where(detail["prepared"]>0, detail["leftover"]/detail["prepared"], np.nan)
daily = detail.groupby(detail["date"].dt.date, as_index=False).agg(
    calories_kcal=("calories_kcal","sum"),
    protein_g=("protein_g","sum"),
    carbs_g=("carbs_g","sum"),
    fat_g=("fat_g","sum"),
    sodium_mg=("sodium_mg","sum"),
    fiber_g=("fiber_g","sum"),
    prepared=("prepared","sum"),
    served=("served","sum"),
    leftover=("leftover","sum"),
    cost_served=("cost_served","sum"),
).rename(columns={"date":"day"})
daily["waste_pct"] = np.where(daily["prepared"]>0, daily["leftover"]/daily["prepared"], np.nan)
daily["approx_cost_per_resident_day_usd"] = daily["cost_served"] / max(len(residents),1)
daily.to_csv(f"{BASE}/daily_summary_with_plate_counts.csv", index=False)
print("Wrote", f"{BASE}/daily_summary_with_plate_counts.csv")