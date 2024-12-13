import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

class BuddySystem:
    def __init__(self, total_memory):
        self.total_memory = total_memory
        self.memory = {total_memory: [(0, total_memory)]}  # Dictionary: size -> list of free blocks
        self.allocated = {}  # Dictionary to track allocated blocks: address -> (requested size, block size)

    def allocate(self, size):
        block_size = self._find_nearest_power_of_two(size)

        while block_size <= self.total_memory:
            if block_size in self.memory and self.memory[block_size]:
                # Allocate the first available block of the required size
                block = self.memory[block_size].pop(0)
                self.allocated[block[0]] = (size, block_size)  # Store requested and actual block sizes
                return block

            # If no block is available, attempt to split larger blocks
            if not self._split_block(block_size):
                break

        return None

    def deallocate(self, block):
        size = block[1] - block[0]  # Actual block size
        self.memory.setdefault(size, []).append(block)
        if block[0] in self.allocated:
            del self.allocated[block[0]]  # Remove from allocated blocks
        self._merge_buddies(size, block)

    def _find_nearest_power_of_two(self, size):
        power = 1
        while power < size:
            power *= 2
        return power

    def _split_block(self, size):
        larger_size = size * 2
        while larger_size <= self.total_memory:
            if larger_size in self.memory and self.memory[larger_size]:
                # Split a larger block into two smaller buddies
                block = self.memory[larger_size].pop(0)
                mid = (block[0] + block[1]) // 2
                smaller_size = larger_size // 2
                self.memory.setdefault(smaller_size, []).append((block[0], mid))
                self.memory[smaller_size].append((mid, block[1]))
                return True
            larger_size *= 2
        return False

    def _merge_buddies(self, size, block):
        buddy_address = block[0] ^ size  # XOR to find buddy address
        buddy = (buddy_address, buddy_address + size)

        if buddy in self.memory.get(size, []):
            self.memory[size].remove(buddy)
            self.memory[size].remove(block)
            merged_block = (min(block[0], buddy[0]), max(block[1], buddy[1]))
            self.memory.setdefault(size * 2, []).append(merged_block)
            self._merge_buddies(size * 2, merged_block)

    def _ensure_memory_keys(self):
        sizes = [2**i for i in range(self.total_memory.bit_length())]
        for size in sizes:
            if size not in self.memory:
                self.memory[size] = []

