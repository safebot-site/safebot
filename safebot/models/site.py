from aredis_om import (
    Field,
    HashModel,
)

class SiteModel(HashModel):
    url: str = Field(index=True)
    is_secure: str