"""Central registry for feature modules."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class ModuleSpec:
    key: str
    label: str
    description: str


class ModuleRegistry:
    def __init__(self) -> None:
        self._modules: Dict[str, ModuleSpec] = {}

    def register(self, module: ModuleSpec) -> None:
        self._modules[module.key] = module

    def list_modules(self) -> Dict[str, ModuleSpec]:
        return dict(self._modules)
