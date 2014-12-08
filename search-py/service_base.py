#!/usr/bin/env python
from functools import partial
import json
import getopt
import logging
import signal
import sys
from common import init_base, init_django, invoke

def _handle_args(argv = sys.argv[1:]):
    config_file = 'config.json'
    try:
        opts, _ = getopt.getopt(
            argv, 'o:fpdiwec',
            ['level=', 'show-warnings', 'output-file=', 'log-format=',      \
                'debug', 'info', 'warn', 'error', 'config-file='])
    except getopt.error, msg:
        print msg
        sys.exit(2)

    logging.basicConfig(
        level = logging.DEBUG)
    now_handler = logging.getLogger().handlers[0]
    # process options
    for o, a in opts:
        if o in ('-o', '--output-file'):
            logging.getLogger('').addHandler(now_handler)
            now_handler = logging.FileHandler(a)
        elif o in ('-l', '--level'):
            now_handler.setLevel(a)
        elif o in ('-d', '--debug'):
            now_handler.setLevel(logging.DEBUG)
        elif o in ('-i', '--info'):
            now_handler.setLevel(logging.INFO)
        elif o in ('-w', '--warn'):
            now_handler.setLevel(logging.WARN)
        elif o in ('-e', '--error'):
            now_handler.setLevel(logging.ERROR)
        elif o in ('-f', '--log-format'):
            now_handler.setFormatter(logging.Formatter(fmt = a))
        elif o in ('-c', '--config-file'):
            config_file = a
        elif o in ('--show-warnings', ):
            logging.captureWarnings(True)
    logging.getLogger('').addHandler(now_handler)
    return config_file

class ServiceEngine(object):
    def __init__(self, local_name):
        from connection import SessionManager
        self.servers     = []
        self.session_mgr = SessionManager()
        self.local_name  = local_name

    def add_server(self, ctor, kwargs, delayed):
        kwargs = kwargs or {}
        kwargs['local_name']  = self.local_name
        kwargs['session_mgr'] = self.session_mgr
        server = ctor(**kwargs)
        server.delayed_start = delayed
        self.servers.append(server)

    def add_connections(self, ctor, kwargs, after_init):
        kwargs = kwargs or {}
        kwargs['mgr']        = self.session_mgr
        kwargs['local_name'] = self.local_name
        client = ctor(**kwargs)
        client.init_session(
            handler = partial(
                self.__after_session_init,
                session    = client,
                after_init = after_init))

    def __after_session_init(self, session, succeed, after_init):
        self.session_mgr.add_managed_session(session = session)
        invoke(after_init, kwargs = {'session': session})

    def start(self):
        for server in self.servers:
            if not server.delayed_start:
                server.start()
            else:
                from tornado.ioloop import IOLoop
                ioloop = IOLoop.instance()
                ioloop.add_callback(callback = server.start)

    def stop(self):
        for server in self.servers:
            server.shutdown()

class ConfigParser(object):
    def __init__(self, file_name):
        self.engine       = None
        self.file_name    = file_name
        self.server_types = {}
        self.client_types = {}

    def get_engine(self):
        return self.engine

    @staticmethod
    def load_module_item(package, name):
        __import__(package)
        module = sys.modules[package]
        return getattr(module, name)

    def handle_base(self, config):
        local_name = config['local_name']
        self.engine = ServiceEngine(local_name)
        queue_thread = config.get('task_threads')
        require_django = bool(config.get('require_django'))
        if queue_thread:
            from common.task import TaskQueue
            task_queue = TaskQueue(num_thread = queue_thread)
            task_queue.make_default()
            task_queue.start()
        if require_django:
            init_django()

    def handle_type(self, config, mapping):
        if not config:
            return
        for entry in config:
            package = entry['package']
            name    = entry['name']
            clsname = entry['class']
            cls     = self.load_module_item(package, clsname)
            mapping[name] = cls

    def handle_message(self, config):
        for entry in config:
            package = entry
            func    = self.load_module_item(package, 'register_message')
            func()

    def handle_endpoint(self, config):
        for entry in config:
            name    = entry['type']
            kwargs  = entry['kwargs']
            enabled = entry['enabled']
            delayed = bool(entry.get('delay_start'))
            if enabled == 'true':
                ctor    = self.server_types[name]
                self.engine.add_server(ctor, kwargs, delayed)

    def handle_connections(self, config):
        if not config:
            return
        for entry in config:
            name    = entry['type']
            kwargs  = entry['kwargs']
            ctor    = self.client_types[name]
            after_init = entry.get('initialize')
            if after_init:
                after_init = self.load_module_item(
                    after_init['package'], after_init['method'])
            self.engine.add_connections(ctor, kwargs, after_init)

    def parse(self):
        try:
            config_str = None
            with open(self.file_name) as f:
                config_str = f.read()
            config = json.loads(config_str)
            self.handle_base(config['base'])
            self.handle_type(config['server'], self.server_types)
            self.handle_message(config['message'])
            self.handle_type(config.get('client'), self.client_types)
            self.handle_endpoint(config['endpoint'])
            self.handle_connections(config.get('connections'))
        except Exception:
            logging.exception('parse config')
            return False
        return True

def _handle_config(config_file):
    parser = ConfigParser(config_file)
    if parser.parse():
        return parser.get_engine()

def sig_handler(*_):
    from tornado.ioloop import IOLoop
    ioloop = IOLoop.instance()
    ioloop.stop()

def main():
    init_base()
    config_file = _handle_args()
    engine = _handle_config(config_file)
    if not engine:
        sys.exit(1)
    engine.start()
    from tornado.ioloop import IOLoop
    from common.task import TaskQueue
    ioloop = IOLoop.instance()
    signal.signal(signal.SIGINT, sig_handler)
    try:
        logging.info('starting io_loop...')
        ioloop.start()
    except:
        logging.exception('ioloop')
    engine.stop()
    TaskQueue.get_instance().stop(wait = True)

if __name__ == '__main__':
    main()

