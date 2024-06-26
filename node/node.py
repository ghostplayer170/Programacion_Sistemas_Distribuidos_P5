from flask import Flask, request
import requests
import os
import time
import sys
from threading import Thread

app = Flask(__name__)  # Create a Flask app
node_id = int(os.getenv('NODE_ID', '80'))  # Defaulting to 80 if NODE_ID is not set
registry_url = os.getenv('REGISTRY_URL', 'http://registry:8080')  # Defaulting to registry if REGISTRY_URL is not set
nodes = []  # List of nodes
current_coordinator = None
election_in_progress = False


def log_message(message):
    print(message)
    sys.stdout.flush()  # Flush the stdout buffer to ensure logs are written immediately


def send_heartbeat():
    while True:
        try:
            # Send a heartbeat to the registry
            requests.post(f"{registry_url}/heartbeat", json={'node': node_id})
            log_message(
                f"Sent heartbeat from node {node_id}, current coordinator is {current_coordinator} among {nodes}")
            time.sleep(30)  # Send heartbeat every 30 seconds
            check_current_coordinator()  # Check the current coordinator
        except requests.RequestException as e:
            log_message(f"Error sending heartbeat from node {node_id}: {e}")


def check_current_coordinator():  # if current coordinator id is less than the node id, then start the election
    global node_id, current_coordinator, election_in_progress
    if current_coordinator is not None and current_coordinator < node_id:
        log_message(
            f"Node {node_id} detected that it has a higher ID than the current coordinator {current_coordinator}. Initiating election.")
        initiate_election()


def register_with_registry():
    node_address = f"node{node_id}:80"
    try:
        # Register the node with the registry
        response = requests.post(f"{registry_url}/register", json={'node': node_id, 'address': node_address})
        if response.status_code == 200:
            global nodes
            nodes = response.json()
            log_message(f"Node {node_id} registered successfully with registry. Active nodes: {nodes}")
            update_peers(nodes)
        else:
            log_message(f"Failed to register node {node_id} with registry.")
    except requests.RequestException as e:
        log_message(f"Error registering node {node_id} with registry: {e}")


def update_peers(new_peers):
    global nodes, current_coordinator, election_in_progress
    if sorted(nodes) != sorted(new_peers):
        nodes = sorted(new_peers)
        log_message(f"Node {node_id} noticed a change in peers: {nodes}")
        time.sleep(10)  # Wait for all nodes to update their lists

        # Attempt to fetch the current coordinator from peers
        if not election_in_progress:
            log_message(f"Node {node_id} fetching coordinator from peers.")
            fetch_coordinator_from_peers()  # Fetch the coordinator from the peers to update the current coordinator

        # Election initiation logic
        if current_coordinator not in nodes:  # If current coordinator is no longer available
            initiate_election()
        elif node_id == current_coordinator:  # Only the coordinator initiates elections
            initiate_election()


def fetch_coordinator_from_peers():
    global nodes, current_coordinator
    for peer in nodes:
        if peer != node_id:  # Avoid querying self
            try:
                response = requests.get(f"http://node{peer}:80/coordinator_info")
                if response.status_code == 200:
                    received_coordinator = response.json().get('coordinator')
                    if received_coordinator:
                        current_coordinator = received_coordinator
                        log_message(f"Updated current coordinator from node {peer} to {current_coordinator}")
                        break  # Exit after successful update
            except requests.RequestException as e:
                log_message(f"Failed to fetch coordinator from node {peer}: {e}")

        # Coordinator initiation logic
        if current_coordinator not in nodes:  # If current coordinator is no longer available
            if not election_in_progress:
                initiate_election()
        elif node_id == current_coordinator:  # Only the coordinator initiates elections
            if not election_in_progress:
                initiate_election()


def initiate_election():
    global node_id, nodes, current_coordinator, election_in_progress
    if election_in_progress:
        return
    election_in_progress = True
    log_message(f"Node {node_id} initiating election among {nodes}")
    pass_election_message(node_id, node_id)  # Pass the election message


