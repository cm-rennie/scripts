import atexit
import json
import traceback
from confluent_kafka import avro, Consumer as KafkaConsumer, KafkaError, TopicPartition, OFFSET_END, TIMESTAMP_NOT_AVAILABLE, Producer
from confluent_kafka.avro.cached_schema_registry_client import CachedSchemaRegistryClient
from confluent_kafka.avro import AvroProducer as OGProducer, AvroConsumer
from confluent_kafka.avro.serializer import SerializerError
from confluent_kafka.avro.serializer.message_serializer import MessageSerializer


class AvroProducer(object):
    def __init__(self, config, default_key_schema=None,
                 default_value_schema=None, schema_registry=None):
        schema_registry_url = config.pop("schema.registry.url", None)
        schema_registry_ca_location = config.pop(
            "schema.registry.ssl.ca.location", None)
        schema_registry_certificate_location = config.pop(
            "schema.registry.ssl.certificate.location", None)
        schema_registry_key_location = config.pop(
            "schema.registry.ssl.key.location", None)

        if schema_registry is None:
            if schema_registry_url is None:
                raise ValueError("Missing parameter: schema.registry.url")

            schema_registry = CachedSchemaRegistryClient(url=schema_registry_url,
                                                         ca_location=schema_registry_ca_location,
                                                         cert_location=schema_registry_certificate_location,
                                                         key_location=schema_registry_key_location)
        elif schema_registry_url is not None:
            raise ValueError(
                "Cannot pass schema_registry along with schema.registry.url config")

        self.producer = Producer(config)
        self._serializer = MessageSerializer(schema_registry)
        self._key_schema = default_key_schema
        self._value_schema = default_value_schema

    def flush(self):
        self.producer.flush()

    def produce(self, **kwargs):
        key_schema = kwargs.pop('key_schema', self._key_schema)
        value_schema = kwargs.pop('value_schema', self._value_schema)
        topic = kwargs.pop('topic', None)
        if not topic:
            raise ClientError("Topic name not specified.")
        value = kwargs.pop('value', None)
        key = kwargs.pop('key', None)

        if value is not None:
            if value_schema:
                value = self._serializer.encode_record_with_schema(
                    topic, value_schema, value)
            else:
                raise ValueSerializerError("Avro schema required for values")

        if key is not None:
            if key_schema:
                key = self._serializer.encode_record_with_schema(
                    topic, key_schema, key, True)

        self.producer.produce(topic, value, key, **kwargs)


def deactivate(record):
    if record['active'] and record['listId'].endswith('_recorded_future'):
        record['active'] = False
        try:
            producer.produce(
                key=record['id'],
                value=record,
                topic=TOPIC
            )
        except BufferError:
            producer.flush()
            deactivate(record)


with open('./recs.json', 'r') as f:
    recs = json.loads(f.read())
    for rec in recs.values():
        deactivate(rec)

if __name__ == "__main__":
    producer = AvroProducer({
        'bootstrap.servers': 'localhost:29092',
        'schema.registry.url': 'http://localhost:8081'
    }, default_value_schema=list_item_schema)

    TOPIC='sandbox_list_items'

    with open("schema.json", "r") as f:
        list_item_schema = avro.loads(
            json.dumps(
                json.loads(f.read())['ListItem']
            )
        )
