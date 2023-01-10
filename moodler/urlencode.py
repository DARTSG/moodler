import urllib.parse


def encode(s):
    """
    Encode string.
    """
    return urllib.parse.quote_plus(str(s))


def get_prefix(path, key):
    """
    Get current prefix for the query string.
    """
    return f"{path}[{encode(key)}]" if path else encode(key)


def iterate(obj):
    if isinstance(obj, dict):
        return obj.items()
    return enumerate(obj)


def urlencode(input, path="", delimiter="&"):
    def build(input, path):
        str_list = []
        for key, value in iterate(input):
            if isinstance(value, (list, dict)):
                str_list.extend(build(value, get_prefix(path, key)))
            elif value is not None:
                str_list.append(f"{get_prefix(path, key)}={encode(value)}")
        return str_list

    return delimiter.join(build(input, path))
