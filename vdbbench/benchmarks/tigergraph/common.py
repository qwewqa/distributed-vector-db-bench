import time
import requests

def create_tigergraph_client(config: dict):
    """Creates a TigerGraph client from the configuration.

    Args:
        config: The output from the Terraform module for the TigerGraph deployment.

    Returns:
        A dictionary containing the base URL and authorization token for TigerGraph.
    """
    base_url = f"http://{config['tigergraph_host']}:9000"
    auth_token = get_tigergraph_token(base_url, config['username'], config['password'])
    return {
        "base_url": base_url,
        "auth_token": auth_token
    }

def get_tigergraph_token(base_url: str, username: str, password: str) -> str:
    """Obtains an authorization token from TigerGraph.

    Args:
        base_url: The base URL of the TigerGraph server.
        username: The username for the TigerGraph server.
        password: The password for the TigerGraph server.

    Returns:
        An authorization token for TigerGraph.
    """
    response = requests.post(
        f"{base_url}/requesttoken",
        json={"username": username, "password": password},
        headers={"accept": "application/json"}
    )
    if response.status_code == 200:
        return response.json().get("token")
    else:
        raise ConnectionError("Failed to obtain TigerGraph token.")

def wait_for_tigergraph_cluster(client: dict, timeout: int = 600):
    """Waits for the TigerGraph cluster to be ready.

    Args:
        client: The TigerGraph client to use, containing the base URL and auth token.
        timeout: The maximum time to wait for the cluster to become ready.

    Raises:
        TimeoutError: If the cluster does not become ready within the timeout.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(
                f"{client['base_url']}/echo",
                headers={"Authorization": f"Bearer {client['auth_token']}", "accept": "application/json"}
            )
            if response.status_code == 200:
                # The cluster is responding, so it's ready
                return
            else:
                time.sleep(5)
        except requests.exceptions.ConnectionError:
            # If a connection error occurs, wait a bit and try again
            time.sleep(5)
    raise TimeoutError("TigerGraph cluster did not become ready within the timeout.")


def create_schema(client):
    """Create a graph schema in TigerGraph."""
    headers = {
        "Authorization": f"Bearer {client['auth_token']}",
        "Content-Type": "application/json"
    }
    schema_endpoint = f"{client['base_url']}/gsqlserver/gsql/schema"
    schema_data = '''
    CREATE VERTEX Person (PRIMARY_ID id STRING, name STRING)
    CREATE UNDIRECTED EDGE Knows (FROM Person, TO Person)
    CREATE GRAPH MyGraph(Person, Knows)
    USE GRAPH MyGraph
    '''
    response = requests.post(schema_endpoint, data=schema_data, headers=headers)
    print(response.text)

def add_vertex(client, vertex_type, vertex_id, attributes):
    """Add a vertex to the graph."""
    data = {
        "vertices": {
            vertex_type: {
                vertex_id: attributes
            }
        }
    }
    endpoint = f"{client['base_url']}/graph/MyGraph"
    headers = {
        "Authorization": f"Bearer {client['auth_token']}",
        "Content-Type": "application/json"
    }
    response = requests.post(endpoint, data=json.dumps(data), headers=headers)
    print(response.text)

def add_edge(client, edge_type, from_vertex, to_vertex):
    """Add an edge between two vertices."""
    data = {
        "edges": {
            from_vertex: {
                edge_type: {
                    to_vertex: {}
                }
            }
        }
    }
    endpoint = f"{client['base_url']}/graph/MyGraph"
    headers = {
        "Authorization": f"Bearer {client['auth_token']}",
        "Content-Type": "application/json"
    }
    response = requests.post(endpoint, data=json.dumps(data), headers=headers)
    print(response.text)

def run_query(client, query_name, parameters):
    """Run a stored query in TigerGraph."""
    endpoint = f"{client['base_url']}/query/MyGraph/{query_name}"
    headers = {
        "Authorization": f"Bearer {client['auth_token']}",
        "Content-Type": "application/json"
    }
    response = requests.get(endpoint, params=parameters, headers=headers)
    return response.json()
