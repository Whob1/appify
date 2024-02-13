from flask import Flask, render_template, request, redirect, url_for, Response
import asyncio
from crawler import Crawler
from threading import Thread
from queue import Queue
import time
import os

app = Flask(__name__)

class CrawlerManager:
    def __init__(self):
        self.crawler = None
        self.loop = None
    
    def start_crawler(self, start_urls, update_callback):
        if not self.crawler or not self.crawler.is_running:
            self.crawler = Crawler(update_callback=update_callback)
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.crawler.start(start_urls))
    
    def stop_crawler(self):
        if self.crawler and self.crawler.is_running:
            self.loop.run_until_complete(self.crawler.stop())
            self.loop.close()
    
    def add_domain(self, domain):
        if self.crawler and self.crawler.is_running:
            self.loop.run_until_complete(self.crawler.add_domain(domain))

crawler_manager = CrawlerManager()
messages = Queue()

def update_callback(message):
    messages.put(message)

def start_crawler_background(start_urls):
    crawler_manager.start_crawler(start_urls, update_callback)

def stop_crawler_background():
    crawler_manager.stop_crawler()

def add_domain_background(domain):
    crawler_manager.add_domain(domain)

@app.route('/start', methods=['POST'])
def start():
    try:
        start_urls = request.form.getlist('start_urls')
        Thread(target=start_crawler_background, args=(start_urls,), daemon=True).start()
    except Exception as e:
        app.logger.error(f"Error starting crawler: {e}")
    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop():
    try:
        Thread(target=stop_crawler_background, daemon=True).start()
    except Exception as e:
        app.logger.error(f"Error stopping crawler: {e}")
    return redirect(url_for('index'))

@app.route('/add_domain', methods=['POST'])
def add_domain():
    try:
        domain = request.form['domain']
        Thread(target=add_domain_background, args=(domain,), daemon=True).start()
    except Exception as e:
        app.logger.error(f"Error adding domain: {e}")
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
