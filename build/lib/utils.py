def delete_none(dict_) -> dict:
    return {k: v for k, v in dict_.items() if v is not None}
