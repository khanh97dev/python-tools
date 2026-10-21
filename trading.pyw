import requests
import time
import tkinter as tk
from threading import Thread
import os
import psutil

# --------------------------
# CONFIG
# --------------------------
BASE_URL = "https://api.binance.com/api/v3/klines"
INTERVAL = "1s"           # Binance candlestick interval
INTERVAL_FETCH = 1        # Refresh every 1 second
SAVE_FILE = "symbols.txt" # File to save coin list

session = requests.Session()  # Keep connection persistent for efficiency


# --------------------------
# Fetch Binance Open Price
# --------------------------
def fetch_open_price(symbol):
    try:
        params = {
            "symbol": symbol,
            "interval": INTERVAL,
            "limit": 1
        }
        response = session.get(BASE_URL, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][1])
        return None
    except Exception as e:
        return f"Error: {e}"


# --------------------------
# GUI Setup
# --------------------------
def start_gui():
    def update_data():
        while True:
            for symbol, label in symbol_labels.items():
                open_price = fetch_open_price(symbol)
                if isinstance(open_price, str) and "Error" in open_price:
                    label.config(text=f"{symbol}: {open_price}")
                else:
                    label.config(text=f"{symbol}: {open_price}")
            time.sleep(INTERVAL_FETCH)

    def update_ram():
        process = psutil.Process(os.getpid())
        while True:
            mem_mb = process.memory_info().rss / (1024 * 1024)
            ram_label.config(text=f"RAM: {mem_mb:.1f} MB")
            time.sleep(5)

    def set_symbols(save=True):
        text = entry.get().strip()
        coins = [c.strip().upper() for c in text.split(",") if c.strip()]
        symbols = [f"{coin}USDT" for coin in coins]

        # Clear old labels
        for lbl in symbol_labels.values():
            lbl.destroy()
        symbol_labels.clear()

        # Create new labels
        for symbol in symbols:
            label = tk.Label(root, text=f"{symbol}: Fetching...", font=("Arial", 9))
            label.pack(anchor="w", padx=5, pady=2)
            symbol_labels[symbol] = label

        # Save symbols
        if save:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                f.write(text)

    def load_symbols():
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
        return "BTC,ETH"  # default

    def toggle_pin_top():
        root.attributes("-topmost", pin_var.get())

    # --------------------------
    # Main Window
    # --------------------------
    root = tk.Tk()
    root.title("Crypto Prices Monitor")

    # Input frame
    frame = tk.Frame(root)
    frame.pack(anchor="w", padx=5, pady=5)

    tk.Label(frame, text="Symbols (comma):", font=("Arial", 9)).pack(side="left")
    entry = tk.Entry(frame, width=25)
    entry.insert(0, load_symbols())
    entry.pack(side="left", padx=5)

    tk.Button(frame, text="Set", command=set_symbols).pack(side="left")
    entry.bind("<Return>", lambda event: set_symbols())

    # Pin top checkbox
    pin_var = tk.BooleanVar(value=True)
    pin_checkbox = tk.Checkbutton(root, text="Pin Top", variable=pin_var, command=toggle_pin_top, font=("Arial", 8))
    pin_checkbox.pack(anchor="w", padx=5, pady=(0, 3))
    root.attributes("-topmost", True)  # default on top

    # RAM label
    ram_label = tk.Label(root, text="RAM: 0 MB", font=("Arial", 8), fg="gray")
    ram_label.pack(anchor="w", padx=5, pady=(0, 5))

    # Symbol labels container
    symbol_labels = {}

    # Load saved symbols initially
    set_symbols(save=False)

    # --------------------------
    # Background Threads
    # --------------------------
    Thread(target=update_data, daemon=True).start()
    Thread(target=update_ram, daemon=True).start()

    # Window position (top-right)
    screen_width = root.winfo_screenwidth()
    root.geometry(f"260x240+{screen_width - 280}+0")

    root.mainloop()


# --------------------------
# Entry Point
# --------------------------
if __name__ == "__main__":
    start_gui()
