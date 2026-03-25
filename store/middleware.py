import time
import logging

logger = logging.getLogger("request_logger")

class RequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.time()
        response = self.get_response(request)
        duration = (time.time() - start) * 1000
        logger.info(f"{request.method} {request.path} {response.status_code} {duration:.2f}ms")
        return response