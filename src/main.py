from typing import Union

from fastapi import FastAPI
from httpx import AsyncClient
from pydantic import BaseModel
from mangum import Mangum

import os
import json
import re

environment = os.environ.get('ENVIRONMENT', None)
base_path = f"/{environment}" if environment else "/"

app = FastAPI(title="Safebot", openapi_prefix=base_path)
http_client = AsyncClient()

class Site(BaseModel):
    url: str
    email: Union[str, None] = None
    cnpj: Union[str, None] = None

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

@app.post("/verify")
async def root(site: Site):

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
        return {f"o site {site.url} é seguro"}
    return {f"o site {site.url} não é seguro"}

lambda_handler = Mangum(app, api_gateway_base_path=base_path)
