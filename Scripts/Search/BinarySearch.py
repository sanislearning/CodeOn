#Implementation of Binary Search. Has constant time O(n)
#Requires a sorted array

def BinarySearch(list1,low,high,key):
    middle=(high+low)//2
    if low>high:       #checks if search space is invalid
        print("Value not present in list")
        return
    elif list1[middle]==key:
        print(f"{key} has been found")
        return
    elif list1[middle]>key:
        high=middle-1
        BinarySearch(list1,low,high,key)
    elif list1[middle]<key:
        low=middle+1
        BinarySearch(list1,low,high,key)
        
    
list1=[1, 2, 3, 4, 10, 5, 23, 89, 10, 100, 33, 40, 12, 35, 15]
list1.sort() #sorts the list
key=int(input())
BinarySearch(list1,0,len(list1)-1,key)