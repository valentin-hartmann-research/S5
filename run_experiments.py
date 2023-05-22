from experiment_params import d_list, m_list, n_log_list, private_list, SERVER_IP, SERVER_PORT
from pathlib import Path
import shlex
from subprocess import Popen, PIPE
import itertools
from server_config import configure_server
# Also for the eval.
import numpy as np
from time import sleep
import shutil
from getpass import getpass
import time

GUNICORN_PATH = '/home/USERNAME/.conda/envs/ENVIRONMENT/bin/gunicorn'
# When traffic gets captured at the same time, breaks are needed to later know when one experiment ended and the next
# one began.
TRAFFIC_CAPTURE_BREAKS = False


if __name__ == '__main__':
    server_url = 'http://{}:{}'.format(SERVER_IP, SERVER_PORT)
    wall_clock_times_path = 'results/wall_clock_times'
    temp_path = 'results/temp'
    for path in (wall_clock_times_path, temp_path):
        Path(path).mkdir(parents=True, exist_ok=True)
    server_sum_path = temp_path + '/sum'

    start_server_cmd = 'taskset -c 0 {} --bind={}:{} "server_app:create_app()"'.format(
    GUNICORN_PATH, SERVER_IP, SERVER_PORT)
    server_process = Popen(shlex.split(start_server_cmd), stdout=PIPE)
    server_stdout = server_process.stdout
    # TODO: Do this more elegantly and make it robust.
    # Wait for the server to start.
    sleep(2)

    def run_experiment_instance(d, m, private, n_log):
        n = 2**n_log
        m_data_type_str = 'np.int' + str(m)
        private_bool = True if private == 'private' else False
        directory_and_file_name = 'd-{}_m-{}_n-{}'.format(d, m, n_log)
        seeds_path = 'data/client_seeds/' + directory_and_file_name
        vectors_path = 'data/client_vectors/' + directory_and_file_name
        curr_true_sum_path = vectors_path + '/sum.npy'
        curr_query_path = 'data/queries/' + directory_and_file_name + '/query0.npy'
        curr_wall_clock_time_path = '{}/{}_{}.txt'.format(wall_clock_times_path, directory_and_file_name, private)

        configure_server(private_bool, d, m, n, server_sum_path, curr_query_path, m_data_type_str,
                         SERVER_IP, SERVER_PORT)

        for client_id in range(n):
            curr_client_port = 5001 + client_id
            curr_seed_path = seeds_path + '/seed{}.npy'.format(client_id)
            curr_vector_path = vectors_path + '/vector{}.npy'.format(client_id)
            start_client_cmd = 'taskset -c 1-47 python start_client.py {} {} {} {} {} {}' \
                .format(server_url, curr_client_port, curr_seed_path, curr_vector_path, m, private)
            Popen(shlex.split(start_client_cmd))

        while True:
            if server_stdout.readline() == b'Starting summation process\n':
                start_time = time.perf_counter_ns()
                break

        while True:
            if server_stdout.readline() == b'Done\n':
                elapsed_time = time.perf_counter_ns() - start_time
                with open(curr_wall_clock_time_path, 'w') as runtime_file:
                    runtime_file.write(str(elapsed_time))
                break

        server_sum = np.load(server_sum_path + '.npy')
        true_sum = np.load(curr_true_sum_path)
        if not np.array_equal(server_sum, true_sum):
            server_process.terminate()
            shutil.rmtree(temp_path)
            raise RuntimeError('The server didn\'t compute the correct sum')

    # Warm-up run
    # run_experiment_instance(100, 32, 'private', 3)
    for d, m, private, n_log in itertools.product(d_list, m_list, private_list, n_log_list):
        time.sleep(30)
        run_experiment_instance(d, m, private, n_log)

    server_process.terminate()
    shutil.rmtree(temp_path)
