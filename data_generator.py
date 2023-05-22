import numpy as np
from numpy import random
import itertools
from pathlib import Path
from experiment_params import  d_list, m_list, n_log_list

random.seed(42)


def generate_seeds(path, n, seed_data_type):
    min_seed = np.iinfo(seed_data_type).min
    max_seed = np.iinfo(seed_data_type).max + 1
    for i in range(n):
        curr_seed = random.randint(min_seed, max_seed, dtype=seed_data_type)
        np.save('{}/seed{}'.format(path, i), curr_seed)


def generate_vectors(client_path, query_path, n, d, m_tilde, m_data_type):
    min_vector_entry = -np.power(2, m_tilde-1)
    max_vector_entry = -min_vector_entry - 1
    vector_sum = np.zeros(d, m_data_type)
    for i in range(n):
        curr_vector = random.randint(min_vector_entry, max_vector_entry, d, dtype=m_data_type)
        np.save('{}/vector{}'.format(client_path, i), curr_vector)
        vector_sum += curr_vector

    curr_vector = random.randint(min_vector_entry, max_vector_entry, d, dtype=m_data_type)
    np.save('{}/query{}'.format(query_path, 0), curr_vector)

    return vector_sum


if __name__ == '__main__':
    for d, m, n_log in itertools.product(d_list, m_list, n_log_list):
        directory = 'd-{}_m-{}_n-{}'.format(d, m, n_log)
        seeds_path = 'data/client_seeds/' + directory
        vectors_path = 'data/client_vectors/' + directory
        queries_path = 'data/queries/' + directory
        for path in (seeds_path, vectors_path, queries_path):
            Path(path).mkdir(parents=True, exist_ok=True)

        n = 2**n_log
        m_tilde = m - n_log
        m_data_type = eval('np.int' + str(m))

        generate_seeds(seeds_path, 2**n_log, np.uint32)
        vector_sum = generate_vectors(vectors_path, queries_path, n, d, m_tilde, m_data_type)
        # We need this for verification to make sure that the sum that the server computes indeed equals the sum of the
        # clients' vectors.
        np.save(vectors_path + '/sum', vector_sum)
