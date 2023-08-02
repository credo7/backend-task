from pydantic import AnyUrl, BaseModel


class GenerateShortURLInput(BaseModel):
    long_url: AnyUrl
