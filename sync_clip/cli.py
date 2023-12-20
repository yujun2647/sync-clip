import argparse
from sync_clip import __version__

from sync_clip.remote.server import server
from sync_clip.monitor import monitor

parser = argparse.ArgumentParser()

parser.add_argument(
    "-t", "--start-type",
    help="choose the type, client or server, default: client",
    default="client", type=str)
parser.add_argument("-sh", "--server-host",
                    help="choose server host the client is going to connect",
                    default="0.0.0.0", type=str)
parser.add_argument("-sp", "--server-port",
                    help="choose the port of the server, default: 12364",
                    default=12364, type=int)

parser.version = str(__version__)
parser.add_argument('-v', action='version', help='print the version and exit')

args = parser.parse_args()


def main():
    start_type = args.start_type.lower()
    host, port = args.server_host, args.server_port
    if start_type == "client":
        monitor(host, port)
    elif start_type == "server":
        server(port)
    else:
        print(f"invalid type: {start_type}, please assign 'server' or client")


if __name__ == "__main__":
    main()
