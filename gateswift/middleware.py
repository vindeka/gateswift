# Copyright (c) 2013 Vindeka, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import kombu

from swift.common.utils import get_logger
from swift.common.swob import Request, HttpOk, HTTPBadRequest, HttpNotFound


class GateMiddleware(object):
    """
    Gate middleware for swift communication.

    Add to your pipeline in proxy-server.conf, such as::

        [pipeline:main]
        pipeline = catch_errors cache tempauth gatemiddleware proxy-server

    And add a keystone2 filter section, such as::

        [filter:gatemiddleware]
        use = egg:gateswift#gatemiddleware
        amqp_connection = amqp://guest:guest@localhost/

    :param app: The next WSGI app in the pipeline
    :param conf: The dict of configuration values
    """
    def __init__(self, app, conf):
        self.app = app
        self.conf = conf
        self.logger = get_logger(conf, log_route='gatemiddleware')

        self.conn_str = conf.get('amqp_connection', 'amqp://localhost/')
        self.exc_str = conf.get('amqp_exchange', 'gate')
        self.exc_type = conf.get('amqp_exchange_type', 'direct')
        self.exc_durable = bool(conf.get('amqp_exchange_durable', 'True'))

    def __call__(self, env, start_response):
        self.logger.debug('Initialising gate middleware')

        req = Request(env)
        try:
            version, account = req.split_path(1, 3, True)
        except ValueError:
            return HttpNotFound(request=req)
        
        if account is 'gate':
            # Handles direct calls to gate
            return HttpOk

        if 'X-Gate-Verify' in env:
            verify = env['X-Gate-Verify']
            self.logger.debug('Verification request: %s algorithms: %s' % (req.path, verify))

            try:
                version, account, container, obj = req.split_path(4, 4, True)
            except ValueError:
                return HTTPBadRequest(request=req)

            algorithms = verify.split(',')
            for algo in algorithms:
                metakey = 'X-Object-Meta-Gate-%s' % algo.upper()
                if metakey not in env:
                    self.logger.debug('Invalid verification request, object missing: %s' % (metakey))
                    return HTTPBadRequest(request=req)

            if publish_verify(req.path, algorithms):
                for algo in algorithms:
                    statuskey = 'X-Object-Meta-Gate-Verify-%s-Status' % algo.upper()
                    env[statuskey] = 'Queued'
                    env['X-Object-Meta-Gate-Verify'] = verify

        if 'X-Gate-Process' in env:
            module = env['X-Gate-Process']
            self.logger.debug('Process request: %s module: %s' % (req.path, module))

            try:
                version, case, container, obj = req.split_path(4, 4, True)
            except ValueError:
                return HTTPBadRequest(request=req)

            if publish_process(req.path, algorithms):
                for algo in algorithms:
                    env['X-Object-Meta-Gate-Process'] = module
                    env['X-Object-Meta-Gate-Process-Status'] = 'Queued'

        # TODO: Get reponse to see if a fake object
        reponse = self.app(env, start_response)
        return reponse

    def publish_verify(self, path, algorithms):
        """ Publish a verify request on the queue to gate engine """
        exchange = kombu.Exchange(self.exc_str, exc_type, durable=exc_durable)
        queue = kombu.Queue('verify', exchange=exchange, routing_key='verify')
        with kombu.Connection(self.conn_str) as connection:
            with connection.Producer(serializer='json') as producer:
                producer.publish({'path':path, 'algorithms':algorithms},
                    exchange=exchange, routing_key='verify', declare=[queue])
        return True

    def publish_process(self, path, module):
        """ Publish a process request on the queue to gate engine """
        exchange = kombu.Exchange(self.exc_str, exc_type, durable=exc_durable)
        queue = kombu.Queue('process', exchange=exchange, routing_key='process')
        with kombu.Connection(self.conn_str) as connection:
            with connection.Producer(serializer='json') as producer:
                producer.publish({'path':path, 'module':module},
                    exchange=exchange, routing_key='process', declare=[queue])
        return True

def filter_factory(global_conf, **local_conf):
    """Returns a WSGI filter app for use with paste.deploy."""
    conf = global_conf.copy()
    conf.update(local_conf)

    def auth_filter(app):
        return GateMiddleware(app, conf)
    return auth_filter
