from typing import Dict, Optional

from pydantic import BaseModel


class TranslationRequest(BaseModel):
    text: str
    source_language: Optional[str] = 'en'
    target_language: Optional[str] = 'cy'


class Translated(BaseModel):
    text: str
    language: str


class ServerConfig(BaseModel):
    experiment_id: str
    config: Dict[str, str]
