"""Small configuration fixture."""


def load_config(defaults, overrides):
    return {**defaults, **overrides}


def require_key(config, name):
    if name not in config:
        raise KeyError(name)
    return config[name]
