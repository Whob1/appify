from flask import Flask, render_template, request, redirect, url_for, Response
import asyncio
from crawler import Crawler
from threading import Thread
from queue import Queue
import time

app = Flask(__name__)
crawler = None
messages = Queue()  # Queue to hold messages for SSE

def update_callback(message):
    """Callback function to receive messages from the crawler."""
    messages.put(message)  # Add message to the queue

def start_crawler_background(start_urls):
    """Function to start the crawler with given start URLs within a new event loop."""
    global crawler
    if crawler is None or not crawler.is_running:
        crawler = Crawler(update_callback=update_callback)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(crawler.start(start_urls))

def stop_crawler_background():
    """Function to stop the crawler within its event loop."""
    global crawler
    if crawler and crawler.is_running:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(crawler.stop())

def add_domain_background(domain):
    """Function to add a new domain to the crawler within its event loop."""
    global crawler
    if crawler and crawler.is_running:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(crawler.add_domain(domain))

@app.route('/start', methods=['POST'])
def start():
    """Flask route to start the crawler with specified start URLs."""
    start_urls = request.form.getlist('start_urls')  # Assuming a form field with name 'start_urls'
    Thread(target=start_crawler_background, args=(start_urls,), daemon=True).start()
    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop():
    """Flask route to stop the crawler."""
    Thread(target=stop_crawler_background, daemon=True).start()
    return redirect(url_for('index'))

@app.route('/add_domain', methods=['POST'])
def add_domain():
    """Flask route to add a new domain to the crawler."""
    domain = request.form['domain']
    Thread(target=add_domain_background, args=(domain,), daemon=True).start()
    return redirect(url_for('index'))

@app.route('/')
def index():
    """Flask route to render the main page."""
    return render_template('index.html')

@app.route('/stream')
def stream():
    """Flask route to stream real-time updates via SSE."""
    def generate():
        while True:
            if not messages.empty():
                message = messages.get()  # Retrieve message from the queue
                yield f"data: {message}\n\n"
            else:
                # Send a heartbeat every 15 seconds to keep the connection alive
                yield f"data: heartbeat\n\n"
                time.sleep(15)
    return Response(generate(), mimetype='text/event-stream')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, threaded=True)
