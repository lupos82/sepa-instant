"""Descargas HTTP prudentes: reintentos con espera, peticiones condicionales y límite de tamaño.

No se usan credenciales, no se eluden autenticaciones ni bloqueos: si una fuente responde
401/403/429 o pide registro, el conector falla y se conserva la versión anterior.
"""
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from . import __version__
from .util import sha256_bytes

USER_AGENT = f"Cryptopocket-SEPA-Tools/{__version__} (+https://cryptopocket.io/tools/; datos abiertos)"
MAX_BYTES = 200 * 1024 * 1024


class FetchError(Exception):
    pass


@dataclass
class FetchResult:
    url: str
    status: int
    content: bytes = b""
    etag: str = ""
    last_modified: str = ""
    sha256: str = ""
    not_modified: bool = False
    headers: dict = field(default_factory=dict)


def fetch(url: str, etag: str = "", last_modified: str = "", retries: int = 3, timeout: int = 90,
          accept: str = "*/*", max_bytes: int = MAX_BYTES) -> FetchResult:
    headers = {"User-Agent": USER_AGENT, "Accept": accept}
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read(max_bytes + 1)
                if len(body) > max_bytes:
                    raise FetchError(f"respuesta mayor de {max_bytes} bytes")
                h = {k.lower(): v for k, v in r.headers.items()}
                return FetchResult(url=r.geturl(), status=r.status, content=body, etag=h.get("etag", ""),
                                   last_modified=h.get("last-modified", ""), sha256=sha256_bytes(body), headers=h)
        except urllib.error.HTTPError as e:
            if e.code == 304:
                return FetchResult(url=url, status=304, not_modified=True, etag=etag, last_modified=last_modified)
            if e.code in (401, 403, 407):
                raise FetchError(f"HTTP {e.code}: acceso no autorizado; no se reintenta ni se elude") from e
            last_err = e
            if e.code == 429:
                time.sleep(30 * (attempt + 1))
                continue
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            last_err = e
        time.sleep(5 * (attempt + 1))
    raise FetchError(f"no se pudo descargar {url}: {last_err}")
