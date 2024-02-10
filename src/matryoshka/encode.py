import random
from logging import getLogger

from .dolls import dolls_registry

logger = getLogger(__name__)


def encode(secret: bytes):
    layers = [random.choice(dolls)() for dolls in dolls_registry]
    random.shuffle(layers)
    swap_count = 0
    while swap_count < 10:
        logger.debug(
            "chaining layers=%s, swap_count=%s",
            [layers.__class__.__name__ for layers in layers],
            swap_count,
        )
        layer_results: list[bytes] = []
        current_round, round_secret = 0, secret
        for round, layer in enumerate(layers):
            if not layer.accept_size(len(round_secret)):
                break
            current_round = round
            round_secret = layer.encode(round_secret)
            layer_results.append(round_secret)
        # if layer did not accept the size, swap the layers
        if current_round < len(layers) - 1:
            layers[current_round + 1], layers[current_round] = (
                layers[current_round],
                layers[current_round + 1],
            )
            swap_count += 1
            continue
        # if all layers accepted the size, do validation for decoding
        validate_secret = round_secret
        for round, layer in reversed([*enumerate(layers)]):
            try:
                validate_secret = layer.decode(validate_secret)
            except Exception as e:
                logger.warning("chain layer=%s, round=%s, failed=%s", layer, round, e)
                validate_secret = None
                break
        if validate_secret == secret:
            return round_secret
        logger.warning(
            "chain validation failed, expected=%s, got=%s",
            secret,
            validate_secret,
        )
        break
    return
