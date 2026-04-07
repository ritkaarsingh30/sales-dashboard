import pandas as pd
from loaders import load_visit_tracker

with open('IVC MARCH REPORT.xlsx', 'rb') as f1, open('Ivory coast visit tracker  feb-2026.xlsx', 'rb') as f2:
    visit_data = load_visit_tracker([(f2.read(), 'Feb'), (f1.read(), 'Mar')])

print(visit_data.head())
print("Total rows:", len(visit_data))
print(visit_data.groupby(['MR', 'Month']).size())
