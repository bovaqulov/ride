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
    DATABASE_PUBLIC_URL: str
    # default api url
    DEFAULT_API_URL: str
    # celery
    CELERY_BROKER_URL_DEMO: str = 'redis://localhost:6379/1'
    CELERY_RESULT_BACKEND_DEMO: str = 'redis://localhost:6379/1'
    REDIS_PUBLIC_URL: str

    PASSENGER_BOT_URL: str
    DRIVER_BOT_URL: str

    class Config:
        env_file = ".env"

    @property
    def CELERY_BROKER_URL(self):
        return self.CELERY_BROKER_URL_DEMO if self.DEBUG  else self.REDIS_PUBLIC_URL

    @property
    def CELERY_RESULT_BACKEND(self):
        return self.CELERY_RESULT_BACKEND_DEMO if self.DEBUG else self.REDIS_PUBLIC_URL

    @property
    def ALLOWED_HOSTS(self) -> List[str]:
        return [
            '127.0.0.1',
            "0.0.0.0",
            "ride-production-62e7.up.railway.app"
        ]

    @property
    def DB_URL(self) -> str:
        return self.DEMO_DB_URL if self.DEBUG else self.DATABASE_PUBLIC_URL

    @property
    def init_database(self):
        return {
            'default': dj_database_url.config(
                default=self.DB_URL,
                conn_max_age=600,
                ssl_require=False
            )
        }

    @property
    def PASSENGER_URL(self) -> str:
        return self.PASSENGER_BOT_URL

    @property
    def DRIVER_URL(self):
        return self.DRIVER_BOT_URL



def en():
    return EventSettings()


env = en()
