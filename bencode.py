from typing import List, Any, Tuple, Dict

DIGITS_RANGE: Tuple[int, int] = (b'0'[0], b'9'[0])
NEG_DIGIT: int = b'-'[0]

DICT_DELIMITER: int = b'd'[0]
LIST_DELIMITER: int = b'l'[0]
INT_DELIMITER: int = b'i'[0]
END_DELIMITER: int = b'e'[0]
STRING_SIZE_DELIMITER: int = b':'[0]

def assert_idx_in_string(bstring: bytes, idx: int):
    if idx >= len(bstring):
        raise ValueError('String ended unexpectedly')

def byte_to_digit(b: int) -> int:
    if b < DIGITS_RANGE[0] or b > DIGITS_RANGE[1]:
        raise ValueError('bencode.byte_to_digit: Given byte is not an encoded digit')
    return b - DIGITS_RANGE[0]

def digits_to_bytes(n: int) -> List[int]:
    if n == 0:
        return [DIGITS_RANGE[0]]

    neg: bool = False
    if n < 0:
        neg = True
        n *= -1

    digit_bytes = []
    while n > 0:
        next_byte = (n % 10) + DIGITS_RANGE[0]
        digit_bytes.append(next_byte)
        n //= 10

    if neg:
        digit_bytes.append(NEG_DIGIT)

    # TODO endianess?
    digit_bytes.reverse()
    return digit_bytes

def parse_int(bstring: bytes, idx: int, terminal_char: int) -> Tuple[int, int]:
    assert_idx_in_string(bstring, idx)

    mult: int = 1
    if bstring[idx] == NEG_DIGIT:
        mult = -1
        idx += 1
        assert_idx_in_string(bstring, idx)

    int_token = None
    while bstring[idx] != terminal_char:
        if int_token is None:
            int_token = 0
        int_token *= 10
        int_token += byte_to_digit(bstring[idx]) 
        idx += 1
        assert_idx_in_string(bstring, idx)

    if int_token is None:
        raise ValueError('bencode.parse_int no digits found in integer string?')

    return mult * int_token, idx+1

def decode_int(bstring: bytes, idx: int) -> Tuple[int, int]:
    assert_idx_in_string(bstring, idx)

    if bstring[idx] != INT_DELIMITER:
        raise ValueError('bencode.decode_int string doesn\'t start with "i"')
    
    idx += 1
    return parse_int(bstring, idx, END_DELIMITER)

def decode_string(bstring: bytes, idx: int) -> Tuple[str, int]:
    assert_idx_in_string(bstring, idx)
    string_length, idx = parse_int(bstring, idx, STRING_SIZE_DELIMITER) 

    if string_length < 0:
        raise ValueError('bencode.decode_string called with negative length')

    assert_idx_in_string(bstring, string_length + idx - 1)

    # Attempt to decode into a Python string. If it fails, just leave it as bytes.
    try:
        ret_string = bstring[idx : (idx + string_length)].decode('ascii')
    except UnicodeDecodeError:
        ret_string = bstring[idx : (idx + string_length)]

    return ret_string, idx + string_length

def decode_list(bstring: bytes, idx: int) -> Tuple[List, int]:
    assert_idx_in_string(bstring, idx)

    if bstring[idx] != LIST_DELIMITER:
        raise ValueError('bencode.decode_list string doesn\'t start with "l"')

    idx += 1
    ret_list = []

    while bstring[idx] != END_DELIMITER:
        r, idx = decode_any(bstring, idx)
        ret_list.append(r)
        assert_idx_in_string(bstring, idx)

    return ret_list, idx+1

def decode_dict(bstring: bytes, idx: int) -> Tuple[Dict, int]:
    assert_idx_in_string(bstring, idx)

    if bstring[idx] != DICT_DELIMITER:
        raise ValueError('bencode.decode_dict string doesn\'t start with "d"')

    idx += 1
    ret_dict: Dict = {}

    while bstring[idx] != END_DELIMITER:
        key, idx = decode_string(bstring, idx)
        assert_idx_in_string(bstring, idx)

        value, idx = decode_any(bstring, idx)
        assert_idx_in_string(bstring, idx)

        ret_dict[key] = value 

    return ret_dict, idx+1

def decode_any(bstring: bytes, idx: int) -> Tuple[Any, int]:
    if bstring[idx] == INT_DELIMITER:
        return decode_int(bstring, idx)
    elif bstring[idx] == LIST_DELIMITER:
        return decode_list(bstring, idx)
    elif bstring[idx] == DICT_DELIMITER:
        return decode_dict(bstring, idx)
    else:
        return decode_string(bstring, idx)

def encode_int(n: int) -> bytes:
    return bytes([INT_DELIMITER] + digits_to_bytes(n) + [END_DELIMITER])

def encode_string(s: str) -> bytes:
    return bytes(digits_to_bytes(len(s)) + [STRING_SIZE_DELIMITER]) + s.encode('ascii')

def encode_list(lst: List) -> bytes:
    ret_tokens: bytearray = bytearray() 
    ret_tokens.append(LIST_DELIMITER)

    for item in lst:
        ret_tokens.extend(encode(item))

    ret_tokens.append(END_DELIMITER)
    return bytes(ret_tokens)

def encode_dict(d: Dict) -> bytes:
    ret_tokens: bytearray = bytearray()
    ret_tokens.append(DICT_DELIMITER)

    for key, val in d.items():
        if not isinstance(key, str):
            raise TypeError('bencode.encode_dict: key must be a string')
        ret_tokens.extend(encode_string(key))
        ret_tokens.extend(encode(val))

    ret_tokens.append(END_DELIMITER)
    return bytes(ret_tokens)

def encode(obj: Any) -> bytes:
    """Encodes some Python object (int, str, list, dict) to a bencoded string"""
    if isinstance(obj, int):
        return encode_int(obj)
    elif isinstance(obj, str):
        return encode_string(obj)
    elif isinstance(obj, list):
        return encode_list(obj)
    elif isinstance(obj, dict):
        return encode_dict(obj)

    raise TypeError('bencode.encode parameter must be one of (int, str, list dict)')

def decode(bstring: bytes) -> Any:
    """Decodes a bencoded string into a Python object"""
    ret, _ = decode_any(bstring, 0)
    return ret


