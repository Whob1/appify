from flask import Flask, render_template, request, redirect, url_for
import threading

# Assuming Crawler is updated to work with Flask and asyncio in a thread
from crawler import Crawler

app = Flask(__name__)
crawler = Crawler()
crawler_thread = None

def run_crawler():
    asyncio.run(crawler.start())

@app.route('/')
def index():
    # Display crawler status and controls
    return render_template('index.html', status=crawler.is_running)

@app.route('/start', methods=['POST'])
def start():
    global crawler_thread
    if not crawler.is_running:
        crawler_thread = threading.Thread(target=run_crawler, daemon=True)
        crawler_thread.start()
    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop():
    if crawler.is_running:
        asyncio.run(crawler.stop())
    return redirect(url_for('index'))

@app.route('/add_domain', methods=['POST'])
def add_domain():
    domain = request.form['domain']
    if domain:
        asyncio.run(crawler.add_domain(domain))
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
