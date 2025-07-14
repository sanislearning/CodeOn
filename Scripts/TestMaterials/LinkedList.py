class Node:
    """Represents a node in the linked list."""
    def __init__(self,data):
        self.data=data
        self.next=None
    
class LinkedList:
    """Represents a singly linked list."""
    def __init__(self):
        self.head=None
        
    def insert(self,data):
        """Inserts a new node with the given data at the end of the list."""
        new_node=Node(data)
        if self.head is None:
            self.head=new_node
            return
        current=self.head
        while current.next:
            current=current.next
        current.next=new_node

    def delete(self, key):
        """Deletes the first node with the given key from the list."""
        temp = self.head
        if self.head is None:
            print(f"List is empty. Cannot delete {key}.")
            return

        if temp and temp.data == key:
            self.head = temp.next
            return

        prev = None
        while temp and temp.data != key:
            prev = temp
            temp = temp.next

        if not temp:
            print(f"{key} not found in the linked list.")
            return

        prev.next = temp.next

    def update(self,old_value,new_value):
        """Updates the first node with the old value to the new value."""
        temp=self.head
        if self.head is None:
            print(f"List is empty. Cannot update {old_value}.")
            return
        while temp:
            if temp.data==old_value:
                temp.data=new_value
                return
            temp=temp.next
        print(f"{old_value} is not present in the list.")
        
    def display(self):
        """Displays the linked list."""
        temp=self.head
        while temp:
            print(temp.data,end="->")
            temp=temp.next
        print("None")            

def main():
    """Main function to interact with the linked list."""
    ll = LinkedList()
    while True:
        print("\nChoose an option:")
        print("1. Insert")
        print("2. Delete")
        print("3. Update")
        print("4. Display")
        print("5. Exit")

        choice = input("Enter your choice (1-5): ")

        match choice:
            case '1':
                data = int(input("Enter value to insert: "))
                ll.insert(data)
            case '2':
                key = int(input("Enter value to delete: "))
                ll.delete(key)
            case '3':
                old = int(input("Enter value to update: "))
                new = int(input("Enter new value: "))
                ll.update(old, new)
            case '4':
                ll.display()
            case '5':
                print("Exiting...")
                break
            case _:
                print("Invalid choice. Please enter 1 to 5.")

if __name__=="__main__":
    main()