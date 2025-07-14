import pandas as pd


def choose_annotation_data(df: pd.DataFrame, filter: pd.DataFrame) -> pd.DataFrame:
    """
    Choose annotation data based on the filter DataFrame.

    Args:
        df (pd.DataFrame): The original DataFrame containing all data.
        filter (pd.DataFrame): The DataFrame containing the filter criteria.

    Returns:
        pd.DataFrame: The filtered DataFrame containing only the selected annotationing data.
    """
    if filter.empty:
        return df
    return df[df["scan_type"].isin(filter["Scan Type"])]


if __name__ == "__main__":

    def test_choose_annotation_data():
        # Sample full data
        data = {
            "scan_type": ["CT", "MRI", "X-Ray", "CT"],
            "patient_id": [1, 2, 3, 4],
            "num_images": [100, 80, 50, 120],
        }
        df = pd.DataFrame(data)

        # Case 1: Empty filter -> returns full df
        empty_filter = pd.DataFrame()
        result = choose_annotation_data(df, empty_filter)
        assert result.equals(df), "Test case 1 failed (empty filter)"

        # Case 2: Filter for 'CT'
        filter_df = pd.DataFrame({"Scan Type": ["CT"]})
        expected = df[df["scan_type"] == "CT"]
        assert result_equals(
            result := choose_annotation_data(df, filter_df), expected
        ), "Test case 2 failed (CT filter)"

        # Case 3: Filter for 'CT' and 'X-Ray'
        filter_df = pd.DataFrame({"Scan Type": ["CT", "X-Ray"]})
        expected = df[df["scan_type"].isin(["CT", "X-Ray"])]
        assert result_equals(
            result := choose_annotation_data(df, filter_df), expected
        ), "Test case 3 failed (CT + X-Ray filter)"

        print("✅ All test cases passed!")

    def result_equals(df1: pd.DataFrame, df2: pd.DataFrame) -> bool:
        return df1.reset_index(drop=True).equals(df2.reset_index(drop=True))

    test_choose_annotation_data()
