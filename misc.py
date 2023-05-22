import math
import numpy as np

INVERSE_COLLISION_PROBABILITY = 10**10


def compute_K(d, m):
    K = int(math.ceil(d * m / 2))
    return K


def compute_seeds_config(K):
    num_seed_bits = math.ceil(math.log(2 * K * (2 * K - 1) * 2 * INVERSE_COLLISION_PROBABILITY))
    if num_seed_bits > 64:
        # TODO: Generate seeds with Python's int generator in this case.
        raise ValueError('Seeds with more than 64 bits are currently not supported.')
    elif num_seed_bits > 32:
        seeds_data_type = np.uint64
    elif num_seed_bits > 16:
        seeds_data_type = np.uint32
    elif num_seed_bits > 8:
        seeds_data_type = np.uint16
    elif num_seed_bits > 0:
        seeds_data_type = np.uint8
    else:
        raise ValueError('Seeds are between 0 and max_seed, hence max_seed needs to be non-negative.')

    return num_seed_bits, seeds_data_type
