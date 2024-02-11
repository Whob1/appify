import tkinter as tk
from tkinter import scrolledtext
from threading import Thread
import asyncio
from crawler import Crawler  # Make sure the Crawler class is correctly implemented in crawler.py

def update_progress(message):
    if progress_text:
        progress_text.insert(tk.END, f"{message}\n")
        progress_text.yview(tk.END)

def start_crawler():
    global crawler
    if not crawler:
        crawler = Crawler(update_callback=update_progress)
    if not crawler.is_running:
        Thread(target=lambda: asyncio.run(crawler.start()), daemon=True).start()

def stop_crawler():
    if crawler and crawler.is_running:
        asyncio.run_coroutine_threadsafe(crawler.stop(), asyncio.get_event_loop())

def add_domain():
    domain = domain_entry.get()
    if crawler and domain:
        asyncio.run_coroutine_threadsafe(crawler.add_domain(domain), asyncio.get_event_loop())
        domain_entry.delete(0, tk.END)

crawler = None

root = tk.Tk()
root.title("Web Crawler Monitor")

start_button = tk.Button(root, text="Start", command=start_crawler)
stop_button = tk.Button(root, text="Stop", command=stop_crawler)
start_button.pack()
stop_button.pack()

domain_entry = tk.Entry(root)
add_domain_button = tk.Button(root, text="Add Domain", command=add_domain)
domain_entry.pack()
add_domain_button.pack()

progress_text = scrolledtext.ScrolledText(root, height=10)
progress_text.pack()

root.mainloop()
