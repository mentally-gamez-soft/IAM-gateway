"""Define a common library for encoding/decoding jwt."""

import logging
import zlib

from itsdangerous import base64_decode, base64_encode

from config.default import ENCODING

logger = logging.getLogger(__name__)


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
    result: str = None
    try:
        result = zlib.decompress(base64_decode(payload)).decode()
    except Exception as exc:
        logger.error("Error when reading the user id => {}".format(exc))

    return result
