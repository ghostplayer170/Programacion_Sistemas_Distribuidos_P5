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
    sys.stdout.flush() # Flush the stdout buffer to ensure logs are written immediately


def check_inactive_nodes():
    global initial_nodes_handled # Flag to check if initial nodes have been handled
    if not initial_nodes_handled:
        initial_nodes()
        initial_nodes_handled = True
    while True:
        time.sleep(30)  # Time interval to check for inactive nodes
        current_time = datetime.now()
        to_remove = [] # List of nodes to remove
        with threading.Lock():
            if not nodes:
                log_message("No nodes registered yet.")
                continue
            for node, info in list(nodes.items()):
                # Check if the node is inactive for more than 30 seconds
                if current_time - info['last_seen'] > timedelta(seconds=30):
                    to_remove.append(node)
            for node in to_remove: # Remove the inactive node
                del nodes[node]
                log_message(f"Detected inactive node: {node}. Triggering notification to active nodes.")
            if to_remove: # Notify active nodes about the change
                notify_nodes_of_change()


def notify_nodes_of_change(): # Notify all nodes about the change
    items = list(nodes.items()) # Get a snapshot of the nodes
    for node, info in items:
        try:
            # Notify the node about the change
            requests.post(f"http://{info['address']}/check_nodes", json={'nodes': list(nodes.keys())})
            log_message(f"Node {node} at {info['address']} has been notified about the change.")
        except Exception as e:
            log_message(f"Failed to notify node {node} about the change: {e}")


def initial_nodes():
    time.sleep(15)  # Wait for 15 seconds after startup
    with threading.Lock():
        if nodes:
            log_message(f"Initial nodes: {list(nodes.keys())}")
            notify_nodes_of_change()
        else:
            log_message("No nodes registered yet.")


@app.route('/register', methods=['POST']) # Register a new node
def register():
    # Get the node ID and address from the request
    node_data = request.json
    node_id = node_data['node']
    node_address = node_data['address']

    # Register the node
    with threading.Lock(): # Lock the thread
        new_node = node_id not in nodes # Check if the node is new
        nodes[node_id] = {'last_seen': datetime.now(), 'address': node_address}
        log_message(f"Node {node_id} registered successfully and updated the last seen time.")

    # if new node are registered, notify all nodes about the change
    if new_node and initial_nodes_handled:
        log_message(f"Triggering notification to all nodes about the new node {node_id}.")
        notify_nodes_of_change()

    # Return the list of all nodes
    return jsonify(list(nodes.keys())), 200


@app.route('/heartbeat', methods=['POST']) # Heartbeat
def heartbeat():
    node = request.json.get('node') # Get the node ID from the request
    with threading.Lock():
        if node in nodes:
            nodes[node]['last_seen'] = datetime.now()  # Update the heartbeat timestamp
    return 'OK', 200


@app.route('/nodes', methods=['GET']) # Get all nodes
def get_nodes():
    return jsonify(list(nodes.keys())), 200


if __name__ == '__main__':
    initial_nodes_handled = False
    # Start the thread to check inactive nodes
    threading.Thread(target=check_inactive_nodes, daemon=True).start()
    # Start the Flask app
    app.run(host='0.0.0.0', port=8080, threaded=True)
