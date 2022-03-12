# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
import importlib.resources as ir
from typing import Dict

from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
import srsly

from . import data, config, controllers
from .models import TranslationRequest


load_dotenv(find_dotenv())

_allow_origins = config.get_allowed_origins()

with ir.path(data, 'example_translation_request.json') as ex_path:
    with open(ex_path) as fp:
        example_translation_request = srsly.json_loads(fp.read())

marian_server = controllers.MarianServer(os.getenv('MARIAN_CONFIG_PATH'),
                                         os.getenv('MARIAN_WS_ADDRESS'))

app = FastAPI(
    title='API Gwasanaeth Cyfieithu Peirianyddol',
    version='0.1',
    description='API Cyfieithu Peirianyddol.',
    openapi_url='/api/openapi.json',
    docs_url='/api/docs',
    redoc_url='/api/redoc')
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=_allow_origins,
    allow_methods=['*'],
    allow_headers=['*'])


@app.on_event('startup')
async def startup():
    await marian_server.start()


@app.on_event('shutdown')
async def shutdown():
    await marian_server.shutdown()


@app.head('/api/translate', response_model=Dict[str, str])
@app.get('/api/info', response_model=Dict[str, str])
def info():
    return marian_server.config


@app.post('/api/translate', response_model=Dict[str, str])
async def translate(item: TranslationRequest, tags=['translation']):
    """Translation sentences from source language to target language.."""
    src_lang = item.source_language or os.getenv('SOURCE_LANGUAGE')
    trg_lang = item.target_language or os.getenv('TARGET_LANGUAGE')
    return await marian_server.translate(item.text, src_lang, trg_lang)
