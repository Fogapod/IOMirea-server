"""
IOMirea-server - A server for IOMirea messenger
Copyright (C) 2019  Eugene Ershov

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""


import asyncio
import argparse
import ssl

from typing import Optional

import jinja2
import aiohttp_jinja2
import aiohttp_remotes
import aiohttp_session

from aiohttp_session.redis_storage import RedisStorage
from aiohttp import web

import middlewares

from routes.api.v0 import routes as api_v0_routes
from routes.auth import routes as auth_routes
from routes.oauth2 import routes as oauth2_routes
from routes.misc import routes as misc_routes

from models.snowflake import SnowflakeGenerator
from config import Config
from log import setup_logging, server_log, AccessLogger

from db.postgres import create_postgres_connection, close_postgres_connection
from db.redis import create_redis_pool, close_redis_pool


try:
    import uvloop
except ImportError:
    print(
        "Warning: uvloop library not installed or not supported on your system"
    )
    print("Warning: Using default asyncio event loop")
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


argparser = argparse.ArgumentParser(description="IOMirea server")

argparser.add_argument(
    "-d", "--debug", action="store_true", help="run server in debug mode"
)

argparser.add_argument(
    "--force-ssl",
    action="store_true",
    help="run https server (certificates paths should be configured)",
)

argparser.add_argument(
    "--with-eval", action="store_true", help="enable python eval endpoint"
)


async def on_startup(app: web.Application) -> None:
    aiohttp_jinja2.setup(
        app, loader=jinja2.FileSystemLoader("iomirea/templates")
    )

    # support for X-Forwarded headers
    await aiohttp_remotes.setup(app, aiohttp_remotes.XForwardedRelaxed())

    aiohttp_session.setup(app, RedisStorage(app["rd_conn"]))


if __name__ == "__main__":
    app = web.Application()

    app["args"] = argparser.parse_args()
    app["config"] = Config("config.yaml")
    app["sf_gen"] = SnowflakeGenerator()

    app.on_startup.append(create_postgres_connection)
    app.on_startup.append(create_redis_pool)
    app.on_startup.append(on_startup)

    app.on_cleanup.append(close_postgres_connection)
    app.on_cleanup.append(close_redis_pool)

    app.router.add_routes(auth_routes)
    app.router.add_routes(misc_routes)

    # API subapps
    APIApp = web.Application(
        middlewares=[
            middlewares.error_handler,
            middlewares.match_info_validator,
        ]
    )

    APIv0App = web.Application()
    APIv0App.add_routes(api_v0_routes)

    # OAuth2 subapp
    OAuth2App = web.Application()
    OAuth2App.add_routes(oauth2_routes)
    OAuth2App["auth_sessions"] = {}

    APIApp.add_subapp("/v0/", APIv0App)
    APIApp.add_subapp("/oauth2/", OAuth2App)

    app.add_subapp("/api/", APIApp)

    # logging setup
    setup_logging(app)

    # SSL setup
    ssl_context: Optional[ssl.SSLContext] = None

    if app["args"].force_ssl:
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_section = app["config"]["ssl"]
        ssl_context.load_cert_chain(
            ssl_section["cert-chain-path"], ssl_section["cert-privkey-path"]
        )

    server_log.info(
        f'Running in {"debug" if app["args"].debug else "production"} mode'
    )

    # debug setup
    if app["args"].debug:
        from routes.debug import routes as debug_routes
        from routes.debug import shutdown as debug_shutdown

        Debugapp = web.Application()
        Debugapp.add_routes(debug_routes)

        Debugapp.on_cleanup.append(debug_shutdown)

        app.add_subapp("/debug", Debugapp)

        if app["args"].with_eval:
            server_log.info(
                f"Python eval endpoint launched at: {Debugapp.router['python-eval'].url_for()}"
            )

    web.run_app(
        app,
        access_log_class=AccessLogger,
        port=app["config"]["app-port"],
        ssl_context=ssl_context,
        host="127.0.0.1",
    )
