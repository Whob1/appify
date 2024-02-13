from quart import Quart, render_template, request, redirect, url_for, websocket
import asyncio
from crawler import Crawler
import json

app = Quart(__name__)

class CrawlerManager:
    def __init__(self):
        self.crawler = None

    async def update_callback(self, data):
        await websocket.send(json.dumps(data))

    async def start_crawler(self, start_urls):
        if not self.crawler or not self.crawler.is_running:
            self.crawler = Crawler(self.update_callback)
            await self.crawler.start(start_urls)

    async def stop_crawler(self):
        if self.crawler and self.crawler.is_running:
            await self.crawler.stop()

    async def pause_crawler(self):
        if self.crawler and self.crawler.is_running:
            await self.crawler.pause()

    async def resume_crawler(self):
        if self.crawler and not self.crawler.is_running:
            await self.crawler.resume()

crawler_manager = CrawlerManager()

@app.route('/start', methods=['POST'])
async def start():
    try:
        start_urls_input = await request.form.get('start_urls', '')
        start_urls = [url.strip() for url in start_urls_input.split(',') if url.strip()]
        if start_urls:
            await crawler_manager.start_crawler(start_urls)
        else:
            app.logger.error("No valid start URLs provided.")
    except Exception as e:
        app.logger.error(f"Error starting crawler: {e}")
    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
async def stop():
    try:
        await crawler_manager.stop_crawler()
    except Exception as e:
        app.logger.error(f"Error stopping crawler: {e}")
    return redirect(url_for('index'))

@app.route('/pause', methods=['POST'])
async def pause():
    try:
        await crawler_manager.pause_crawler()
    except Exception as e:
        app.logger.error(f"Error pausing crawler: {e}")
    return redirect(url_for('index'))

@app.route('/resume', methods=['POST'])
async def resume():
    try:
        await crawler_manager.resume_crawler()
    except Exception as e:
        app.logger.error(f"Error resuming crawler: {e}")
    return redirect(url_for('index'))

@app.route('/')
async def index():
    return await render_template('index.html')

@app.websocket('/stream')
async def stream():
    while True:
        data = await websocket.receive()
        await websocket.send(data)

if __name__ == "__main__":
    app.run(port=5000, use_reloader=True, debug=True)
