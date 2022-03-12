import os


def get_allowed_origins():
    origins = os.getenv('API_ALLOW_CORS_ORIGINS', '').split(',')
    return list(map(str.strip, origins))
