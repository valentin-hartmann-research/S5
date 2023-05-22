import requests

SERVER_IP = '0.0.0.0'
SERVER_PORT = 5000
CONFIG_URL = 'http://{}:{}/configure'


def configure_server(private, d, m, num_clients, sum_path, query_vector_path, m_data_type, server_ip, server_port):
    configuration = {'private': private, 'd': d, 'm': m, 'num_clients': num_clients,
                     'sum_path': sum_path, 'query_vector_path': query_vector_path, 'm_data_type': m_data_type}
    r = requests.post(CONFIG_URL.format(server_ip, server_port), data=configuration)
    if not r.text == 'Configuration successful':
        print('Server configuration failed.')
        exit()


if __name__ == '__main__':
    configure_server(True, 1000, 32, 1, '/', 'queries/query0.npy', 'np.int32', SERVER_IP, SERVER_PORT)
