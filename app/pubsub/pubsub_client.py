# app/pubsub/pubsub_client.py
from google.cloud import pubsub_v1
import json
import os

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
TOPIC_ID = os.getenv("PUBSUB_TOPIC")

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

def publish_event(event_type: str, payload: dict):
    """
    Envía un mensaje a Pub/Sub con el tipo de evento y los datos asociados.
    """
    message = {
        "event": event_type,
        "data": payload
    }
    data = json.dumps(message).encode("utf-8")

    future = publisher.publish(topic_path, data)
    print(f"Publicando evento '{event_type}' en {TOPIC_ID}...")
    return future.result()
