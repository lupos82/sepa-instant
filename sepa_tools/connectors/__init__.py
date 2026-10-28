"""Registro de conectores por tipo (campo "connector" de DATA_SOURCES_REGISTRY.yaml)."""
from .bundesbank import BundesbankConnector
from .ecb_mfi import ECBMFIConnector
from .epc import EPCConnector
from .gleif import GLEIFBicLeiConnector, GLEIFLeiConnector
from .national import BdEMFIConnector, CNBConnector, OeNBConnector
from .schwifty_bundle import SchwiftyBundleConnector

CONNECTORS = {
    "epc": EPCConnector,
    "bundesbank": BundesbankConnector,
    "oenb": OeNBConnector,
    "cnb": CNBConnector,
    "bde_mfi": BdEMFIConnector,
    "ecb_mfi": ECBMFIConnector,
    "gleif_bic_lei": GLEIFBicLeiConnector,
    "gleif_lei": GLEIFLeiConnector,
    "schwifty_bundle": SchwiftyBundleConnector,
}


def make(source_cfg: dict):
    cls = CONNECTORS.get(source_cfg.get("connector"))
    return cls(source_cfg["id"]) if cls else None
