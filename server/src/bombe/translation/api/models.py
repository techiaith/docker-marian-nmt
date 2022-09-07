from typing import Dict, Optional

from pydantic import BaseModel, Field


class TranslationRequest(BaseModel):
    text: str = Field(example='I have a headache.')
    source_language: Optional[str] = Field(default='en', example='en')
    target_language: Optional[str] = Field(default='cy', example='cy')


class Translated(BaseModel):
    text: str = Field(example='Mae gen i gur pen.')


class ServerConfig(BaseModel):
    experiment_id: str
    config: Dict[str, str]
