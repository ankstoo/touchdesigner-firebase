import pyrebase
from pythonosc import udp_client
from pythonosc import dispatcher
from pythonosc import osc_server

from threading import Thread
import signal
import sys
import json


config = None

firebase = None
firebase_stream = None
firebase_thread = None

osc_udp_client = None
osc_thread = None
osc_udp_server = None

values_cache = dict()


def prepare_value(value):
    try:
        float_value = float(value)
        return float_value
    except ValueError:
        return value


def build_path(root, path):
    prepared_root = root
    if not prepared_root.startswith("/"):
        prepared_root = "/" + prepared_root
    if not prepared_root.endswith("/"):
        prepared_root = prepared_root + "/"

    prepared_path = path
    if prepared_path.startswith("/"):
        prepared_path = prepared_path[1:]

    result = prepared_root + prepared_path
    return result


def notify_osc(path, value):
    if isinstance(value, dict):
        for child_name, child_value in value.items():
            child_path = path
            if not child_path.endswith("/"):
                child_path = child_path + "/"
            child_path = child_path + child_name
            notify_osc(child_path, child_value)
    else:
        prepared_path = build_path(root=config["path"], path=path)
        prepared_value = prepare_value(value)
        print(">>> Osc out: ", prepared_path, " = ", prepared_value)
        values_cache[prepared_path] = prepared_value
        osc_udp_client.send_message(prepared_path, prepared_value)


def stream_handler(message):
    path = message["path"]
    data = message["data"]
    if data is None:
        return

    print("<<< Firebase in: ", path, " = ", data)
    notify_osc(path=path, value=data)


def handle_firebase():
    global firebase
    firebase = pyrebase.initialize_app(config["firebase"])

    global firebase_stream
    db = firebase.database()
    firebase_stream = db.child(config["path"]).stream(stream_handler)


def osc_message_handler(path, *values):
    prepared_value = prepare_value(values[0])
    prepared_path = path
    if prepared_path.endswith("/"):
        prepared_path = prepared_path[:-1]

    global values_cache
    if prepared_path in values_cache:
        if values_cache[prepared_path] == prepared_value:
            return
    values_cache[prepared_path] = prepared_value

    print("<<< Osc in: ", path, " = ", values)
    if path.startswith("/_"):
        return

    print(">>> Firebase out: ", prepared_path, " = ", prepared_value)

    db = firebase.database()
    db.update({prepared_path: prepared_value})

    pass


def handle_osc():
    global osc_udp_client
    osc_udp_client = udp_client.SimpleUDPClient(config["osc"]["sendToHost"], config["osc"]["sendToPort"])

    disp = dispatcher.Dispatcher()
    disp.map(config["path"] + "*", osc_message_handler)

    global osc_udp_server
    osc_udp_server = osc_server.BlockingOSCUDPServer(
        server_address=(config["osc"]["receiveFromHost"], config["osc"]["receiveFromPort"]),
        dispatcher=disp)
    osc_udp_server.serve_forever()


def handle_signals(sig, frame):
    print('You pressed Ctrl+C!')

    firebase_stream.close()
    osc_udp_server.shutdown()

    firebase_thread.join(timeout=2)
    osc_thread.join(timeout=2)

    sys.exit(0)


def main():
    global config
    with open('config.json') as f:
        config = json.load(f)

    global firebase_thread
    firebase_thread = Thread(target=handle_firebase)
    firebase_thread.start()

    global osc_thread
    osc_thread = Thread(target=handle_osc)
    osc_thread.start()

    signal.signal(signal.SIGINT, handle_signals)
    signal.pause()


if __name__ == "__main__":
    main()
