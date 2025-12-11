from typing import List

import dj_database_url
from pydantic_settings import BaseSettings


class EventSettings(BaseSettings):
    # debug
    DEBUG: bool = True
    # secret
    SECRET_KEY: str
    # db url
    DEMO_DB_URL: str = "sqlite:///db.sqlite3"
    DATABASE_PUBLIC_URL: str = "sqlite:///db.sqlite3"
    # default api url
    DEFAULT_API_URL: str

    CELERY_BROKER_URL_DEMO: str = 'redis://localhost:6379/1'
    CELERY_RESULT_BACKEND_DEMO: str = 'redis://localhost:6379/1'
    REDIS_PUBLIC_URL: str

    PASSENGER_BOT_URL: str
    DRIVER_BOT_URL: str

    ESKIZ_HOST: str
    ESKIZ_EMAIL: str
    ESKIZ_PASSWORD: str

    GROUP_ID: int = 4817936909
    MAIN_BOT: str = None

    class Config:
        env_file = ".env"

    @property
    def CELERY_BROKER_URL(self):
        # return self.CELERY_BROKER_URL_DEMO
        return self.REDIS_PUBLIC_URL

    @property
    def CELERY_RESULT_BACKEND(self):
        # return self.CELERY_RESULT_BACKEND_DEMO
        return self.REDIS_PUBLIC_URL

    @property
    def ALLOWED_HOSTS(self) -> List[str]:
        return [
            '127.0.0.1',
            "0.0.0.0",
            "ride-production-62e7.up.railway.app"
        ]

    @property
    def DB_URL(self) -> str:
        return self.DATABASE_PUBLIC_URL

    @property
    def DATABASES(self):
        """Django DATABASES sozlamasi"""
        return {
            'default': dj_database_url.config(
                default=self.DB_URL,
                conn_max_age=600,
                ssl_require=False
            )
        }

    @property
    def PASSENGER_URL(self) -> str:
        # return self.PASSENGER_BOT_URL
        return "http://127.0.0.1:8888/"

    @property
    def DRIVER_URL(self):
        # return self.DRIVER_BOT_URL
        return "http://127.0.0.1:8080/"

def en():
    return EventSettings()


env = en()

# psql -h database-1.czic202o6e4s.eu-north-1.rds.amazonaws.com -U postgres -d postgres database connection
