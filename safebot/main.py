from fastapi import FastAPI
from fastapi import APIRouter
from mangum import Mangum
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

import os
import aioredis

from aredis_om import (
    Migrator,
    get_redis_connection,
)

from safebot.models.site import SiteModel
from safebot.routers.verify import verify_router

app = FastAPI(title="Safebot")
app.include_router(verify_router, prefix="")


@app.on_event("startup")
async def startup():
    redis_url = os.environ.get('REDIS_CACHE_URL', None)
    r = aioredis.from_url(redis_url, encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(r), prefix="fastapi-cache")

    # You can set the Redis OM URL using the REDIS_OM_URL environment
    # variable, or by manually creating the connection using your model's
    # Meta object.
    SiteModel.Meta.database = get_redis_connection(url=redis_url, decode_responses=True)
    await Migrator().run()

lambda_handler = Mangum(app)

#https://github.com/redis/redis-om-python/blob/main/docs/fastapi_integration.md

#https://app.redislabs.com/#/login