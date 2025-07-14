def LinearSearch(list1, key):
    list_length = len(list1)
    if not list1:
        return -1
    for i in range(list_length):
        if list1[i] == key:
            return i
    return -1
    
list1=[100, 5, 23, 89, 10, 100, 33, 40, 12, 35, 15, 2, 3, 4, 1, 55, 66, 77, 88, 99, 101, 102, 103, 104]
key=int(input("Enter the key to search: "))
gender = input("Enter your gender (male/female/other): ").lower()
if gender == "male":
    print("Hello, Sir!")
elif gender == "female":
    print("Hello, Madam!")
else:
    print("Hello!")
index = LinearSearch(list1, key)
if index != -1:
    print(f"{key} found at index {index}")
else:
    print("Value not found")