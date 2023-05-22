from server_app import create_app

SERVER_IP = '0.0.0.0'
SERVER_PORT = 5000

if __name__ == '__main__':
    app = create_app()
    app.run(host=SERVER_IP, port=SERVER_PORT)