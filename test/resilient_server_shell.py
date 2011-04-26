# -*- coding: utf-8 -*-
"""
resilient_server_shell.py

simple zeromq_driven_process running a ResilientServer
"""
from collections import deque
import logging
import os
import sys
import time

import zmq

from diyapi_tools.zeromq_pollster import ZeroMQPollster
from diyapi_tools.resilient_server import ResilientServer
from diyapi_tools.deque_dispatcher import DequeDispatcher
from diyapi_tools import time_queue_driven_process

_local_node_name = os.environ["SPIDEROAK_MULTI_NODE_NAME"]
_log_path = u"/var/log/pandora/resilient_server_shell.log"
_test_server_address = os.environ.get(
    "DIYAPI_TEST_SERVER_ADDRESS",
    "tcp://127.0.0.1:8000"
)

def _handle_test_message(state, message, _data):
    log = logging.getLogger("_handle_test_message")
    log.info("received %s" % (message, ))

    reply = {
        "message-type"  : "test-message-reply",
        "request-id"    : message["request-id"],
        "client-tag"    : message["client-tag"],
    }

    state["test-server"].send_reply(reply)

_dispatch_table = {
    "test-message"              : _handle_test_message,
}

def _create_state():
    return {
        "zmq-context"           : zmq.Context(),
        "pollster"              : ZeroMQPollster(),
        "test-server"           : None,
        "receive-queue"         : deque(),
        "queue-dispatcher"      : None,
    }

def _setup(_halt_event, _state):
    log = logging.getLogger("_setup")

    state["test-server"] = ResilientServer(
        state["zmq-context"],
        _test_server_address,
        state["receive-queue"]
    )
    state["test-server"].register(state["pollster"])

    state["queue-dispatcher"] = DequeDispatcher(
        state,
        state["receive-queue"],
        _dispatch_table
    )

    # hand the pollster and the queue-dispatcher to the time-queue 
    return [
        (state["pollster"].run, time.time(), ), 
        (state["queue-dispatcher"].run, time.time(), ), 
    ] 

def _tear_down(_state):
    log = logging.getLogger("_tear_down")

    log.debug("stopping test server")
    state["test-server"].close()

    state["zmq-context"].term()
    log.debug("teardown complete")

if __name__ == "__main__":
    state = _create_state()
    sys.exit(
        time_queue_driven_process.main(
            _log_path,
            state,
            pre_loop_actions=[_setup, ],
            post_loop_actions=[_tear_down, ]
        )
    )
