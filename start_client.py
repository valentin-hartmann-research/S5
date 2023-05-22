from client_app import create_app
import requests
# Also needed for the eval.
import numpy as np
import sys
from multiprocessing import Process, Queue

CLIENT_IP = '0.0.0.0'


def register(server_base_url, own_port):
    server_url = '{}/register'.format(server_base_url)
    own_url = 'http://{}:{}/{}'.format(CLIENT_IP, own_port, 'request_vector')
    req = requests.post(server_url, data={'url': own_url})
    if not req.text == 'Successfully registered':
        print('Client could not register.')
        exit()


if __name__ == '__main__':
    app_args = {}
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
        # If the clients run on the same machine, each client needs to use a different port.
        client_port = int(sys.argv[2])
        # The seed that the client is initialized with. NOT the random seeds used for generating the random vectors.
        client_seed = np.load(sys.argv[3])
        true_vector = np.load(sys.argv[4])
        # TODO: Having both m and m_data_type is redundant. We would either only have m (the most flexible solution) or
        #  only m_data_type (easier to implement, and what we do now).
        m = int(sys.argv[5])
        m_data_type = type(true_vector[0])
        d = len(true_vector)
        private = True if sys.argv[6] == 'private' else False

        finished_queue = Queue()
        app = create_app(server_url=server_url, client_seed=client_seed, true_vector=true_vector, m=m,
                         m_data_type=m_data_type, d=d, private=private, finished_queue=finished_queue)
    else:
        print('Need to provide CL args.')
        exit()

    app_process = Process(target=app.run, kwargs={'host':CLIENT_IP, 'port':client_port})
    app_process.start()
    register(server_url, client_port)

    finished_queue.get()
    app_process.terminate()
    app_process.join()
