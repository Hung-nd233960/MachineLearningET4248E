from typing import List
from statistics import mean, median, mode, StatisticsError
from collections import Counter


def reconcilate(data_list: List[int], strategy: str = "mean") -> int:
    """
    Reconciles a list of integer slice indices using the specified strategy.

    Supported strategies:
        - "mean": average and round to nearest int
        - "median": middle value (rounded if float)
        - "mode": most common value (returns lowest if multiple)
        - "majority": like mode, but returns -1 if no majority

    Returns:
        An integer index representing the reconciled value.
    """
    if not data_list:
        raise ValueError("data_list must not be empty")

    if strategy == "mean":
        return int(round(mean(data_list)))

    elif strategy == "median":
        return int(round(median(data_list)))

    elif strategy == "mode":
        try:
            return mode(data_list)
        except StatisticsError:
            # multiple modes: choose the smallest
            count = Counter(data_list)
            most_common = count.most_common()
            max_count = most_common[0][1]
            candidates = [k for k, v in most_common if v == max_count]
            return min(candidates)

    elif strategy == "majority":
        count = Counter(data_list)
        most_common = count.most_common(1)[0]
        if most_common[1] > len(data_list) // 2:
            return most_common[0]
        return -1  # no majority
    else:
        raise ValueError(f"Unknown strategy '{strategy}'")


if __name__ == "__main__":
    # Example usage
    data = [1, 2, 2, 3, 4]
    print("Mean:", reconcilate(data, "mean"))
    print("Median:", reconcilate(data, "median"))
    print("Mode:", reconcilate(data, "mode"))
    print("Majority:", reconcilate(data, "majority"))

    # Test with empty list
    try:
        print(reconcilate([], "mean"))
    except ValueError as e:
        print(e)
