class Node:
    def __init__(self,data):
        self.data=data
        self.next=None
    
class LinkedList:
    def __init__(self):
        self.head=None
        
    def insert(self,data):
        new_node=Node(data)
        if self.head is None:
            self.head=new_node
            return
        current=self.head
        while current.next:
            current=current.next
        current.next=new_node

    def delete(self,key):
        temp=self.head
        if temp and temp.data==key:
            self.head=temp.next
            temp=None
            return
        prev=None
        while temp and temp.data!=key:
            prev=temp
            temp=temp.next
        if not temp:
            print(f"{key} not found in the linked list.")
            return
        prev.next=temp.next
        temp=None

    def update(self,old_value,new_value):
        temp=self.head
        while temp:
            if temp.data==old_value:
                temp.data=new_value
                return
            temp=temp.next
        print(f"{old_value} is not present in the list.")
        
    def display(self):
        temp=self.head
        while temp:
            print(temp.data,end="->")
            temp=temp.next
        print("None")            

def main():
    ll = LinkedList()
    while True:
        print("\nChoose an option:")
        print("1. Insert")
        print("2. Delete")
        print("3. Update")
        print("4. Display")
        print("5. Exit")

        choice = input("Enter your choice (1-5): ")

        if choice == '1':
            data = int(input("Enter value to insert: "))
            ll.insert(data)
        elif choice == '2':
            key = int(input("Enter value to delete: "))
            ll.delete(key)
        elif choice == '3':
            old = int(input("Enter value to update: "))
            new = int(input("Enter new value: "))
            ll.update(old, new)
        elif choice == '4':
            ll.display()
        elif choice == '5':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please enter 1 to 5.")

if __name__=="__main__":
    main()