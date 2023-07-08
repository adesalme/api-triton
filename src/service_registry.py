import glob
import importlib
import semver
from services.service_util import ServiceBase
from typing import Union

_registry: dict[str, Union[ServiceBase, "MetaRegistry"]] = {}


def get_registry():
    return _registry


def load_all():
    for file in glob.glob('services/*.py') + glob.glob('services/*/*.py'):
        importlib.import_module(file.replace('.py', '').replace('/', '.'))


def from_class(c):
    return _registry[c.__name__]


def all_from_class(services_list: list):
    return list(map(from_class, services_list))


def from_fully_qualified(fqn):
    service_name, service_version = fqn.split(ServiceBase.VERSION_SEPARATOR)
    return from_name_version(service_name, service_version)


def from_name_version(name, version):
    for _, s in _registry.items():
        version_as_semver = semver.version.Version.parse(version.lstrip('v'))
        if s.name() == name and (s.version_str() == version or version_as_semver == s.version()):
            return s
    raise NotImplementedError


class MetaRegistry(type):
    def __new__(cls, cls_name, bases, attrs):
        new_class = super(cls, MetaRegistry).__new__(cls, cls_name, bases, attrs)
        if new_class.__name__ not in _registry:
            _registry[new_class.__name__] = new_class
        else:
            raise ValueError(f"Duplicated service {new_class.__name__}")
        return new_class
