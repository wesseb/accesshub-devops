from http.server import ThreadingHTTPServer

from app import db
from app.config import config
from app.handlers import AccessHubHandler
from app.logger import get_logger

log = get_logger(__name__)


def main() -> None:
    db.init_db()
    server = ThreadingHTTPServer((config.HOST, config.PORT), AccessHubHandler)
    log.info("AccessHub listening on %s:%s", config.HOST, config.PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("shutting down")
        server.shutdown()


if __name__ == "__main__":
    main()
