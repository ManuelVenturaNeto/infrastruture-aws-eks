import pkgutil

PROCESSES = sorted(module.name for module in pkgutil.iter_modules(__path__))
