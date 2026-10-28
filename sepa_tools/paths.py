"""Rutas del proyecto (todas relativas a la raíz del repositorio)."""
import os

ROOT = os.environ.get("SEPA_TOOLS_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFERENCE_DIR = os.path.join(ROOT, "reference")
REGISTRY_FILE = os.environ.get("SEPA_TOOLS_REGISTRY") or os.path.join(ROOT, "DATA_SOURCES_REGISTRY.yaml")
DATA_DIR = os.path.join(ROOT, "data", "v2")          # datos públicos publicados
STATE_DIR = os.path.join(ROOT, "state")              # estado de sincronización (versionado)
SNAPSHOT_DIR = os.path.join(STATE_DIR, "snapshots")  # observaciones normalizadas por fuente publicable
CACHE_DIR = os.environ.get("SEPA_TOOLS_CACHE") or os.path.join(ROOT, ".cache", "raw")  # no versionado
LEGACY_PARTICIPANTS = os.path.join(ROOT, "participants.json")
LEGACY_CHANGES = os.path.join(ROOT, "changes.json")
LEGACY_STATUS = os.path.join(ROOT, "status.json")
