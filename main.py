from fastapi import FastAPI
from httpx import AsyncClient
from pydantic import BaseModel

import json

app = FastAPI()
http_client = AsyncClient()

class Site(BaseModel):
    url: str
    email: str | None = None
    cnpj: str | None = None

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

@app.post("/verify")
async def root(site: Site):

    is_site_secure = validate_protocol(site.url)

    if is_site_secure:
        is_site_secure = await validate_certificate(site.url)

    if is_site_secure:
        if site.email:
            is_site_secure = await validate_email(site.email)

    if (is_site_secure):
        is_site_secure = validate_certificate(site_url)

    if (is_site_secure):
        return {f"certificado válido para o site: {site_url}"}
    return {f"certificado inválido para o site: {site_url}"}