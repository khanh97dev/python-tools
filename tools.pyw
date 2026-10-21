import tkinter as tk
from tkinter import messagebox
import inspect
import os

# Define functions for each button
def option_1kill_riot():
    try:
        os.system("taskkill /F /IM RiotClientServices.exe")  # Force kill Riot Client process
        messagebox.showinfo("Option 1", "Riot Client has been terminated.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to terminate Riot Client: {e}")

def option_2():
    messagebox.showinfo("Option 2", "You selected Option 2")
def option_3():
    messagebox.showinfo("Option 3", "You selected Option 3")
def option_4():
    messagebox.showinfo("Option 4", "You selected Option 4")
def option_off():
    try:
        os.system("shutdown /s /t 0")  # Shutdown the system immediately
        messagebox.showinfo("Shutdown", "The system is shutting down.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to shutdown the system: {e}")

# Create the main window
root = tk.Tk()
root.title("Choice Popup")

# Set the window size
window_width = 120
window_height = 180
root.geometry(f"{window_width}x{window_height}")

# Position the window in the top-right corner
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x_position = screen_width - window_width - 10  # 10px margin from the right
y_position = 10  # 10px margin from the top
root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

# Make the window always on top
root.attributes("-topmost", True)

# Add a label
label = tk.Label(root, text="Please select an option:")
label.pack(pady=5)

# Automatically detect all option_* functions
functions = [
    (name.replace("option_", "").capitalize(), func)  # Remove "option_" from the function name
    for name, func in inspect.getmembers(__import__(__name__), inspect.isfunction)
    if name.startswith("option_")
]

# Create buttons dynamically for each function and bind keys
key_shortcuts = {}  # Dictionary to store key bindings
for i, (name, func) in enumerate(functions, start=1):
    def create_command(func_name, func):
        return lambda: [label.config(text=f"Selected: {func_name}"), func()]

    # Create a button for the function
    button = tk.Button(root, text=name, command=create_command(name, func), width=6, height=1)  # Extra small button size
    button.pack(pady=1)  # Minimal padding for compact layout

    # Assign a key shortcut (1, 2, 3, etc.)
    key_shortcuts[str(i)] = func

# Function to handle key presses
def on_key_press(event):
    key = event.char
    if key in key_shortcuts:
        func = key_shortcuts[key]
        label.config(text=f"Selected: {key}")  # Update label with the key pressed
        func()  # Call the corresponding function

# Bind the key press event to the on_key_press function
root.bind("<KeyPress>", on_key_press)

# Run the GUI event loop
root.mainloop()
