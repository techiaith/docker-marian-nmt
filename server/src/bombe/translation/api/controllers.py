from contextlib import closing
from pathlib import Path
import shlex
import subprocess
import time

from techiaith.utils.bitext import Sentence, normalize
import sentencepiece
import spacy
import srsly
import websocket


class MarianServer:

    marain_server_cmd = ('marian-server '
                         '--allow-unk '
                         '-c {config_path} '
                         '--port {ws_port}')

    def __init__(self, config_path: Path, ws_port: str):
        self.config_path = config_path
        self.config = self.read_config(config_path)
        self.ws_port = ws_port
        self.marian_ws_addr = f'ws://127.0.0.1:{ws_port}/translate'
        print('VOCAB:', self.vocab)
        self.spm = sentencepiece.SentencePieceProcessor(self.vocab)
        self.nlp = spacy.load('en_core_web_sm', disable=['tagger'])
        self.nlp.add_pipe('sentencizer')
        self.proc = None

    @property
    def vocab(self):
        return self.config['vocabs']

    def read_config(self, config_path):
        with open(config_path) as fp:
            config = srsly.yaml_loads(fp.read())
        return {k: v[0] if isinstance(v, list) else v
                for (k, v) in config.items()}

    def pre_process(self, text, lang):
        spm_encode = self.spm.encode
        doc = self.doc = self.nlp(normalize(text))
        for i, sent in enumerate(doc.sents, start=1):
            print(f'Sent to translate {i}:', sent.text)
            sent = Sentence(sent.text, lang)
            text = sent.text.strip().rstrip('.')
            yield ' '.join(spm_encode(text, out_type=str))

    def post_process(self, translated_sentences, lang):
        for sent in map(self.spm.decode, translated_sentences):
            yield sent

    async def translate(self, source_text, source_lang, target_lang):
        out_sep = '\n' if source_text.find('\n') >= 0 else '  '
        source_sentences = list(self.pre_process(source_text, source_lang))
        raw = translated = None
        print('Using WS:', self.marian_ws_addr)
        with closing(websocket.create_connection(self.marian_ws_addr)) as ws:
            ws.send('\n'.join(source_sentences))
            translated = ws.recv().splitlines()
            print('Before pre-process:', translated)
            ws.send('\n'.join(source_text.split('\n')))
            translated_raw = ws.recv().splitlines()
        target_sentences = list(self.post_process(translated, target_lang))
        return dict(translated=out_sep.join(target_sentences),
                    source_text=source_text,
                    source_sentences='\n'.join(map(str, self.doc.sents)),
                    before_post_proc='\n' .join(translated),
                    raw='\n'.join(translated_raw),
                    source_lang=source_lang,
                    target_lang=target_lang)

    async def start(self):
        cmd = self.marain_server_cmd.format(config_path=self.config_path,
                                            ws_port=self.ws_port)
        self.proc = subprocess.Popen(shlex.split(cmd))

    async def restart(self):
        self.shutdown()
        time.sleep(1)
        self.start()

    async def shutdown(self):
        if self.proc is not None:
            self.proc.terminate()
            self.proc.wait()
