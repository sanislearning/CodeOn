def BinarySearch(list1, low, high, key):
    """Performs a binary search on a sorted list.

    Args:
        list1: The sorted list to search.
        low: The starting index of the search range.
        high: The ending index of the search range.
        key: The value to search for.

    Returns:
        The index of the key if found, otherwise -1.
    """
    if low > high:
        return -1

    middle = (high + low) // 2

    if list1[middle] == key:
        return middle
    elif list1[middle] > key:
        return BinarySearch(list1, low, middle - 1, key)
    else:
        return BinarySearch(list1, middle + 1, high, key)


if __name__ == "__main__":
    list1 = [1, 2, 3, 4, 10, 5, 23, 89, 10, 100, 33, 40, 12, 35, 15]
    list1.sort()
    key = int(input("Enter the key to search: "))
    print("Hello!")

    index = BinarySearch(list1, 0, len(list1) - 1, key)
    if index != -1:
        print(f"{key} has been found at index {index}")
    else:
        print("Value not present in list")