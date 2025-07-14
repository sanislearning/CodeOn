def BinarySearch(list1, low, high, key):
    if low > high:
        return False

    middle = (high + low) // 2

    if list1[middle] == key:
        return True
    elif list1[middle] > key:
        return BinarySearch(list1, low, middle - 1, key)
    else:
        return BinarySearch(list1, middle + 1, high, key)


list1 = [1, 2, 3, 4, 10, 5, 23, 89, 10, 100, 33, 40, 12, 35, 15]
list1.sort()
key = int(input("Enter the key to search: "))
gender = input("Enter your gender (male/female/other): ").lower()
if gender == "male":
    print("Hello, Sir!")
elif gender == "female":
    print("Hello, Madam!")
else:
    print("Hello!")
if BinarySearch(list1, 0, len(list1) - 1, key):
    print(f"{key} has been found")
else:
    print("Value not present in list")