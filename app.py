from flask import Flask, render_template, request, redirect, url_for, Response
import asyncio
from crawler import Crawler
from threading import Thread

app = Flask(__name__)
crawler = None

def start_crawler_background():
    asyncio.run(crawler.start())

@app.route('/start', methods=['POST'])
def start():
    global crawler
    if not crawler or not crawler.is_running:
        crawler = Crawler(update_callback=update_callback)
        Thread(target=start_crawler_background, daemon=True).start()
    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop():
    if crawler and crawler.is_running:
        asyncio.run_coroutine_threadsafe(crawler.stop(), asyncio.get_event_loop())
    return redirect(url_for('index'))

@app.route('/add_domain', methods=['POST'])
def add_domain():
    domain = request.form['domain']
    if crawler and domain:
        asyncio.run_coroutine_threadsafe(crawler.add_domain(domain), asyncio.get_event_loop())
    return redirect(url_for('index'))

@app.route('/')
def index():
    return render_template('index.html')

def update_callback(message):
    # Implement functionality to stream this message back to the client using SSE or WebSocket

@app.route('/stream')
def stream():
    def generate():
        # Yield messages for SSE
        if crawler:
            for message in crawler.get_messages():  # Assuming crawler can provide messages
                yield f"data: {message}\n\n"
    return Response(generate(), mimetype='text/event-stream')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, threaded=True)
