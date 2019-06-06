import aiohttp_jinja2
import jinja2
from aiohttp import web

from background_tasks import start_background_tasks, cleanup_background_tasks
from routes import setup_routes
from utils import init_app

app = web.Application()
app = init_app(app)

app.router.add_static('/static/', path='static', name='static')
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('templates'))

app.on_startup.append(start_background_tasks)
app.on_cleanup.append(cleanup_background_tasks)

setup_routes(app)
web.run_app(app)
