from fastapi import HTTPException
from fastapi import APIRouter

from starlette.requests import Request
from starlette.responses import Response

from fastapi_cache.decorator import cache

from safebot.validations.validate import (
    validate_protocol,
    validate_certificate,
    validate_email,
    validate_cnpj,
    validate_reclame_aqui,
)

# async def update_cache(site_url: str, is_secure: bool):
#     site_url = site_url[8:]
#     try:
#         site_model = await SiteModel.find(SiteModel.url == site_url).first()
#         site_model.url = site_url
#         site_model.is_secure = str(is_secure)

#         await site_model.update()
#     except NotFoundError:
#         site_model = SiteModel(url=site_url, is_secure=str(is_secure))
#         await site_model.save()

verify_router = APIRouter()

@verify_router.get("/verify/{site_url:path}")
@cache(expire=7200)
async def verify_site(site_url: str, email: str, cnpj: str, request: Request, response: Response):
    is_site_secure = validate_protocol(site_url)

    if is_site_secure:
        is_site_secure = await validate_certificate(site_url)

    if is_site_secure:
        if email:
            is_site_secure = await validate_email(email)
   
    if is_site_secure:
        if cnpj:
            is_site_secure = await validate_cnpj(site_url, cnpj)
    
    if is_site_secure:
        is_site_secure = await validate_reclame_aqui(site_url)

    #await update_cache(site_url, is_site_secure)
    if is_site_secure:
        return {}
    raise HTTPException(status_code=422, detail="Site inseguro")

    # try:
    #     # normalize_url
    #     site_url = site_url[8:]
    #     site_model = await SiteModel.find(SiteModel.url == site_url).first()
    #     return {}
    # except NotFoundError:
    #     raise HTTPException(status_code=404, detail="Site not found")