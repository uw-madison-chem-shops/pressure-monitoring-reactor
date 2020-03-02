__all__ = ["GasUptakeDirector"]

import asyncio
from typing import Dict, Any

from yaqd_core import Base, logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class GasUptakeDirector(Base):
    _kind = "gas-uptake-director"
    defaults: Dict[str, Any] = {}

    def __init__(self, name, config, config_filepath):
        super().__init__(name, config, config_filepath)
        # Perform any unique initialization

    def begin_recording(self):
        return "hi"