class BuddySystemGUI:
    def __init__(self, root, buddy_system):
        self.buddy_system = buddy_system

        # Configure the main window
        root.title("Buddy System Memory Management")
        root.geometry("1200x700")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=("Helvetica", 10))
        style.configure("Treeview.Heading", font=("Helvetica", 12, "bold"))

        # Title Label
        title_label = ttk.Label(
            root,
            text="Buddy System Memory Management",
            font=("Helvetica", 16, "bold"),
            anchor="center",
            foreground="darkblue",
        )
        title_label.pack(pady=10)

        # Main Frame
        main_frame = ttk.Frame(root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Free Blocks Section
        free_blocks_label = ttk.Label(main_frame, text="Free Memory Blocks", font=("Helvetica", 12, "bold"))
        free_blocks_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.free_blocks_tree = ttk.Treeview(
            main_frame, columns=("Address", "Size"), show="headings", height=10
        )
        self.free_blocks_tree.heading("Address", text="Address")
        self.free_blocks_tree.heading("Size", text="Size (KB)")
        self.free_blocks_tree.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        # Allocated Blocks Section
        allocated_blocks_label = ttk.Label(
            main_frame, text="Allocated Memory Blocks", font=("Helvetica", 12, "bold")
        )
        allocated_blocks_label.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.allocated_blocks_tree = ttk.Treeview(
            main_frame, columns=("Address", "Requested Size", "Block Size"), show="headings", height=10
        )
        self.allocated_blocks_tree.heading("Address", text="Address")
        self.allocated_blocks_tree.heading("Requested Size", text="Requested Size (KB)")
        self.allocated_blocks_tree.heading("Block Size", text="Block Size (KB)")
        self.allocated_blocks_tree.grid(row=1, column=1, padx=10, pady=5, sticky="nsew")

        # Memory Visualization Section
        memory_label = ttk.Label(main_frame, text="Memory Visualization", font=("Helvetica", 12, "bold"))
        memory_label.grid(row=2, column=0, columnspan=2, pady=5)
        self.canvas = tk.Canvas(main_frame, height=200, bg="white")
        self.canvas.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")

        # Controls Section
        controls_frame = ttk.Frame(root, padding=10)
        controls_frame.pack(fill=tk.X)

        self.allocate_label = ttk.Label(controls_frame, text="Allocate Size (KB):", font=("Helvetica", 10))
        self.allocate_label.pack(side=tk.LEFT, padx=5)
        self.allocate_entry = ttk.Entry(controls_frame, width=10)
        self.allocate_entry.pack(side=tk.LEFT, padx=5)

        self.allocate_button = ttk.Button(controls_frame, text="Allocate", command=self.allocate_block)
        self.allocate_button.pack(side=tk.LEFT, padx=5)

        self.deallocate_label = ttk.Label(controls_frame, text="Deallocate Address:", font=("Helvetica", 10))
        self.deallocate_label.pack(side=tk.LEFT, padx=5)
        self.deallocate_entry = ttk.Entry(controls_frame, width=10)
        self.deallocate_entry.pack(side=tk.LEFT, padx=5)

        self.deallocate_button = ttk.Button(controls_frame, text="Deallocate", command=self.deallocate_block)
        self.deallocate_button.pack(side=tk.LEFT, padx=5)

        # Update the GUI views
        self.update_view()

    def allocate_block(self):
        try:
            size = int(self.allocate_entry.get())
            block = self.buddy_system.allocate(size)
            if block:
                messagebox.showinfo(
                    "Success",
                    f"Allocated {size} KB at address {block[0]} (Block Size: {self.buddy_system.allocated[block[0]][1]} KB)",
                )
            else:
                messagebox.showwarning("Failure", "Allocation failed. Not enough memory.")
        except ValueError:
            messagebox.showerror("Error", "Invalid input for allocation size.")
        self.update_view()

    def deallocate_block(self):
        try:
            address = int(self.deallocate_entry.get())
            if address in self.buddy_system.allocated:
                size = self.buddy_system.allocated[address][1]  # Actual block size
                block = (address, address + size)
                self.buddy_system.deallocate(block)
                messagebox.showinfo("Success", f"Deallocated block at address {address}")
            else:
                messagebox.showwarning("Failure", "Invalid address or block not allocated.")
        except ValueError:
            messagebox.showerror("Error", "Invalid input for deallocation address.")
        self.update_view()

    def update_view(self):
        # Update free blocks
        for row in self.free_blocks_tree.get_children():
            self.free_blocks_tree.delete(row)
        for size, blocks in self.buddy_system.memory.items():
            for block in blocks:
                self.free_blocks_tree.insert("", "end", values=(block[0], size))

        # Update allocated blocks
        for row in self.allocated_blocks_tree.get_children():
            self.allocated_blocks_tree.delete(row)
        for address, (requested_size, block_size) in self.buddy_system.allocated.items():
            self.allocated_blocks_tree.insert("", "end", values=(address, requested_size, block_size))

        # Update memory visualization
        self.canvas.delete("all")
        total_width = self.canvas.winfo_width()
        unit_width = total_width / self.buddy_system.total_memory

        # Draw free blocks
        for size, blocks in self.buddy_system.memory.items():
            for block in blocks:
                x1 = block[0] * unit_width
                x2 = block[1] * unit_width
                self.canvas.create_rectangle(x1, 10, x2, 50, fill="green", outline="black", tags="free")
                self.canvas.create_text((x1 + x2) / 2, 30, text=f"{size} KB", fill="black", tags="free")

        # Draw allocated blocks
        for address, (requested_size, block_size) in self.buddy_system.allocated.items():
            x1 = address * unit_width
            x2 = (address + block_size) * unit_width
            self.canvas.create_rectangle(x1, 60, x2, 100, fill="red", outline="black", tags="allocated")
            self.canvas.create_text((x1 + x2) / 2, 80, text=f"{requested_size} KB", fill="black", tags="allocated")

# Example Usage
if __name__ == "__main__":
    total_memory = 1024  # 1 MB
    buddy_system = BuddySystem(total_memory)
    buddy_system._ensure_memory_keys()

    root = tk.Tk()
    gui = BuddySystemGUI(root, buddy_system)
    root.mainloop()
 