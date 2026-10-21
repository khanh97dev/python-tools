import tkinter as tk
from tkinter import messagebox, ttk
import feedparser
import webbrowser
import threading
import re # Added for better keyword matching

try:
    from deep_translator import GoogleTranslator
except ImportError:
    messagebox.showerror("Error", "Please install 'deep-translator':\n\npip install deep-translator")
    exit()

# --------------------------
# CONFIGURATION
# --------------------------
RSS_FEEDS = {
    "BBC": "https://feeds.bbci.co.uk/news/rss.xml",
    "CNN": "http://rss.cnn.com/rss/edition.rss",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml"
}
REFRESH_INTERVAL = 600000  # 10 minutes
FONT_TEXT = ("Segoe UI", 10)
global_articles = []

# --- NEW: Topic Keywords for Categorization (Fast & Local) ---
TOPIC_KEYWORDS = {
    "CRYPTO": ["crypto", "bitcoin", "ethereum", "blockchain", "NFT", "dogecoin", "coinbase", "tether", "defi"],
    "POLITICS": ["election", "parliament", "congress", "senate", "president", "prime minister", "government", "war", "vote", "geopolitics", "diplomacy", "sanctions", "bill", "treaty"],
    "BUSINESS": ["market", "stocks", "economy", "investment", "shares", "finance", "bank", "CEO", "merger", "acquisition", "GDP", "inflation", "recession", "trade"],
    "TECHNOLOGY": ["AI", "tech", "software", "google", "apple", "meta", "robotics", "cybersecurity", "innovation", "startup", "5G", "semiconductor", "quantum"]
}
DEFAULT_TOPIC = "GENERAL"

# --------------------------
# UTILITY FUNCTIONS (Optimization)
# --------------------------

def update_status(msg):
    """Update status message in the Listbox."""
    news_list.delete(0, tk.END)
    news_list.insert(tk.END, msg)


def translate_batch_safe(titles):
    """Batch-translate all titles efficiently with fallback. (Existing Optimization)"""
    try:
        # Re-using the efficient batch translation
        translator = GoogleTranslator(source="en", target="vi")
        return translator.translate_batch(titles)
    except Exception as e:
        print(f"[Batch Translation Error] {e}")
        # fallback: return original
        return titles

# --- NEW: Categorization Function ---
def categorize_article(title_en):
    """Classify an article based on keyword matching in the English title."""
    title_lower = title_en.lower()

    # Simple, fast keyword matching
    for topic, keywords in TOPIC_KEYWORDS.items():
        # Use regex word boundaries (\b) for more accurate matching (e.g., 'coin' doesn't match 'coinbase')
        if any(re.search(r'\b' + re.escape(k) + r'\b', title_lower) for k in keywords):
            return topic

    return DEFAULT_TOPIC

# --------------------------
# CORE LOGIC
# --------------------------

def fetch_and_translate(selected_sources, limit):
    """Fetch RSS feeds, categorize, and translate titles quickly."""
    global global_articles
    headlines = []

    root.after(0, lambda: update_status("📰 Fetching headlines..."))
    for source in selected_sources:
        url = RSS_FEEDS[source]
        feed = feedparser.parse(url)
        for entry in feed.entries[:limit]:
            title = entry.get("title", "")
            link = entry.get("link", "")
            if title:
                # Store source now
                headlines.append({"title": title, "link": link, "source": source})

    if not headlines:
        root.after(0, lambda: update_status("⚠️ No headlines found."))
        return

    # --- NEW: Categorization BEFORE Translation (Optional but logical) ---
    root.after(0, lambda: update_status(f"🏷️ Categorizing {len(headlines)} headlines..."))
    for h in headlines:
        h["topic"] = categorize_article(h["title"])

    root.after(0, lambda: update_status(f"🌐 Translating {len(headlines)} headlines..."))

    # Batch translate (Existing Optimization)
    titles_en = [h["title"] for h in headlines]
    titles_vi = translate_batch_safe(titles_en)

    translated_articles = [
        {
            "en": h["title"],
            "vi": vi,
            "link": h["link"],
            "source": h["source"],
            "topic": h["topic"] # Add the topic
        }
        for h, vi in zip(headlines, titles_vi)
    ]

    global_articles = translated_articles
    root.after(0, update_news_list)

