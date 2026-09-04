# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

"""Pure-Python domain core for the clean-room RadioTV add-on."""

from .catalog_service import CatalogDataError, StationCatalog, normalize_text
from .entities import CatalogMetadata, Station, Verification
from .persistence import PersistenceError, StateStore, UserState

__all__ = (
    "CatalogDataError",
    "CatalogMetadata",
    "PersistenceError",
    "StateStore",
    "Station",
    "StationCatalog",
    "UserState",
    "Verification",
    "normalize_text",
)
