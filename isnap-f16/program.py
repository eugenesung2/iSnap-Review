import pandas as pd

first_second_hints = pd.read_csv("ratings.csv")

first_second_hints.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
dtype_map = {}

for idx, col in enumerate(first_second_hints.columns):
    if idx in (0, 1, 4):
        dtype_map[col] = "string"
    elif idx == 9:
        dtype_map[col] = "float64"
    elif idx == 10:
        dtype_map[col] = "boolean"
    else:
        dtype_map[col] = "Int64"

df = first_second_hints.astype(dtype_map)



print(df.info())