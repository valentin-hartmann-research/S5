from flask import Flask, make_response, request
import requests
from multiprocessing import Process, Queue
import numpy as np
from numpy import random
from io import BytesIO
import logging
from misc import *
import time

LOGGING = False
BIT_SHIFT_AMOUNT = np.uint64(32)


def create_app():
    app = Flask(__name__)

    if not LOGGING:
        app.logger.disabled = True
        log = logging.getLogger('werkzeug')
        log.disabled = True

    # TODO: Is there a better way to do this?
    # Declare variables that will be set in configure().
    seeds_data_type = False
    num_clients = False
    num_summands = False
    m_data_type = False
    query_vector = False
    sum_path = False
    client_urls = False
    min_int = False
    max_int = False
    d = False

    # https://stackoverflow.com/questions/11515944/how-to-use-multiprocessing-queue-in-python
    vector_summation_queue = Queue()
    # We need this to signal to another thread that the time counting should start. Counting across threads (start the counter in one thread, evaluate it in the other) doesn't seem to work.
    all_clients_registered_queue = Queue()

    @app.route('/configure', methods=['GET', 'POST'])
    def configure():
        nonlocal seeds_data_type, num_summands, num_clients, m_data_type, sum_path, min_int, max_int,\
            client_urls, d, query_vector

        req_data = request.form
        private = True if req_data['private'] == 'True' else False
        d = int(req_data['d'])
        m = int(req_data['m'])
        num_clients = int(req_data['num_clients'])
        sum_path = req_data['sum_path']
        query_vector = np.load(req_data['query_vector_path'])
        m_data_type = eval(req_data['m_data_type'])

        if private:
            K = compute_K(d, m)
            # K seeds per client and one noisy vector.
            num_summands = num_clients * (K + 1)
            seeds_data_type = compute_seeds_config(K)[1]
        else:
            num_summands = num_clients
        min_int = np.iinfo(m_data_type).min
        max_int = np.iinfo(m_data_type).max

        client_urls = set()

        p = Process(target=add_vector, args=(vector_summation_queue, d, m_data_type))
        p.start()

        return 'Configuration successful'

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        nonlocal client_urls, all_clients_registered_queue

        req_data = request.form
        # The URL via which to contact the client.
        client_url = req_data['url']
        client_urls.add(client_url)

        if len(client_urls) == num_clients:
            all_clients_registered_queue.put(True)
            print('Starting summation process')
            # We do this in a different process because otherwise the current client won't get a response before all
            # summands have been collected.
            p = Process(target=request_summands)
            p.start()

        response = make_response('Successfully registered', 200)
        response.mimetype = "text/plain"
        return response

    def request_summands():
        query_file = BytesIO()
        np.save(query_file, query_vector)
        query_file.seek(0)
        for url in client_urls:
            # When a client can send different vector, add something like data={'query': <query content>}
            requests.post(url, files={'query': query_file})
        query_file.close()

    @app.route('/send_vector', methods=['GET', 'POST'])
    def send_vector():
        vector_data_dict = request.files
        # vector_data_dict only contains one item.
        # multiprocessing closes file handles that are passed to child processes, hence we need to do the reading from
        # the files here.
        # https://stackoverflow.com/questions/14899355/python-multiprocessing-valueerror-i-o-operation-on-closed-file
        for key, file in vector_data_dict.items():
            if key == 'seed':
                vector_data = (key, int.from_bytes(file.read(), 'big'))
            else:
                vector_data = (key, np.load(file, allow_pickle=True))
        vector_summation_queue.put(vector_data)
        return 'Received vector.'

    def add_vector(queue, d, datatype):
        summed_vector = np.zeros(d, datatype)

        num_summands_collected = 0
        while True:
            vector_data = queue.get()
            num_summands_collected += 1
            if vector_data[0] == 'seed':
                # Minus, because we need to subtract the noise that was added by the client.
                to_add = -add_from_seed(vector_data[1])
            else:
                to_add = add_directly(vector_data[1])

            summed_vector += to_add

            if num_summands_collected == num_summands:
                np.save(sum_path, summed_vector)

                print('Done')
                break

    def add_directly(to_add_vector):
        return to_add_vector

    def add_from_seed(to_add_seed):
        if seeds_data_type == np.uint64:
            to_add_seed = np.uint64(to_add_seed)
            # Because the seed can only be a 32 bit uint or an array of 32 bit uints.
            # https://stackoverflow.com/questions/30513741/python-bit-shifting-with-numpy
            seed_first = to_add_seed >> BIT_SHIFT_AMOUNT
            seed_second = (to_add_seed << BIT_SHIFT_AMOUNT) >> BIT_SHIFT_AMOUNT
            random.seed((int(seed_first), int(seed_second)))
        else:
            random.seed(to_add_seed)
        return random.randint(min_int, max_int + 1, d, dtype=m_data_type)

    return app
