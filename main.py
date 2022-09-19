from fastapi import FastAPI
import requests

app = FastAPI()

# valida se site usa o protocolo HTTPS
def validate_protocol(site_url: str):
    return site_url.lower().startswith("https")

# valida certificado ssl
def validate_certificate(site_url: str):
    try:
        response = requests.get(site_url)
        return True
    except:
        return False

@app.get("/verify/{site_url:path}")
async def root(site_url: str):

    is_site_secure = validate_protocol(site_url)

    if (is_site_secure):
        is_site_secure = validate_certificate(site_url)

    if (is_site_secure):
        return {f"certificado válido para o site: {site_url}"}
    return {f"certificado inválido para o site: {site_url}"}