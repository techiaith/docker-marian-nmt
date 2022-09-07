import logging
import requests


class Client:

    def __init__(self, service, lang, default_chunk_size=8192):
        self.lang = lang
        self.service = service
        self.default_chunk_size = default_chunk_size
        self.log = logging.getLogger(__name__)

    def format_url(self, *parts):
        url_parts = [self.service, self.lang]
        url_parts.extend(filter(None, parts))
        return '/'.join(url_parts)

    def list_all(self, endpoint, domain):
        url = self.format_url(endpoint)
        response = requests.get(url)
        subs = response.json()['submissions']
        domains = set(d.lower() for d in domain)
        return list(sub
                    for sub in subs
                    if not domains or sub['domain'].lower() in domains)
