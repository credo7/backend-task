import random
import string

from aiohttp import web
from aiohttp.web import Request, Response

from models import GenerateShortURLInput
from mongo_service import MongoService
from utils import backoff


class URLShortenerApp:
    """
        A URL shortener application that generates and manages short URLs.

        Parameters:
            mongo_service (MongoService): An instance of the MongoService class to interact with MongoDB.
            domain (str): The domain where short URLs will be hosted.
            protocol (str): The protocol to use in the short URLs (e.g., 'http' or 'https').
            link_length (int): The length of the generated short URL path. Default is 5.

        Usage:
            app = web.Application()
            mongo_service = MongoService(...)
            url_shortener = URLShortenerApp(mongo_service, 'example.com', 'https', link_length=5)
            app.router.add_post('/generate_short_url', url_shortener.generate_short_url)
            app.router.add_get('/{short_url_path}', url_shortener.redirect_to_original_url)
            app.router.add_get('/get_long_url/{short_url_path}', url_shortener.get_long_url)
            app.router.add_get('/count/{short_url_path}', url_shortener.get_short_url_visits)

    """

    def __init__(self, mongo_service: MongoService, domain: str, protocol: str, link_length=5):
        self.mongo_service = mongo_service
        self._link_length = link_length
        self._domain = domain
        self._protocol = protocol

    @backoff()
    async def generate_short_url(self, request: Request) -> Response:
        """
                Generate a short URL for a given long URL.

                This method handles the POST request to generate a short URL for a provided long URL.
                It validates the input data, generates a unique short URL path, and inserts the URL mapping into the database.

                Args:
                    request: aiohttp request object containing JSON data with the 'long_url' parameter.

                Returns:
                    aiohttp.web.Response: JSON response containing the generated short URL.
        """
        data = await request.json()
        GenerateShortURLInput(**data)
        long_url = data.get('long_url')
        if not long_url:
            return web.Response(text='long_url parameter was not specified', status=400)

        if short_url_path := self.mongo_service.find_short_url_path_by_long_url(long_url=long_url):
            short_url = self._generate_full_url(path=short_url_path)
            return web.json_response({'short_url': short_url})

        short_url_path = await self._generate_unique_short_url_path()
        self.mongo_service.insert_url_mapping(short_url_path=short_url_path, long_url=long_url)

        short_url = self._generate_full_url(path=short_url_path)
        return web.json_response({'short_url': short_url})

    async def redirect_to_original_url(self, request: Request) -> Response:
        """
                Redirect to the original URL corresponding to the provided short URL path.

                This method handles the GET request to redirect users to the original long URL
                corresponding to the provided short URL path.

                Args:
                    request: aiohttp request object containing the 'short_url_path' parameter in the URL.

                Returns:
                    aiohttp.web.Response: HTTPFound response for redirection.
        """
        short_url_path = request.match_info['short_url_path']
        if not short_url_path:
            return web.Response(text='short url path was not provided', status=400)

        long_url = self.mongo_service.find_long_url_by_short_url_path(short_url_path=short_url_path)

        if not long_url:
            return web.Response(text='urls were not found', status=400)

        self.mongo_service.increment_short_url_path_counter(short_url_path=short_url_path)

        raise web.HTTPFound(long_url)

    @backoff()
    async def get_long_url(self, request: Request) -> Response:
        """
                Get the original long URL corresponding to the provided short URL path.

                This method handles the GET request to retrieve the original long URL
                corresponding to the provided short URL path.

                Args:
                    request: aiohttp request object containing the 'short_url_path' parameter in the URL.

                Returns:
                    aiohttp.web.Response: JSON response containing the long URL.
        """
        short_url_path = request.match_info['short_url_path']
        if not short_url_path:
            return web.Response(text='short url path was not provided', status=400)

        long_url = self.mongo_service.find_long_url_by_short_url_path(short_url_path=short_url_path)

        if not long_url:
            return web.Response(text="long url doesn't exist", status=400)

        return web.json_response({'long_url': long_url})

    @backoff()
    async def get_short_url_visits(self, request: Request) -> Response:
        """
                Get the number of visits to the provided short URL path.

                This method handles the GET request to retrieve the number of visits
                to the provided short URL path.

                Args:
                    request: aiohttp request object containing the 'short_url_path' parameter in the URL.

                Returns:
                    aiohttp.web.Response: JSON response containing the number of visits.
        """
        short_url_path = request.match_info['short_url_path']
        if not short_url_path:
            return web.Response(text='short url path was not provided', status=400)

        visits = self.mongo_service.find_short_url_path_visits(short_url_path=short_url_path)
        return web.json_response({'visits': visits})

    @backoff()
    async def _generate_unique_short_url_path(self) -> str:
        """
                Generate a unique short URL path.

                This method generates a random short URL path and ensures its uniqueness
                by checking if it already exists in the database. If the generated short URL path
                exists, it generates another one until a unique short URL path is found.

                Returns:
                    str: A unique short URL path consisting of characters from 'string.ascii_letters' and 'string.digits'.
        """
        while True:
            short_url_path = self._generate_short_url_path()
            if not self.mongo_service.is_short_url_path_exist(path=short_url_path):
                return short_url_path

    def _generate_short_url_path(self) -> str:
        """
                Generate a random short URL path.

                This method generates a random short URL path of a specified length using characters
                from 'string.ascii_letters' and 'string.digits'.

                Returns:
                    str: A random short URL path of the specified length.
        """
        allowed_characters = string.ascii_letters + string.digits
        return ''.join(random.choice(allowed_characters) for _ in range(self._link_length))

    def _generate_full_url(self, path: str) -> str:
        """
                Generate a full URL from the short URL path.

                This method constructs a full URL by combining the specified 'protocol', 'domain',
                and 'path' parameters.

                Args:
                    path (str): The short URL path to be combined with the protocol and domain.

                Returns:
                    str: The full URL constructed from the protocol, domain, and short URL path.
        """
        return f'{self._protocol}://{self._domain}/{path}'
