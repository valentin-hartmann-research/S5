from flask import Flask, make_response
import requests
import numpy as np
from numpy import random
from multiprocessing import Process, Queue
from io import BytesIO
import logging
from misc import *

LOGGING = False


def create_app(server_url, client_seed, true_vector, m, m_data_type, d, private, finished_queue):
    random.seed(client_seed)
    if private:
        K = compute_K(d, m)
        num_seed_bits, seeds_data_type = compute_seeds_config(K)
    else:
        K = 0
    min_noise = np.iinfo(m_data_type).min
    max_noise = np.iinfo(m_data_type).max

    app = Flask(__name__)

    if not LOGGING:
        app.logger.disabled = True
        log = logging.getLogger('werkzeug')
        log.disabled = True

    @app.route('/request_vector', methods=['GET', 'POST'])
    def request_vector():
        # Check here what data was requested. But for now each client only has one vector anyway.

        to_send_queue = Queue()
        process_send = Process(target=send_vectors, args=(to_send_queue,))
        process_send.start()
        process_generate = Process(target=generate_vectors, args=(to_send_queue,))
        process_generate.start()

        response = make_response('Vector and noise are about to be sent.', 200)
        response.mimetype = "text/plain"
        return response

    def send_vectors(to_send_queue):
        url = '{}/{}'.format(server_url, 'send_vector')

        num_vectors_sent = 0
        while True:
            curr_to_send = to_send_queue.get()
            seed_or_vector = curr_to_send[0]  # str
            payload = curr_to_send[1]
            to_send_file = BytesIO()

            if seed_or_vector == 'seed':
                payload_bytes = payload.to_bytes((payload.bit_length() + 7) // 8, 'big')
                to_send_file.write(payload_bytes)
            else:
                np.save(to_send_file, payload)

            # https://stackoverflow.com/questions/55301037/save-and-send-large-numpy-arrays-with-flask
            to_send_file.seek(0)
            requests.post(url=url, files={seed_or_vector: to_send_file})
            to_send_file.close()

            num_vectors_sent += 1
            # +1 because all K seeds and the vector are sent.
            if num_vectors_sent == K + 1:
                print('Done')
                finished_queue.put('Done')
                break

    def generate_vectors(to_send_queue):
        noisy_vector = true_vector
        if private:
            generated_seeds = random.randint(0, 2 ** num_seed_bits, size=K, dtype=seeds_data_type)
            long_seed = False
            if seeds_data_type == np.uint64:
                # Because the seed can only be a 32 bit uint or an array of 32 bit uints.
                long_seed = True
                seeds_first = generated_seeds >> 32
                seeds_second = (generated_seeds << 32) >> 32
            for i in range(len(generated_seeds)):
                generated_seed = generated_seeds[i]
                to_send_queue.put(('seed', int(generated_seed)))
                if long_seed:
                    random.seed((int(seeds_first[i]), int(seeds_second[i])))
                else:
                    random.seed(generated_seed)
                noise = random.randint(min_noise, max_noise + 1, d, dtype=m_data_type)
                # We implement the modulo operation by simply letting the numbers over-/underflow.
                noisy_vector += noise
        to_send_queue.put(('vector', noisy_vector))

    return app
