from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import threading
import time
import requests
import sys

app = Flask(__name__)
nodes = {}  # Node ID mapped to {last_seen: datetime, address: str}


def log_message(message):
    print(message)
    sys.stdout.flush()


def check_inactive_nodes():
    global initial_nodes_handled
    if not initial_nodes_handled:
        initial_nodes()
        initial_nodes_handled = True
    while True:
        time.sleep(30)  # Periodic check
        current_time = datetime.now()
        to_remove = []
        with threading.Lock():
            if not nodes:
                log_message("No nodes registered yet.")
                continue
            for node, info in list(nodes.items()):
                if current_time - info['last_seen'] > timedelta(seconds=30):
                    to_remove.append(node)
            for node in to_remove:
                del nodes[node]
                log_message(f"Detected inactive node: {node}. Triggering notification to active nodes.")
            if to_remove:
                notify_nodes_of_change()


def notify_nodes_of_change():
    items = list(nodes.items())
    for node, info in items:
        try:
            requests.post(f"http://{info['address']}/check_nodes", json={'nodes': list(nodes.keys())})
            log_message(f"Node {node} at {info['address']} has been notified about the change.")
        except Exception as e:
            log_message(f"Failed to notify node {node} about the change: {e}")


def initial_nodes():
    time.sleep(15)  # Wait for 25 seconds after startup
    with threading.Lock():
        if nodes:
            log_message(f"Initial nodes: {list(nodes.keys())}")
            notify_nodes_of_change()
        else:
            log_message("No nodes registered yet.")


@app.route('/register', methods=['POST'])
def register():
    node_data = request.json
    node_id = node_data['node']
    node_address = node_data['address']

    with threading.Lock():
        new_node = node_id not in nodes
        log_message(f"New node: {new_node}")
        nodes[node_id] = {'last_seen': datetime.now(), 'address': node_address}
        log_message(f"Node {node_id} registered or updated with address {node_address}.")

    # if new node are registered, notify all nodes about the change
    if new_node and initial_nodes_handled:
        log_message(f"Triggering notification to all nodes about the new node {node_id}.")
        notify_nodes_of_change()

    return jsonify(list(nodes.keys())), 200


@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    node = request.json.get('node')
    with threading.Lock():
        if node in nodes:
            nodes[node]['last_seen'] = datetime.now()  # Update the heartbeat timestamp
    return 'OK', 200


@app.route('/nodes', methods=['GET'])
def get_nodes():
    return jsonify(list(nodes.keys())), 200


if __name__ == '__main__':
    initial_nodes_handled = False
    threading.Thread(target=check_inactive_nodes, daemon=True).start()
    app.run(host='0.0.0.0', port=8080, threaded=True)
