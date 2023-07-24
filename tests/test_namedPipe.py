# -*- coding: utf-8 -*-

import time
import unittest
import namedPipe


class TestNamedPipe(unittest.TestCase):
    def test_duplicate(self):
        pipeServer = namedPipe.Server("testpipe")
        pipeServer.start()
        time.sleep(0.3)
        with self.assertRaises(namedPipe.PipeAlreadyExistsError):
            pipeServer2 = namedPipe.Server("testpipe")
            pipeServer2.start()
        #end error
        pipeServer.exit()

    def test_connection(self):
        self.connected = False
        self.disconnected = False
        self.recreated = False
        pipeServer = namedPipe.Server("testpipe")
        pipeServer.setConnectCallback(self.onConnect)
        pipeServer.setDisconnectCallback(self.onDisconnect)
        pipeServer.setReopenCallback(self.onReopen)
        self.assertEqual(pipeServer.getFullName(), "\\\\.\\pipe\\testpipe")
        pipeServer.start()
        time.sleep(0.3)
        pipeClient = namedPipe.Client("testpipe")
        pipeClient.connect()
        time.sleep(1)
        self.assertTrue(self.connected)
        pipeClient.disconnect()
        time.sleep(1)
        self.assertTrue(self.disconnected)
        self.assertTrue(self.reopened)
        pipeServer.exit()

    def test_connection_error(self):
        pipeClient = namedPipe.Client("testpipe")
        with self.assertRaises(namedPipe.PipeServerNotFoundError):
            pipeClient.connect()

    def test_message_callback(self):
        pipeServer = namedPipe.Server("testpipe")
        self.received_message = ""
        pipeServer.setReceiveCallback(self.onReceive)
        pipeServer.start()
        time.sleep(0.3)
        pipeClient = namedPipe.Client("testpipe")
        pipeClient.connect()
        time.sleep(1)
        msg = "abc abc abc"
        pipeClient.write(msg)
        time.sleep(1)
        self.assertEqual(self.received_message, msg)
        pipeClient.disconnect()
        pipeServer.exit()

    def test_message_polling(self):
        pipeServer = namedPipe.Server("testpipe")
        pipeServer.start()
        time.sleep(0.3)
        pipeClient = namedPipe.Client("testpipe")
        pipeClient.connect()
        time.sleep(1)
        self.assertTrue(pipeServer.getNewMessageList() is None)
        msg1 = "beep, boop, meow"
        msg2 = "hoge, huga, piyo"
        pipeClient.write(msg1)
        pipeClient.write(msg2)
        time.sleep(1)
        lst = pipeServer.getNewMessageList()
        self.assertTrue(isinstance(lst, list))
        self.assertEqual(len(lst), 2)
        self.assertEqual(lst[0], msg1)
        self.assertEqual(lst[1], msg2)
        self.assertTrue(pipeServer.getNewMessageList() is None)
        pipeClient.disconnect()
        pipeServer.exit()

    def test_message_unicodefragment(self):
        pipeServer = namedPipe.Server("testpipe")
        pipeServer.start()
        time.sleep(0.3)
        pipeClient = namedPipe.Client("testpipe")
        pipeClient.connect()
        time.sleep(1)
        msg1 = ("a" * (namedPipe.READ_SIZE - 1)) + "猫" # b'\xe7\x8c\xab'
        pipeClient.write(msg1)
        time.sleep(1)
        lst = pipeServer.getNewMessageList()
        self.assertTrue(isinstance(lst, list))
        self.assertEqual(len(lst), 2)
        self.assertEqual(lst[0], "a" * (namedPipe.READ_SIZE - 1))
        self.assertEqual(lst[1], "猫")
        pipeClient.disconnect()
        pipeServer.exit()


    def onConnect(self):
        self.connected = True

    def onDisconnect(self):
        self.disconnected = True

    def onReopen(self):
        self.reopened = True

    def onReceive(self, msg):
        self.received_message = msg
