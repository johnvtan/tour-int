from typing import List, Any, Tuple, Dict

DIGITS: List[str] = set([str(i) for i in range(10)] + ['-'])

def assert_idx_in_string(bstring: str, idx: int):
    if idx >= len(bstring):
        raise ValueError('String ended unexpectedly')

def parse_int(bstring: str, idx: int, terminal_char: str) -> Tuple[int, int]:
    assert_idx_in_string(bstring, idx)

    int_token = []
    while bstring[idx] != terminal_char:
        if bstring[idx] not in DIGITS:
            raise ValueError('bencode.parse_int string contains bad character')
        int_token.append(bstring[idx])
        idx += 1
        assert_idx_in_string(bstring, idx)

    if not int_token:
        raise ValueError('bencode.parse_int string contained no digits')

    return int(''.join(int_token)), idx+1

def decode_int(bstring: str, idx: int) -> Tuple[int, int]:
    assert_idx_in_string(bstring, idx)

    if bstring[idx] != 'i':
        raise ValueError('bencode.decode_int string doesn\'t start with "i"')
    
    idx += 1
    return parse_int(bstring, idx, 'e')

def decode_string(bstring: str, idx: int) -> Tuple[str, int]:
    assert_idx_in_string(bstring, idx)
    string_length, idx = parse_int(bstring, idx, ':') 

    if string_length < 0:
        raise ValueError('bencode.decode_string called with negative length')

    assert_idx_in_string(bstring, string_length + idx - 1)

    return bstring[idx : (idx + string_length)], idx + string_length

def decode_list(bstring: str, idx: int) -> Tuple[List, int]:
    assert_idx_in_string(bstring, idx)

    if bstring[idx] != 'l':
        raise ValueError('bencode.decode_list string doesn\'t start with "l"')

    idx += 1
    ret_list = []

    while bstring[idx] != 'e':
        r, idx = decode_any(bstring, idx)
        ret_list.append(r)
        assert_idx_in_string(bstring, idx)

    return ret_list, idx+1

def decode_dict(bstring: str, idx: int) -> Tuple[Dict, int]:
    assert_idx_in_string(bstring, idx)

    if bstring[idx] != 'd':
        raise ValueError('bencode.decode_dict string doesn\'t start with "d"')

    idx += 1
    ret_dict: Dict = {}

    while bstring[idx] != 'e':
        key, idx = decode_string(bstring, idx)
        assert_idx_in_string(bstring, idx)

        value, idx = decode_any(bstring, idx)
        assert_idx_in_string(bstring, idx)

        ret_dict[key] = value 

    return ret_dict, idx+1

def decode_any(bstring: str, idx: int) -> Tuple[Any, int]:
    if bstring[idx] == 'i':
        return decode_int(bstring, idx)
    elif bstring[idx] == 'l':
        return decode_list(bstring, idx)
    elif bstring[idx] == 'd':
        return decode_dict(bstring, idx)
    else:
        return decode_string(bstring, idx)

def decode(bstring: str) -> Any:
    """Decodes a bencoded string into a Python object"""
    ret, _ = decode_any(bstring, 0)
    return ret


