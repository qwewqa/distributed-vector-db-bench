from weaviate import Client, Objects, schema
import time


def create_weaviate_client(config):
    """Creates and returns a Weaviate client.

    Args:
        config: A dictionary with Weaviate connection details.

    Returns:
        A Weaviate client instance.
    """
    return Client(
        url=f"http://{config['host']}:{config['port']}",
        timeout_config=(5, 15)
    )


def wait_for_weaviate(client, timeout=300):
    """Waits for Weaviate to become ready.

    Args:
        client: The Weaviate client.
        timeout: Timeout in seconds.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if client.is_ready():
            print("Weaviate is ready.")
            return
        time.sleep(2)
    raise TimeoutError("Weaviate did not become ready in time.")


def create_schema(client):
    """Creates a basic schema in Weaviate.

    Args:
        client: The Weaviate client.
    """
    person_class = schema.Class(
        name="Person",
        description="A person",
        properties=[
            schema.Property(name="name", data_type=["string"]),
            schema.Property(name="age", data_type=["int"])
        ]
    )

    client.schema.create_class(person_class)
    print("Schema created successfully.")


def add_data(client):
    """Adds data to Weaviate.

    Args:
        client: The Weaviate client.
    """
    person = {
        "name": "John Doe",
        "age": 30
    }
    client.data_object.create(data_object=person, class_name="Person")
    print("Data added successfully.")


def query_data(client):
    """Queries data from Weaviate.

    Args:
        client: The Weaviate client.
    """
    result = client.query.get(class_name="Person", properties=["name", "age"]).do()
    print("Query results:", result)
