import atexit
import json
import traceback
from confluent_kafka import avro, Consumer as KafkaConsumer, KafkaError, TopicPartition, OFFSET_END, TIMESTAMP_NOT_AVAILABLE, Producer
from confluent_kafka.avro.cached_schema_registry_client import CachedSchemaRegistryClient
from confluent_kafka.avro import AvroProducer as OGProducer, AvroConsumer
from confluent_kafka.avro.serializer import SerializerError
from confluent_kafka.avro.serializer.message_serializer import MessageSerializer


class StringKeyAvroConsumer(AvroConsumer):

    def poll(self, timeout=None):
        """
        This is an overriden method from AvroConsumer class. This handles message
        deserialization using avro schema for the value only.

        @:param timeout
        @:return message object with deserialized key and value as dict objects
        """
        if timeout is None:
            timeout = -1
        message = super(AvroConsumer, self).poll(timeout)
        if message is None:
            return None
        if not message.value() and not message.key():
            return message
        if not message.error():
            if message.value() is not None:
                try:
                    decoded_value = self._serializer.decode_message(
                        message.value())
                    message.set_value(decoded_value)
                except Exception as e:
                    print("bad value", message.value())
        return message


def seek_to(consumer, topic_name, offset=OFFSET_END):
    topic = consumer.list_topics(topic_name).topics[topic_name]
    partition_ids = topic.partitions.keys()
    consumer.assign([
        TopicPartition(topic_name, pid, offset)
        for pid in partition_ids
    ])


consumer = StringKeyAvroConsumer({
    'bootstrap.servers': 'kafka-sharedv1.internal.jask.ai:9092',
    'schema.registry.url': 'http://schema-registry.internal.jask.ai:8081',
    'group.id': 'crennie',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': False
})

state={}

def stop():
    with open('recs.json', 'w') as f:
        f.write(json.dumps(state))
    consumer.close()
    producer.flush()

atexit.register(stop)


def cycle(consumer, on_msg=lambda x: None):
    msg = None
    try:
        msg = consumer.poll(10)
    except SerializerError:
        print("Message deserialization failed")
        traceback.print_exc()

    if msg is not None:
        if msg.error():
            if msg.error().code() != KafkaError._PARTITION_EOF:
                print("err", msg.error())
        else:
            record = msg.value()
            print('rec', record)
            on_msg(record)

TOPIC='vertiv-us_list_items'

def to_state(record):
    if record['listId'].endswith('_recorded_future'):
        if record['active']:
            state[record['id']] = record
        else:
            try:
                del state[record['id']]
            except KeyError:
                pass

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

seek_to(consumer, TOPIC, 0)

while True:
    cycle(consumer, to_state)

