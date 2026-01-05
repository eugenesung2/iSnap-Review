import pandas as pd


def normalise_assignment_id(value: str):
    if pd.isna(value):
        return value

    value = str(value)

    # If there is a prefix, keep only the part after the first dot
    if "." in value:
        return value.split(".", 1)[1]

    # Otherwise, already a valid assignment ID
    return value


def load_files() -> dict[str, pd.DataFrame]:
    data = {}

    # Main table containing student actions
    data["main"] = pd.read_csv("MainTable.csv", low_memory=False)

    # Objectives for homeworks
    data["guess2HW"] = pd.read_csv("grades/guess2HW.csv")
    data["squiralHW"] = pd.read_csv("grades/squiralHW.csv")

    # Objectives for labs
    data["guess1Lab"] = pd.read_csv("grades/guess1Lab.csv")
    data["guess3Lab"] = pd.read_csv("grades/guess3Lab.csv")
    data["polygonMakerLab"] = pd.read_csv("grades/polygonMakerLab.csv")

    # Grades for associated labs or homeworks
    data["student_assignment"] = pd.read_csv("LinkTables/AssignmentSubject.csv")

    # Code states
    data["code_states"] = pd.read_csv("CodeStates/CodeStates.csv")

    # Normalise SubjectID from student_assignment dataframe
    data["student_assignment"]["SubjectID"] = (data["student_assignment"]["SubjectID"].apply(normalise_assignment_id))

    return data



def main():
    # Load related CSV files into data frame
    data = load_files()

    main_df = data["main"]
    student_assignment_df = data["student_assignment"]

    print(main_df.info())

    # Flag hint events
    main_df["is_hint_event"] = main_df["X-HintData"].notna()

    student_hint_usage = (main_df.groupby("SubjectID")
                          .agg(used_hint=("is_hint_event", "any"))
                          .reset_index())
    
    summary = (student_hint_usage.groupby("used_hint")
               .size()
               .reset_index(name="n_students"))

    print(summary)

if __name__ == "__main__":
    main()