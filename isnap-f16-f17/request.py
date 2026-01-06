import pandas as pd
import json
from collections import defaultdict

# load request data
requests = pd.read_csv("requests.csv")

# ensure correct ordering
requests = requests.sort_values("index")

# compute max index per trace FIRST
requests["max_index"] = (
    requests
    .groupby(["assignmentID", "traceID"])["index"]
    .transform("max")
)

# isolate the actual hint request (final snapshot per trace)
request_states = (
    requests
    .groupby(["assignmentID", "traceID"])
    .tail(1)
    .reset_index(drop=True)
)

# compute relative position of the request within the trace
request_states["request_progress"] = (
    request_states["index"] / request_states["max_index"]
)

# load snap grammar
with open("snap-grammar.json") as f:
    grammar = json.load(f)

# build mapping from node type to grammar category
type_to_category = {}
for category, types in grammar["categories"].items():
    for t in types:
        type_to_category[t] = category

# grammar-aware AST traversal
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

# extract grammar-aware features at request time
rows = []

for _, row in request_states.iterrows():
    ast = json.loads(row["code"])
    cat_counts = count_categories(ast, type_to_category)

    rows.append({
        "assignmentID": row["assignmentID"],
        "traceID": row["traceID"],
        "index": row["index"],
        "request_progress": row["request_progress"],
        "n_COMMAND": cat_counts.get("COMMAND", 0),
        "n_REPORTER": cat_counts.get("REPORTER", 0),
        "n_HAT": cat_counts.get("HAT", 0),
        "n_BOOLEAN": cat_counts.get("BOOLEAN", 0),
    })

request_analysis_df = pd.DataFrame(rows)

print(request_analysis_df.info())
print(request_analysis_df.head())