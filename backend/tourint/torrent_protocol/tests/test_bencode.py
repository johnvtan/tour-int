import unittest
from bencode import *

class BencodeDecodeTests(unittest.TestCase):
    def test_decode_int(self):
        self.assertEqual(decode_int(b'i123e', 0), (123, 5))
        self.assertEqual(decode_int(b'i-123e', 0), (-123, 6))

        self.assertEqual(decode_int(b'i0e', 0), (0, 3))

        self.assertRaises(ValueError, decode_int, b'd456e', 0)
        self.assertRaises(ValueError, decode_int, b'i1234', 0)
        self.assertRaises(ValueError, decode_int, b'i12b3', 0)
        self.assertRaises(ValueError, decode_int, b'i123e', 5)
        self.assertRaises(ValueError, decode_int, b'i1-23e', 5)
        self.assertRaises(ValueError, decode_int, b'ie', 0)

    def test_decode_string(self):
        self.assertEqual(decode_string(b'5:hello', 0), ('hello', 7))
        self.assertEqual(decode_string(b'0:', 0), ('', 2))
        self.assertEqual(decode_string(b'6:a&C2e!', 0), ('a&C2e!', 8))
        self.assertEqual(decode_string(b'3:123', 0), ('123', 5))

        self.assertRaises(ValueError, decode_string, b'abc', 0)
        self.assertRaises(ValueError, decode_string, b':abc', 0)
        self.assertRaises(ValueError, decode_string, b'-1:abc', 0)
        self.assertRaises(ValueError, decode_string, b'4:abc', 0)
        self.assertRaises(ValueError, decode_string, b'3:abc', 4)

    def test_decode_list(self):
        self.assertEqual(decode_list(b'li123ee', 0), ([123], 7))
        self.assertEqual(decode_list(b'ld1:a1:bei1ee', 0), ([{'a': 'b'}, 1], 13))
        self.assertEqual(decode_list(b'li123e4:abc!e', 0), ([123, 'abc!'], 13))
        self.assertEqual(decode_list(b'li123eli23ei13ee4:abc!e', 0), ([123, [23, 13], 'abc!'], 23))
        self.assertRaises(ValueError, decode_list, b'li123eli23ei13ee4:abc!', 0)
        self.assertRaises(ValueError, decode_list, b'li123eli23ei13ee5:abc!e', 0)
        self.assertRaises(ValueError, decode_list, b'd2:abi2ee', 0)

    def test_decode_dict(self):
        self.assertEqual(decode_dict(b'd1:ai123ee', 0), ({'a': 123}, 10))
        self.assertEqual(decode_dict(b'd1:ad1:b1:cee', 0), ({'a': {'b': 'c'}}, 13))
        self.assertEqual(decode_dict(b'd1:ali2ei3ee1:bi23ee', 0), ({'a': [2, 3], 'b': 23}, 20))
        self.assertEqual(decode_dict(b'de', 0), ({}, 2))

        self.assertRaises(ValueError, decode_dict, b'di12ei23ee', 0)
        self.assertRaises(ValueError, decode_dict, b'dd1:a1:bee', 0)
        self.assertRaises(ValueError, decode_dict, b'i123e', 0)

class BencodeEncodeTests(unittest.TestCase):
    def test_encode_int(self):
        self.assertEqual(encode_int(123), b'i123e')
        self.assertEqual(encode_int(-123), b'i-123e')
        self.assertEqual(encode_int(0), b'i0e')

    def test_encode_string(self):
        self.assertEqual(encode_string('hello'), b'5:hello')
        self.assertEqual(encode_string(''), b'0:')

    def test_encode_list(self):
        self.assertEqual(encode_list(['a']), b'l1:ae')
        self.assertEqual(encode_list(['a', 123]), b'l1:ai123ee')
        self.assertEqual(encode_list(['a', ['b', -1], 3]), b'l1:al1:bi-1eei3ee')

    def test_encode_dict(self):
        self.assertEqual(encode_dict({'a':'b'}), b'd1:a1:be')
        self.assertEqual(encode_dict({
            'a': [1,-2],
            'b': {'c': 'd'},
            'c': 'd'
            }), b'd1:ali1ei-2ee1:bd1:c1:de1:c1:de')

        self.assertRaises(TypeError, encode_dict, {1: 'b'})

