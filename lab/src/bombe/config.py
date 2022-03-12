from typing import Optional, Tuple
from pydantic import BaseModel, BaseSettings


class Settings(BaseSettings):
    pg_user: str
    pg_pass: str
    pg_host: str
    pg_port: int
    pg_db: str
    sqlalchemy_track_modifications: Optional[bool] = False

    def db_uri(self):
        db_conn_str = ('postgresql://{.pg_user}:{.pg_pass}'
                       '@{.pg_host}:{.pg_port}/{.pg_db}')
        return db_conn_str.format(self)


async def get_settings():
    return Settings()


# TODO: generate from `marian --help` ?
class MarianConfig(BaseModel):

    # Preallocate  arg  MB of work space
    workspace: int

    # Log training process information to file given by  arg
    log: str

    # Set verbosity level of logging: trace, debug, info, warn,
    # err(or), critical, off
    log_level: Optional[str] = 'info'

    # Set time zone for the date shown on logging
    log_time_zone: Optional[str] = 'utc'

    # Seed for all random number generators. 0 means initialize randomly
    seed: Optional = int

    # allow the use of environment variables in paths, of the form ${VAR_NAME}
    interpolate_env_vars: Optional[bool] = True

    # All paths are relative to the config file location
    relative_paths: Optional[bool] = True


class ModelOptions(BaseModel):
    train_sets: str
    valid_sets: str
    vocabs: str
    valid_metrics: Tuple[str]
