import pandas as pd
import json
from collections import defaultdict
import numpy as np

training = pd.read_csv("training.csv")

with open("snap-grammar.json") as f:
    grammar = json.load(f)

# compute number of steps per trace (index starts at 0)
steps_per_trace = (
    training
    .groupby(["assignmentID", "traceID"])
    .agg(n_steps=("index", "max"))
    .reset_index()
)
steps_per_trace["n_steps"] += 1

print(
    steps_per_trace
    .groupby("assignmentID")["n_steps"]
    .agg(["mean", "median"])
)

# build mapping from node type to grammar category
type_to_category = {}
for category, types in grammar["categories"].items():
    for t in types:
        type_to_category[t] = category

# count grammar categories in an AST
def count_categories(ast, type_to_category):
    counts = defaultdict(int)

    def visit(node):
        if not isinstance(node, dict):
            return

        node_type = node.get("type")
        category = type_to_category.get(node_type)

        if category:
            counts[category] += 1

        for child in node.get("children", {}).values():
            visit(child)

    visit(ast)
    return counts

# extract grammar-aware features for each snapshot
rows = []

for _, row in training.iterrows():
    ast = json.loads(row["code"])
    cat_counts = count_categories(ast, type_to_category)

    rows.append({
        "assignmentID": row["assignmentID"],
        "traceID": row["traceID"],
        "index": row["index"],
        "n_COMMAND": cat_counts.get("COMMAND", 0),
        "n_REPORTER": cat_counts.get("REPORTER", 0),
        "n_HAT": cat_counts.get("HAT", 0),
        "n_BOOLEAN": cat_counts.get("BOOLEAN", 0),
    })

grammar_features = pd.DataFrame(rows)

# compute normalised progress within each trace
grammar_features["max_index"] = (
    grammar_features
    .groupby(["assignmentID", "traceID"])["index"]
    .transform("max")
)

grammar_features["progress"] = (
    grammar_features["index"] / grammar_features["max_index"]
)

# bin progress to stabilise aggregation
grammar_features["progress_bin"] = pd.cut(
    grammar_features["progress"],
    bins=np.linspace(0, 1, 11),
    include_lowest=True
)

print(steps_per_trace.info())




# aggregate structural evolution across traces
evolution = (
    grammar_features
    .groupby(["assignmentID", "progress_bin"], observed=True)
    .agg(
        mean_COMMAND=("n_COMMAND", "mean"),
        mean_REPORTER=("n_REPORTER", "mean"),
        mean_HAT=("n_HAT", "mean"),
    )
    .reset_index()
)




print("\nEvolution (first few rows):")
print(evolution.info())