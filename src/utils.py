import asyncio
import json
import logging
from functools import wraps

from aiohttp import web
from pydantic import ValidationError


def backoff(start_sleep_time=0.1, factor=2, border_sleep_time=10):
    """
        Функция для повторного выполнения функции через некоторое время, если возникла ошибка. Использует наивный экспоненциальный рост времени повтора (factor) до граничного времени ожидания (border_sleep_time)

        Формула:
            t = start_sleep_time * 2^(n) if t < border_sleep_time
            t = border_sleep_time if t >= border_sleep_time
        :param start_sleep_time: начальное время повтора
        :param factor: во сколько раз нужно увеличить время ожидания
        :param border_sleep_time: граничное время ожидания
        :return: результат выполнения функции
        """
    current_sleep_time = start_sleep_time

    def func_wrapper(func):
        @wraps(func)
        async def inner(*args, **kwargs):
            nonlocal current_sleep_time
            while current_sleep_time < border_sleep_time:
                try:
                    return await func(*args, **kwargs)

                except json.JSONDecodeError:
                    return web.Response(text='Invalid JSON data in the request body.', status=400)

                except ValidationError as e:
                    # Extract the validation error information
                    errors = []
                    for error in e.errors():
                        field_name = '.'.join(error['loc'])
                        error_msg = error['msg']
                        errors.append({'field': field_name, 'message': error_msg})
                    # Return a custom response with the validation errors and a 400 status code
                    return web.json_response({'errors': errors}, status=400)

                except Exception as e:
                    logging.error(str(e))

                await asyncio.sleep(current_sleep_time)
                current_sleep_time *= factor

            # If the function is still failing after the maximum retries, return an error response to the client
            return web.Response(text='An internal server error occurred.', status=500)

        return inner

    return func_wrapper
