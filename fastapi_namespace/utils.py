import string
import secrets

def delete_none(dict_) -> dict:
    return {k: v for k, v in dict_.items() if v is not None}


alphabet = string.ascii_letters
def gen_op_id(length: int = 15) -> str:
    return ''.join(secrets.choice(alphabet) for i in range(length))