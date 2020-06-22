"""
File with constants
"""
import random

DEFAULT_PORT: int = 6881

# TODO actually generate this?
PEER_ID: bytes = b'-XY0000-' + bytes([random.randint(0, 255) for _ in range(12)]) 

