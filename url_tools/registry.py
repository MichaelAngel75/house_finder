from __future__ import annotations

from .base import PropertyUrlResolver
from .generic_resolver import GenericResolver
from .immuebles24_resolver import Immuebles24Resolver
from .lamudi_resolver import LamudiResolver
from .propiedades_resolver import PropiedadesResolver


RESOLVERS: list[PropertyUrlResolver] = [
    Immuebles24Resolver(),
    LamudiResolver(),
    PropiedadesResolver(),
    GenericResolver(),
]


def get_resolver(url: str) -> PropertyUrlResolver:
    for resolver in RESOLVERS:
        if resolver.can_handle(url):
            return resolver

    return GenericResolver()