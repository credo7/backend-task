from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_hostname: str
    database_port: int
    database_name: str
    links_collection_name: str
    protocol: str
    service_domain: str
    api_port: int

    class Config:
        env_file = '../.env'


settings = Settings()
