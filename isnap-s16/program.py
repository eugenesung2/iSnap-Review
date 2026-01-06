import json
from pathlib import Path
import pandas as pd

def load_python_grammar(grammar_path: str) -> dict:
    """Loads Python grammer into a dataframe.

    Args:
        grammar_path: CSV file name for Python grammer.

    Returns:
        dict: A dictionary with the Python AST grammar, with
        entries such as root node types, valid node definitions,
        category mappings, and special types.
    """
    with open(grammar_path, "r") as file:
        return json.load(file)


def load_traces(csv_path: str, type: str) -> pd.DataFrame:
    """Loads either training or request CSV file into a dataframe.

    Args:
        csv_path: CSV file name for training or request.
        type: Categorise the file as either training or request.

    Returns:
        pd.DataFrame:
    """
    df = pd.read_csv(csv_path)

    return pd.DataFrame({
        "type": type,
        "assignmentID": df["assignmentID"].astype(str),
        "traceID": df["traceID"].astype(str),
        "index": df["index"].astype(int),
        "isCorrect": df.get("isCorrect", False),
        "ast": df["code"].apply(json.loads)
    })


# --------------------------------------------------
# Gold-standard tutor hints
# --------------------------------------------------

def load_gold_hints(gold_csv: str) -> pd.DataFrame:
    df = pd.read_csv(gold_csv)

    # Keep only rows with valid from/to ASTs
    df = df[df["from"].notna() & df["to"].notna()]

    return pd.DataFrame({
        "source": "gold",
        "algorithm": "tutor",
        "assignmentID": df["assignmentID"].astype(str),
        "requestID": df["requestID"].astype(str),
        "hint_index": None,
        "from_ast": df["from"].apply(json.loads),
        "to_ast": df["to"].apply(json.loads),
        "MultipleTutors": df.get("MultipleTutors", True)
    })



# --------------------------------------------------
# Generated hints (CTD / CHF / ITAP etc.)
# --------------------------------------------------

def extract_target_ast(hint_json: dict) -> dict:
    """
    Extract the target AST from an algorithm-generated hint.

    CTD / CHF / ITAP often store ONLY the target AST
    (the whole JSON is the AST).
    """
    # CTD-style: JSON itself is an AST
    if "type" in hint_json and "children" in hint_json:
        return hint_json

    # Other known wrappers
    if "to" in hint_json:
        return hint_json["to"]

    if "toAST" in hint_json:
        return hint_json["toAST"]

    if "hintAST" in hint_json:
        return hint_json["hintAST"]

    raise KeyError(f"Unknown hint JSON format: {hint_json.keys()}")


def load_generated_hints(algorithms_dir: str) -> pd.DataFrame:
    records = []
    algorithms_dir = Path(algorithms_dir)

    for algorithm_dir in algorithms_dir.iterdir():
        if not algorithm_dir.is_dir():
            continue

        algorithm = algorithm_dir.name

        for assignment_dir in algorithm_dir.iterdir():
            if not assignment_dir.is_dir():
                continue

            assignmentID = assignment_dir.name

            for hint_file in assignment_dir.glob("*.json"):
                with open(hint_file, "r") as f:
                    hint_json = json.load(f)

                try:
                    to_ast = extract_target_ast(hint_json)
                except KeyError as e:
                    print(f"Skipping {hint_file}: {e}")
                    continue

                stem = hint_file.stem
                if "_" in stem:
                    requestID, hint_index = stem.split("_", 1)
                    hint_index = int(hint_index)
                else:
                    requestID = stem
                    hint_index = None

                records.append({
                    "source": "generated",
                    "algorithm": algorithm,
                    "assignmentID": assignmentID,
                    "requestID": str(requestID),
                    "hint_index": hint_index,
                    "from_ast": None,        # filled later
                    "to_ast": to_ast,
                    "path": str(hint_file)
                })

    return pd.DataFrame(records)


# --------------------------------------------------
# MAIN PIPELINE
# --------------------------------------------------

def main():
    # File name variables
    grammar_path = "python-grammar.json"
    training_csv = "training.csv"
    requests_csv = "requests.csv"
    gold_csv = "gold-standard.csv"
    algorithms_dir = "algorithms"


    # Load grammer
    grammar = load_python_grammar(grammar_path)
    print(grammar)

    # Load training and requests
    df_training = load_traces(training_csv, type = "training")
    df_requests = load_traces(requests_csv, type = "request")

    # Merge training and requests df
    df_traces = pd.concat([df_training, df_requests], ignore_index = True)


    # Load algorithm hints
    df_generated = load_generated_hints(algorithms_dir)

    # Load gold hints
    df_gold = load_gold_hints(gold_csv)

    # Merge algorithm hints and gold hints
    df_hints = pd.concat([df_generated, df_gold], ignore_index = True)


    # ---- attach request-time AST as from_ast ----
    request_asts = df_traces[df_traces["type"] == "request"][
        ["assignmentID", "traceID", "ast"]
    ].rename(columns={"traceID": "requestID"})

    df_hints = df_hints.merge(
        request_asts,
        on=["assignmentID", "requestID"],
        how="left"
    )

    df_hints["from_ast"] = df_hints["from_ast"].fillna(df_hints["ast"])
    df_hints = df_hints.drop(columns=["ast"])

    # ---- sanity checks ----
    # --- report missing from_ast ---
    missing = df_hints["from_ast"].isna().sum()
    total = len(df_hints)

    print(f"Hints without request AST: {missing} / {total}")

    # --- keep only evaluable hints ---
    df_hints = df_hints[df_hints["from_ast"].notna()].reset_index(drop=True)

    assert df_hints["to_ast"].notna().all(), "Missing to_ast"

    # ---- outputs ----
    print("Unified traces:", df_traces.shape)
    print("Unified hints:", df_hints.shape)
    print("Algorithms:", df_hints["algorithm"].unique())




if __name__ == "__main__":
    main()