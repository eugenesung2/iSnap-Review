import pandas as pd
import json
from collections import defaultdict


class SnapGrammar:
    """
    Handles grammar-aware analysis of Snap! ASTs.

    Responsibilities:
    - Load the Snap grammar definition
    - Map AST node types to grammar categories
    - Count grammar categories within an AST
    """

    def __init__(self, grammar_path):
        """
        Initialise the grammar by loading the grammar specification.

        Parameters
        ----------
        grammar_path : str
            Path to snap-grammar.json
        """
        with open(grammar_path) as f:
            grammar = json.load(f)

        # Map each node type to its corresponding grammar category
        self.type_to_category = {}
        for category, types in grammar["categories"].items():
            for t in types:
                self.type_to_category[t] = category

    def count_categories(self, ast):
        """
        Count grammar categories present in an AST.

        Parameters
        ----------
        ast : dict
            JSON representation of a Snap! abstract syntax tree

        Returns
        -------
        dict
            Mapping from grammar category to frequency
        """
        counts = defaultdict(int)

        def visit(node):
            # Ignore malformed or non-dictionary nodes
            if not isinstance(node, dict):
                return

            node_type = node.get("type")
            category = self.type_to_category.get(node_type)

            # Increment category count if applicable
            if category:
                counts[category] += 1

            # Recursively visit child nodes
            for child in node.get("children", {}).values():
                visit(child)

        visit(ast)
        return counts


class TraceExtractor:
    """
    Extracts final program states from traces and computes
    grammar-aware features for each state.
    """

    def __init__(self, grammar: SnapGrammar):
        """
        Parameters
        ----------
        grammar : SnapGrammar
            Grammar handler used for AST analysis
        """
        self.grammar = grammar

    def final_snapshots(self, df):
        """
        Select the final snapshot for each trace.

        Assumes snapshots are indexed chronologically by 'index'.

        Parameters
        ----------
        df : pandas.DataFrame
            Trace-level dataset (training or requests)

        Returns
        -------
        pandas.DataFrame
            One row per trace, corresponding to the final snapshot
        """
        return (
            df.sort_values("index")
              .groupby(["assignmentID", "traceID"])
              .tail(1)
              .reset_index(drop=True)
        )

    def extract_features(self, df, state, include_trace=False):
        """
        Extract grammar-based features from a set of program states.

        Parameters
        ----------
        df : pandas.DataFrame
            DataFrame containing program snapshots
        state : str
            Label indicating the state type (e.g. 'correct', 'request')
        include_trace : bool
            Whether to retain traceID for downstream merging

        Returns
        -------
        pandas.DataFrame
            Grammar feature representation of each program state
        """
        rows = []

        for _, row in df.iterrows():
            ast = json.loads(row["code"])
            counts = self.grammar.count_categories(ast)

            record = {
                "assignmentID": row["assignmentID"],
                "state": state,
                "n_COMMAND": counts.get("COMMAND", 0),
                "n_REPORTER": counts.get("REPORTER", 0),
                "n_HAT": counts.get("HAT", 0),
                "n_BOOLEAN": counts.get("BOOLEAN", 0),
            }

            # Preserve traceID when analysing request-level ambiguity
            if include_trace:
                record["traceID"] = row["traceID"]

            rows.append(record)

        return pd.DataFrame(rows)


class GoldStandard:
    """
    Handles gold-standard tutor annotations and computes
    hint ambiguity metrics.
    """

    def __init__(self, path):
        """
        Parameters
        ----------
        path : str
            Path to gold-standard.csv
        """
        self.gold = pd.read_csv(path)

    def ambiguity_metrics(self):
        """
        Aggregate gold-standard hints into ambiguity measures.

        Returns
        -------
        pandas.DataFrame
            One row per request, containing ambiguity metrics
        """
        return (
            self.gold
            .groupby(["assignmentID", "requestID"])
            .agg(
                n_gold_hints=("hintID", "count"),
                n_multi_tutor=("MultipleTutors", "sum"),
                n_consensus=("Consensus", "sum")
            )
            .reset_index()
        )


# -------------------------
# Main analysis pipeline
# -------------------------

# Load raw datasets
training = pd.read_csv("training.csv")
requests = pd.read_csv("requests.csv")

# Initialise core components
grammar = SnapGrammar("snap-grammar.json")
extractor = TraceExtractor(grammar)
gold = GoldStandard("gold-standard.csv")

# Extract final states from training (correct solutions)
correct_states = extractor.final_snapshots(training)

# Extract final states from request traces (actual hint requests)
request_states = extractor.final_snapshots(requests)

# Compute grammar-aware features
correct_features = extractor.extract_features(correct_states, "correct")
request_features = extractor.extract_features(
    request_states, "request", include_trace=True
)

# Combine correct and request states for structural comparison
comparison_df = pd.concat(
    [correct_features, request_features.drop(columns=["traceID"])],
    ignore_index=True
)

# Compute gold-standard ambiguity metrics
gold_summary = gold.ambiguity_metrics()

# Merge ambiguity metrics onto request-level features
# NOTE: traceID in requests corresponds one-to-one with requestID
#       in gold-standard annotations (verified empirically)
request_with_gold = request_features.merge(
    gold_summary.rename(columns={"requestID": "traceID"}),
    on=["assignmentID", "traceID"],
    how="left"
)

print("Request-level structure + ambiguity:")
print(request_with_gold.head())

print(
    request_with_gold
    .groupby("n_gold_hints")[["n_COMMAND", "n_REPORTER"]]
    .mean()
)
