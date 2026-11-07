import importlib.util
from pathlib import Path
import socket
import struct
import threading
import time
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('cts_socks_relay', Path(__file__).resolve().parents[1] / 'socks-relay-vm.py')
relay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(relay)


class SocksRelay(unittest.TestCase):
    def session(self, command, target='127.0.0.1', port=443):
        client, server = socket.socketpair()
        client.settimeout(5)
        records = []
        worker = threading.Thread(target=relay.serve, args=(server, ('127.0.0.1', 0), time.monotonic() + 5, records.append))
        worker.start()
        client.sendall(b'\x05\x01\x00')
        self.assertEqual(relay.read_exact(client, 2), b'\x05\x00')
        raw = target.encode('ascii')
        client.sendall(bytes([5, command, 0, 3, len(raw)]) + raw + struct.pack('!H', port))
        reply = relay.read_exact(client, 10)
        return client, worker, records, reply

    def test_private_target_is_rejected(self):
        client, worker, records, reply = self.session(1)
        self.assertEqual(reply[1], 1)
        client.close()
        worker.join(2)
        self.assertFalse(worker.is_alive())
        self.assertIn('public Internet', records[0]['message'])

    def test_udp_and_non_web_port_are_rejected(self):
        for command, port in [(3, 443), (1, 22)]:
            with self.subTest(command=command, port=port):
                client, worker, records, reply = self.session(command, port=port)
                self.assertEqual(reply[1], 1)
                client.close()
                worker.join(2)
                self.assertFalse(worker.is_alive())
                self.assertTrue(records[0].get('error'))

    def test_binary_stream_and_half_close_are_preserved(self):
        # Only this isolated unit fixture substitutes a local echo endpoint.
        # The production resolver continues to reject all private destinations.
        listener = socket.socket()
        listener.bind(('127.0.0.1', 0))
        listener.listen(1)
        target = listener.getsockname()
        payload = bytes(range(256)) * 2048

        def echo():
            connection, _ = listener.accept()
            with connection:
                received = bytearray()
                while data := connection.recv(4096):
                    received.extend(data)
                connection.sendall(received)

        echo_thread = threading.Thread(target=echo)
        echo_thread.start()
        with patch.object(relay, 'public_addresses', return_value=[(socket.AF_INET, socket.SOCK_STREAM, 0, target)]):
            client, worker, records, reply = self.session(1, 'example.com')
            self.assertEqual(reply[1], 0)
            client.sendall(payload)
            client.shutdown(socket.SHUT_WR)
            returned = bytearray()
            while data := client.recv(4096):
                returned.extend(data)
            client.close()
            worker.join(3)
        echo_thread.join(3)
        listener.close()
        self.assertFalse(worker.is_alive())
        self.assertFalse(echo_thread.is_alive())
        self.assertEqual(returned, payload)
        self.assertEqual(records[0]['client_bytes'], len(payload))
        self.assertEqual(records[0]['server_bytes'], len(payload))


if __name__ == '__main__':
    unittest.main()
