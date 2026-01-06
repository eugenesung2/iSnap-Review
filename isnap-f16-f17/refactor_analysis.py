import json
from collections import defaultdict
import pandas as pd


class SnapGrammar:
    """Grammar handler for Snap! abstract syntax trees.

    This class loads a Snap grammar specification and provides utilities for
    mapping AST node types to grammar categories and counting category
    occurrences within an AST.
    """

    def __init__(self, grammar_path):
        """Initialise the Snap grammar.

        Args:
            grammar_path (str): Path to the Snap grammar JSON file
                (e.g. ``snap-grammar.json``).
        """
        with open(grammar_path) as f:
            grammar = json.load(f)

        self.type_to_category = {}
        for category, types in grammar["categories"].items():
            for t in types:
                self.type_to_category[t] = category

    def count_categories(self, ast):
        """Count grammar categories present in an AST.

        Args:
            ast (dict): JSON representation of a Snap! abstract syntax tree.

        Returns:
            dict: Mapping from grammar category name to occurrence count.
        """
        counts = defaultdict(int)

        def visit(node):
            if not isinstance(node, dict):
                return

            node_type = node.get("type")
            category = self.type_to_category.get(node_type)
            if category:
                counts[category] += 1

            for child in node.get("children", {}).values():
                visit(child)

        visit(ast)
        return counts


class TraceExtractor:
    """Extractor for final program states and grammar-based features.

    This class is responsible for:
    - Selecting the final snapshot from each program trace.
    - Converting ASTs into grammar-aware structural features.
    """

    def __init__(self, grammar):
        """Initialise the trace extractor.

        Args:
            grammar (SnapGrammar): Grammar handler used for AST analysis.
        """
        self.grammar = grammar

    def final_snapshots(self, df):
        """Extract the final snapshot from each trace.

        Assumes snapshots are ordered chronologically by the ``index`` column.

        Args:
            df (pandas.DataFrame): Trace-level dataset containing multiple
                snapshots per trace.

        Returns:
            pandas.DataFrame: One row per trace, corresponding to the final
            snapshot.
        """
        return (
            df.sort_values("index")
              .groupby(["assignmentID", "traceID"])
              .tail(1)
              .reset_index(drop=True)
        )

    def extract_features(self, df, state, include_trace=False):
        """Extract grammar-aware features from program states.

        Args:
            df (pandas.DataFrame): DataFrame containing program snapshots.
            state (str): Label indicating the state type (e.g. ``"correct"``,
                ``"request"``).
            include_trace (bool): Whether to include ``traceID`` in the output
                for downstream merging.

        Returns:
            pandas.DataFrame: Grammar feature representation of each program
            state.
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

            if include_trace:
                record["traceID"] = row["traceID"]

            rows.append(record)

        return pd.DataFrame(rows)


class GoldStandard:
    """Handler for gold-standard tutor annotations.

    This class aggregates tutor-authored hints into ambiguity metrics that
    quantify how many valid hints exist for each request and the level of
    tutor agreement.
    """

    def __init__(self, path):
        """Initialise the gold-standard handler.

        Args:
            path (str): Path to ``gold-standard.csv``.
        """
        self.gold = pd.read_csv(path)

    def ambiguity_metrics(self):
        """Compute hint ambiguity metrics per request.

        Returns:
            pandas.DataFrame: One row per request, containing ambiguity
            measures such as number of valid hints and tutor agreement.
        """
        return (
            self.gold
            .groupby(["assignmentID", "requestID"])
            .agg(
                n_gold_hints=("hintID", "count"),
                n_multi_tutor=("MultipleTutors", "sum"),
                n_consensus=("Consensus", "sum"),
            )
            .reset_index()
        )


def main():
    """Run the grammar-aware structural and ambiguity analysis."""
    training = pd.read_csv("training.csv")
    requests = pd.read_csv("requests.csv")

    grammar = SnapGrammar("snap-grammar.json")
    extractor = TraceExtractor(grammar)
    gold = GoldStandard("gold-standard.csv")

    correct_states = extractor.final_snapshots(training)
    request_states = extractor.final_snapshots(requests)

    correct_features = extractor.extract_features(correct_states, "correct")
    request_features = extractor.extract_features(
        request_states, "request", include_trace=True
    )

    comparison_df = pd.concat(
        [correct_features, request_features.drop(columns=["traceID"])],
        ignore_index=True,
    )

    gold_summary = gold.ambiguity_metrics()

    request_with_gold = request_features.merge(
        gold_summary.rename(columns={"requestID": "traceID"}),
        on=["assignmentID", "traceID"],
        how="left",
    )

    print("Request-level structure + ambiguity:")
    print(request_with_gold.head())

    print(
        request_with_gold
        .groupby("n_gold_hints")[["n_COMMAND", "n_REPORTER"]]
        .mean()
    )


if __name__ == "__main__":
    main()