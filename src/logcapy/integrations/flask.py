try:
    from flask import Flask, request, g, Response
except ImportError:
    Flask = object # type: ignore
    request = object # type: ignore
    g = object # type: ignore
    Response = object # type: ignore

import uuid
import time
from ..core.context import LogContext
from ..config import global_config

class LogCapyExtension:
    """
    Flask Extension for LogCapy.
    """
    def __init__(self, app: Flask = None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        self.logger = global_config.get_logger()

        @app.before_request
        def before_request():
            request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
            g.start_time = time.time()
            g.request_id = request_id
            
            LogContext.clear()
            LogContext.set("request_id", request_id)
            LogContext.set("method", request.method)
            LogContext.set("path", request.path)
            LogContext.set("client_ip", request.remote_addr)
            LogContext.set("user_agent", request.headers.get("User-Agent"))

        @app.after_request
        def after_request(response: Response):
            duration = time.time() - g.start_time
            self.logger.info(
                f"{request.method} {request.path} - {response.status_code} - {duration:.4f}s",
                context=LogContext.get_all()
            )
            response.headers["X-Request-ID"] = g.request_id
            return response

        @app.teardown_request
        def teardown_request(exception=None):
            if exception:
                self.logger.error(
                    f"Unhandled exception in {request.method} {request.path}: {exception}",
                    context=LogContext.get_all(),
                    exc_info=True
                )
