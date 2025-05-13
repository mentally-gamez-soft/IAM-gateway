"""Define a common library for encoding/decoding jwt."""

import zlib

from itsdangerous import base64_decode, base64_encode

from config.default import ENCODING


def encode_as_base64(payload: str) -> bytes:
    """Encode the payloads.

    Args:
        payload (str): the message to encode.

    Returns:
        bytes: the encoded message.
    """
    return base64_encode(zlib.compress(payload.encode(ENCODING))).decode()


def decode_as_base64(payload: str) -> bytes:
    """Decode the payloads.

    Args:
        payload (str): The message to decode.

    Returns:
        bytes:  the decoded message.
    """
    return zlib.decompress(base64_decode(payload)).decode()
