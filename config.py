import json
from typing import Any, Union

import boto3
from pydantic import BaseSettings
from pydantic.env_settings import SettingsSourceCallable

ssm_client = boto3.client("ssm", region_name="us-east-1")


class SecretManagerConfig:

    @classmethod
    def _get_secret(cls, secret_name: str) -> Union[str, dict[str, Any]]:
        secret_name = f"/social-media-backend/{secret_name}"
        print(f"Getting secret {secret_name}")
        secret_string = ssm_client.get_parameter(
            Name=secret_name, WithDecryption=True)["Parameter"]["Value"]
        try:
            return json.loads(secret_string)
        except json.decoder.JSONDecodeError:
            return secret_string

    @classmethod
    def get_secrets(cls, settings: BaseSettings) -> dict[str, Any]:
        return {
            name: cls._get_secret(name)
            for name, _ in settings.__fields__.items()
        }

    @classmethod
    def customise_sources(
        cls,
        init_settings: SettingsSourceCallable,
        env_settings: SettingsSourceCallable,
        file_secret_settings: SettingsSourceCallable,
    ):
        return (
            init_settings,
            cls.get_secrets,
            env_settings,
            file_secret_settings,
        )


class Settings(BaseSettings):
    """Server config settings"""

    # Mongo Engine settings
    mongo_uri: str

    # Neo4j settings
    neo4j_uri: str
    neo4j_username: str
    neo4j_password: str

    class Config(SecretManagerConfig):
        ...


CONFIG = Settings()
