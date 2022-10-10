from typing import Union

from fastapi import FastAPI, HTTPException
from httpx import AsyncClient
from pydantic import BaseModel
from mangum import Mangum

from bs4 import BeautifulSoup

from starlette.requests import Request
from starlette.responses import Response

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

import aioredis

from aredis_om import (
    Field,
    HashModel,
    Migrator,
    NotFoundError,
)

from aredis_om import get_redis_connection

from pydantic import HttpUrl, EmailStr

import os
import json
import re


environment = os.environ.get('ENVIRONMENT', None)
base_path = f"/{environment}" if environment else "/"

app = FastAPI(title="Safebot", openapi_prefix=base_path)
http_client = AsyncClient()


class Site(BaseModel):
    url: str
    email: Union[EmailStr, None] = None
    cnpj: Union[str, None] = None

class SiteModel(HashModel):
    url: str = Field(index=True)
    is_secure: str

# valida se site usa o protocolo HTTPS
def validate_protocol(site_url: str):
    return site_url.lower().startswith("https")

# valida certificado ssl
async def validate_certificate(site_url: str):
    try:
        response = await http_client.get(site_url)
        return True
    except:
        return False

# valida endereco de email de contato
async def validate_email(email: str):
    response = await http_client.get(f"https://api.eva.pingutil.com/email?email={email}")
    response_data = json.loads(response.text)["data"]

    if response_data["disposable"]:
        return False
    if response_data["catch_all"]:
        return False
    if response_data["gibberish"]:
        return False
    if response_data["spam"]:
        return False
    return True

# calcula o CNPJ da matriz a partir de outro CNPJ
def calculate_cnpj_matriz(site_cnpj):
    cnpj = list(site_cnpj[:12])
    cnpj[8] = '0'
    cnpj[9] = '0'
    cnpj[10] = '0'
    cnpj[11] = '1'
    cnpj = ''.join(cnpj)

    if (site_cnpj.endswith("0001", 0, 12)):
        return site_cnpj
    reverse_cnpj = list(map(int, cnpj[::-1]))

    pesos = [2, 3, 4, 5, 6, 7, 8, 9, 2, 3, 4, 5]
    for i in range(12):
        reverse_cnpj[i] = reverse_cnpj[i] * pesos[i]

    soma = 0
    for i in range(12):
        soma += reverse_cnpj[i]
    
    primeiro_digito_verificador = 11 - (soma % 11)

    if (primeiro_digito_verificador >= 10):
        primeiro_digito_verificador = '0'
    else:
        primeiro_digito_verificador = str(primeiro_digito_verificador)
    
    cnpj_matriz = list(cnpj)
    cnpj_matriz.append(primeiro_digito_verificador)
    reverse_cnpj = list(map(int, ''.join(cnpj_matriz)[::-1]))
    pesos = [2, 3, 4, 5, 6, 7, 8, 9, 2, 3, 4, 5, 6]
    for i in range(13):
        reverse_cnpj[i] = reverse_cnpj[i] * pesos[i]

    soma = 0
    for i in range(13):
        soma += reverse_cnpj[i]
    
    segundo_digito_verificador = 11 - (soma % 11)

    if (segundo_digito_verificador >= 10):
        segundo_digito_verificador = '0'
    else:
        segundo_digito_verificador = str(segundo_digito_verificador)
    
    cnpj_matriz.append(segundo_digito_verificador)

    return ''.join(cnpj_matriz)

# validar o CNPJ do dono do site com o CNPJ da empresa 
async def validate_cnpj(site_url, site_cnpj):
    domain_url = site_url[7:]
    response = await http_client.get(f"https://rdap.registro.br/domain/{domain_url}")
    cnpj = response.json()["entities"][0]["handle"]
    cnpj_matriz = calculate_cnpj_matriz(site_cnpj)

    return cnpj_matriz==cnpj

# valida reputacao do site no reclame aqui
async def validate_reclame_aqui(site_url):
    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
        'X-user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36 FKUA/website/41/website/Desktop',
        'Content-Type': 'application/json',
        'Origin': 'https://www.reclameaqui.com.br',
        'Host': 'www.reclameaqui.com.br',
        'Pragma': 'no-cache'
    }

    response = await http_client.get("https://www.reclameaqui.com.br/empresa/kabum/", headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    score = float(soup.find_all("span", class_="score")[0].b.extract().get_text())

    return score >= 6

async def update_cache(site_url: str, is_secure: bool):
    site_url = site_url[8:]
    try:
        site_model = await SiteModel.find(SiteModel.url == site_url).first()
        site_model.url = site_url
        site_model.is_secure = str(is_secure)

        await site_model.update()
    except NotFoundError:
        site_model = SiteModel(url=site_url, is_secure=str(is_secure))
        await site_model.save()

@app.post("/verify")
async def verify_site(site: Site):

    is_site_secure = validate_protocol(site.url)

    if is_site_secure:
        is_site_secure = await validate_certificate(site.url)

    if is_site_secure:
        if site.email:
            is_site_secure = await validate_email(site.email)
   
    if is_site_secure:
        if site.cnpj:
            is_site_secure = await validate_cnpj(site.url, site.cnpj)
    
    if is_site_secure:
        is_site_secure = await validate_reclame_aqui(site.url)

    await update_cache(site.url, is_site_secure)
    if is_site_secure:
        return {}
    raise HTTPException(status_code=422, detail="Site inseguro")

@app.get("/verify/{site_url:path}")
@cache(expire=7200)
async def verify_site_url(site_url: str, request: Request, response: Response):
    try:
        # normalize_url
        site_url = site_url[8:]
        site_model = await SiteModel.find(SiteModel.url == site_url).first()
        return {}
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Site not found")

@app.on_event("startup")
async def startup():
    redis_url = os.environ.get('REDIS_CACHE_URL', None)
    r = aioredis.from_url(redis_url, encoding="utf8",
                          decode_responses=False)
    FastAPICache.init(RedisBackend(r), prefix="fastapi-cache")

    # You can set the Redis OM URL using the REDIS_OM_URL environment
    # variable, or by manually creating the connection using your model's
    # Meta object.
    SiteModel.Meta.database = get_redis_connection(url=redis_url,
                                                  decode_responses=False)
    await Migrator().run()

lambda_handler = Mangum(app, api_gateway_base_path=base_path)

#https://github.com/redis/redis-om-python/blob/main/docs/fastapi_integration.md

#https://app.redislabs.com/#/login