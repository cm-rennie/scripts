from __future__ import print_function
import sys
import uuid

from max_message_vars import message, random_asset_from_group
from confluent_kafka import Producer


class SimpleProducer(object):
    def __init__(self, config):
        self.producer = Producer(config)

    def flush(self):
        self.producer.flush()

    def produce(self, **kwargs):
        topic = kwargs.pop('topic', None)
        value = kwargs.pop('value', None)
        key = kwargs.pop('key', None)

        self.producer.produce(topic, value, key, **kwargs)


def main(**kwargs):
    topic = kwargs.pop('topic', 'sandbox_events')
    max_iters = kwargs.pop('max_iters', 10)

    p = SimpleProducer({
        'bootstrap.servers': 'localhost:9092'
    })

    i = 0
    while True:
        asset_id = random_asset_from_group()
        msg = message(asset_id, 40000)
        print("{0} -> Pushing message for asset {1} \\nTo topic: {2}".format(str(i), asset_id, topic))
        p.produce(topic=topic, key=None, value=msg)
        if i % 10000 == 0:
            p.flush()
        i += 1


if __name__ == "__main__":
    args = {}
    if len(sys.argv) > 0:
        args['topic'] = sys.argv[1].strip()
    if len(sys.argv) > 1:
        args['max_iters'] = int(sys.argv[2].strip())
    main(**args)