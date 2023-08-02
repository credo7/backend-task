import logging

from aiohttp import web

from config import settings
from mongo_service import MongoService
from urls_shortener import URLShortenerApp

logging.basicConfig(level=logging.DEBUG)


async def on_startup(_):
    logging.info(f'Server started on {settings.protocol}://{settings.service_domain}')


mongo_service = MongoService(
    hostname=settings.database_hostname,
    port=settings.database_port,
    db_name=settings.database_name,
    col_name=settings.links_collection_name,
)

urls_shortener_app = URLShortenerApp(
    mongo_service=mongo_service, domain=settings.service_domain, protocol=settings.protocol, link_length=5,
)


app = web.Application()

app.router.add_post('/generate_short_url', urls_shortener_app.generate_short_url)
app.router.add_get('/{short_url_path}', urls_shortener_app.redirect_to_original_url)
app.router.add_get('/get_long_url/{short_url_path}', urls_shortener_app.get_long_url)
app.router.add_get('/count/{short_url_path}', urls_shortener_app.get_short_url_visits)

app.on_startup.append(on_startup)

if __name__ == '__main__':
    web.run_app(app)
