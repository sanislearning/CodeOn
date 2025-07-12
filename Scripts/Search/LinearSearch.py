#Linear Search implementation, it has a time complexity of O(n)
def LinearSearch(list1): 
    key=int(input())
    for i in range(0,len(list1)-1):
        if list1[i]==key:
            print(f"{key} found at index {i}")
            return
    print("Value not found")
    return
    
list1=[1, 2, 3, 4, 10, 5, 23, 89, 10, 100, 33, 40, 12, 35, 15]
LinearSearch(list1)