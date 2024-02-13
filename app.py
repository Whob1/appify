from flask import Flask, render_template, request, redirect, url_for, Response
import asyncio
from crawler import Crawler
from threading import Thread
from queue import Queue
import time
import json

app = Flask(__name__)

class CrawlerManager:
    def __init__(self):
        self.crawler = None
        self.loop = None
    
    def update_callback(self, data):
        messages.put(data)

    def start_crawler(self, start_urls):
        if not self.crawler or not self.crawler.is_running:
            self.crawler = Crawler(self.update_callback)
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.crawler.start(start_urls))
    
    def stop_crawler(self):
        if self.crawler and self.crawler.is_running:
            self.loop.run_until_complete(self.crawler.stop())
            self.loop.close()

    def pause_crawler(self):
        if self.crawler and self.crawler.is_running:
            self.loop.run_until_complete(self.crawler.pause())

    def resume_crawler(self):
        if self.crawler and not self.crawler.is_running:
            self.loop.run_until_complete(self.crawler.resume())

crawler_manager = CrawlerManager()
messages = Queue()

@app.route('/start', methods=['POST'])
def start():
    try:
        start_urls_input = request.form.get('start_urls', '')
        start_urls = [url.strip() for url in start_urls_input.split(',') if url.strip()]
        start_urls = [f"http://{url}" if not url.startswith(('http://', 'https://')) else url for url in start_urls]

        if start_urls:
            Thread(target=crawler_manager.start_crawler, args=(start_urls,), daemon=True).start()
        else:
            app.logger.error("No valid start URLs provided.")
    except Exception as e:
        app.logger.error(f"Error starting crawler: {e}")
    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop():
    try:
        Thread(target=crawler_manager.stop_crawler, daemon=True).start()
    except Exception as e:
        app.logger.error(f"Error stopping crawler: {e}")
    return redirect(url_for('index'))

@app.route('/pause', methods=['POST'])
def pause():
    try:
        Thread(target=crawler_manager.pause_crawler, daemon=True).start()
    except Exception as e:
        app.logger.error(f"Error pausing crawler: {e}")
    return redirect(url_for('index'))

@app.route('/resume', methods=['POST'])
def resume():
    try:
        Thread(target=crawler_manager.resume_crawler, daemon=True).start()
    except Exception as e:
        app.logger.error(f"Error resuming crawler: {e}")
    return redirect(url_for('index'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream')
def stream():
    def generate():
        while True:
            if not messages.empty():
                message = messages.get()
                yield f"data: {message}\n\n"
            else:
                yield "data: heartbeat\n\n"
                time.sleep(15)
    return Response(generate(), mimetype='text/event-stream')

if __name__ == "__main__":
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    app.run(host=host, port=port, threaded=True)
