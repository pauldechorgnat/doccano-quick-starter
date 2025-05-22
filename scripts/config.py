import os
from dotenv import load_dotenv
from utils import create_doccano_client
from logger import logger, set_logger_level

load_dotenv()


def get_env_variable(env_variable_name: str) -> str:
    value = os.environ.get(env_variable_name)
    if value is None:
        raise EnvironmentError(f"{env_variable_name} is not set")
    return value


DOCCANO_USERNAME = get_env_variable("ADMIN_USERNAME")
DOCCANO_PASSWORD = get_env_variable("ADMIN_PASSWORD")
DOCCANO_URL = get_env_variable("DOCCANO_URL")
PROJECT_NAME = get_env_variable("PROJECT_NAME")
LOG_LEVEL = get_env_variable("LOG_LEVEL")

if (
    (DOCCANO_PASSWORD is None)
    or (DOCCANO_USERNAME is None)
    or (DOCCANO_URL is None)
    or (PROJECT_NAME is None)
    or (LOG_LEVEL is None)
):
    raise EnvironmentError("Environment variables are not set.")

set_logger_level(
    logger=logger,
    level=LOG_LEVEL,
)


doccano_client = create_doccano_client(
    username=DOCCANO_USERNAME,
    password=DOCCANO_PASSWORD,
    base_url=DOCCANO_URL,
)