def update_news_list():
    """Display categorized and translated news."""
    global global_articles
    news_list.delete(0, tk.END)

    # NOTE: Listbox does NOT support tags, nor does it support 'font'
    # for individual items. We use itemconfig with only 'bg' and 'fg'.
    # news_list.tag_config('topic_header', background='#fff0d9', foreground='#663300') # <-- REMOVED (Listbox Error)
    # news_list.tag_config('source_header', background='#d9eaff', foreground='#003366') # <-- REMOVED (Listbox Error)

    if not global_articles:
        news_list.insert(tk.END, "⚠️ No articles found or failed to fetch.")
        return

    # --- Group by Topic first, then by Source ---
    grouped_by_topic = {}
    for a in global_articles:
        # Assuming 'TOPIC_KEYWORDS' and 'DEFAULT_TOPIC' are defined globally
        grouped_by_topic.setdefault(a["topic"], []).append(a)

    # Define a custom order for topics (assuming TOPIC_KEYWORDS is available)
    topic_order = list(TOPIC_KEYWORDS.keys()) + [DEFAULT_TOPIC]

    for topic in topic_order:
        items = grouped_by_topic.get(topic)
        if items:
            # 1. Topic Header
            news_list.insert(tk.END, "")
            news_list.insert(tk.END, f"✨ {topic} ARTICLES:")

            # --- FIX: Use itemconfig on tk.END with only supported options (bg, fg) ---
            news_list.itemconfig(tk.END, {'bg': '#fff0d9', 'fg': '#663300'})

            # Group items by source within the topic
            grouped_by_source = {}
            for a in items:
                grouped_by_source.setdefault(a["source"], []).append(a)

            for source, articles_in_source in grouped_by_source.items():
                # 2. Source Header
                news_list.insert(tk.END, f"  📰 {source.upper()} ({len(articles_in_source)} articles):")

                # --- FIX: Use itemconfig on tk.END with only supported options (bg, fg) ---
                news_list.itemconfig(tk.END, {'bg': '#d9eaff', 'fg': '#003366'})

                news_list.insert(tk.END, "-" * 80)

                for a in articles_in_source:
                    news_list.insert(tk.END, f"  EN: {a['en']}")
                    news_list.insert(tk.END, f"  VI: {a['vi']}")
                    news_list.insert(tk.END, f"  🔗 {a['link']}")
                    news_list.insert(tk.END, "")

    # Assuming REFRESH_INTERVAL and display_news are defined globally
    root.after(REFRESH_INTERVAL, display_news)

def display_news():
    """Triggered when user clicks Fetch button."""
    selected_sources = [s for s, v in source_vars.items() if v.get() == 1]
    if not selected_sources:
        messagebox.showwarning("Warning", "Please select at least one news source!")
        return

    try:
        limit = int(limit_entry.get())
        if not (1 <= limit <= 10):
            raise ValueError
    except ValueError:
        messagebox.showerror("Invalid Input", "Limit must be an integer between 1–10.")
        return

    update_status("⏳ Fetching, categorizing & translating news...")
    # Using a thread to prevent GUI freeze during I/O (fetching) and CPU-bound work (translation/categorization)
    threading.Thread(target=fetch_and_translate, args=(selected_sources, limit), daemon=True).start()


def on_double_click(event):
    """Handle double-click to open links or search."""
    idx = news_list.curselection()
    if not idx:
        return
    text = news_list.get(idx[0]).strip() # Use strip() to clean up leading/trailing spaces

    if text.startswith("🔗"):
        link = text[2:].strip()
        webbrowser.open(link)
    elif text.startswith("EN:") or text.startswith("VI:"):
        # Use the raw headline for a better search query
        query = text[3:].strip()
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(url)


# --------------------------
# GUI SETUP
# --------------------------
root = tk.Tk()
root.title("🗞️ News Aggregator & Translator (Categorized)")
root.geometry("1000x750") # Slightly wider/taller for better display

# Use a better style for modern look
style = ttk.Style()
style.theme_use('clam')

# --- Source Selection ---
source_frame = ttk.LabelFrame(root, text="Select News Sources", padding=(10, 5))
source_frame.pack(padx=10, pady=5, fill="x")

source_vars = {}
for src in RSS_FEEDS.keys():
    var = tk.IntVar(value=1)
    chk = ttk.Checkbutton(source_frame, text=src, variable=var)
    chk.pack(side=tk.LEFT, padx=8)
    source_vars[src] = var

# --- Limit Input & Pin Option ---
control_frame = ttk.Frame(root)
control_frame.pack(pady=10)

limit_label = ttk.Label(control_frame, text="Articles per source (1–10):")
limit_label.pack(side=tk.LEFT, padx=5)
limit_entry = ttk.Entry(control_frame, width=5)
limit_entry.insert(0, "10")
limit_entry.pack(side=tk.LEFT, padx=10)

fetch_btn = ttk.Button(control_frame, text="🔄 Fetch & Categorize News", command=display_news)
fetch_btn.pack(side=tk.LEFT, padx=15) # Increased padding

# 📌 Pin-on-top checkbox
pin_var = tk.IntVar(value=0)
def toggle_pin():
    root.wm_attributes("-topmost", bool(pin_var.get()))

pin_check = ttk.Checkbutton(control_frame, text="📌 Pin on Top", variable=pin_var, command=toggle_pin)
pin_check.pack(side=tk.LEFT, padx=10)

# --- News Display ---
display_frame = ttk.Frame(root)
display_frame.pack(padx=10, pady=5, fill="both", expand=True)

# Using Listbox/Scrollbar setup from original, but allowing for expansion
news_list = tk.Listbox(display_frame, font=FONT_TEXT, bg="#ffffff", selectmode=tk.SINGLE)
news_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scrollbar = ttk.Scrollbar(display_frame, orient=tk.VERTICAL, command=news_list.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
news_list.config(yscrollcommand=scrollbar.set)
news_list.bind("<Double-1>", on_double_click)

# Initial load
display_news()

root.mainloop()