def pass_election_message(initiator, max_id):
    global nodes, current_coordinator, election_in_progress

    nodes.sort()

    if len(nodes) <= 1:  # If there is only one node in the network
        log_message(f"Node {node_id} is the only node in the network. Elected as coordinator.")
        current_coordinator = node_id
        election_in_progress = False
        return

    # Get the next node to pass the election message
    # The next node is the one after the current node in the sorted list
    current_index = nodes.index(node_id)
    next_node_index = (current_index + 1) % len(nodes)
    next_node = nodes[next_node_index]

    log_message(
        f"Passing election message from node {node_id} to node {next_node} with initiator {initiator} and max_id {max_id}")

    # If the next node is the initiator, the election is complete
    if next_node == initiator:
        if max_id == node_id:  # If the current node has the highest ID
            current_coordinator = node_id
        else:  # If the current node does not have the highest ID
            current_coordinator = max_id
        notify_all_coordinator()
        election_in_progress = False
    else:  # Pass the election message to the next node
        try:
            # Pass the election message to the next node
            # Max ID is the maximum of the current node's ID and the max ID seen so far in the network
            response = requests.post(f'http://node{next_node}:80/election',
                                     json={'initiator': initiator, 'max_id': max(max_id, node_id)})
            if response.status_code != 200:
                log_message(f"Error passing election message to node {next_node}")
        except requests.RequestException as e:
            log_message(f"Error passing election message to node {next_node}: {e}")


def notify_all_coordinator():
    global current_coordinator, nodes
    for peer in nodes:
        if peer != node_id:  # No need to notify self
            try:
                # Notify the peer about the new coordinator in the network to update their records
                response = requests.post(f'http://node{peer}:80/coordinator', json={'coordinator': current_coordinator})
                if response.status_code == 200:
                    log_message(f"Node {peer} acknowledged {current_coordinator} as coordinator.")
            except requests.RequestException as e:
                log_message(f"Error notifying node {peer} about the new coordinator: {e}")
    log_message(f"Election completed. Node {current_coordinator} is the coordinator among {nodes}.")


@app.route('/coordinator_info', methods=['GET'])  # Get the coordinator info
def get_coordinator_info():
    global current_coordinator
    return {'coordinator': current_coordinator}, 200


@app.route('/check_nodes', methods=['POST'])  # Check the nodes and update the peers
def check_nodes():
    try:
        response = requests.get(f"{registry_url}/nodes")
        new_nodes = response.json()
        update_peers(new_nodes)
    except requests.RequestException as e:
        log_message(f"Error fetching active nodes from registry: {e}")
    return 'Checked nodes and updated peers', 200


@app.route('/election', methods=['POST'])  # Pass the election message
def election():
    # Get the initiator and max_id from the request
    data = request.json
    initiator = data['initiator']
    max_id = data['max_id']
    pass_election_message(initiator, max_id)  # Pass the election message
    return 'Election message passed on', 200


@app.route('/coordinator', methods=['POST'])  # Update the coordinator
def receive_coordinator_notification():
    global current_coordinator, election_in_progress
    incoming_coordinator = request.json['coordinator']
    if current_coordinator != incoming_coordinator:  # Update the coordinator if it has changed
        current_coordinator = incoming_coordinator
        log_message(f"Node {node_id} updated coordinator to {current_coordinator}.")
        notify_all_coordinator()  # Notify all nodes about the new coordinator
    election_in_progress = False  # Reset the election flag
    return 'Coordinator updated', 200


if __name__ == '__main__':
    register_with_registry()  # Register with the registry
    peer_refresh_thread = Thread(target=send_heartbeat)  # Create a thread for the heartbeat
    peer_refresh_thread.start()  # Start the heartbeat thread
    app.run(host='0.0.0.0', port=80)  # Each node listens on its NODE_ID as port
