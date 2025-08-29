# Restart Guide — Memory Care Meals (Target base: /Projects/memory_care_meals)

1) Move the **memory_care_meals/** folder to **/Projects/memory_care_meals** so files live at `/Projects/memory_care_meals/...`

2) In VS Code terminal:
```
python -m venv .venv
# Windows
.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate
pip install -r memory_care_meals/requirements.txt
```

3) Generate & analyze plate counts:
```
python memory_care_meals/generate_plate_counts.py
python memory_care_meals/analyze_plate_counts.py
```

4) Optional: Streamlit dashboard
```
pip install -r memory_care_meals/requirements_streamlit.txt
streamlit run memory_care_meals/app.py
```
