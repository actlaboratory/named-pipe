# -*- coding: utf-8 -*-

import time
import unittest
import namedPipe

class TestNamedPipe(unittest.TestCase):
	def test_connection(self):
		self.connected=False
		self.disconnected=False
		self.recreated=False
		pipeServer=namedPipe.Server("testpipe")
		pipeServer.setConnectCallback(self.onConnect)
		pipeServer.setDisconnectCallback(self.onDisconnect)
		pipeServer.setReopenCallback(self.onReopen)
		pipeServer.start()
		time.sleep(0.3)
		pipeClient=namedPipe.Client("testpipe")
		pipeClient.connect()
		time.sleep(1)
		self.assertTrue(self.connected)
		pipeClient.disconnect()
		time.sleep(1)
		self.assertTrue(self.disconnected)
		self.assertTrue(self.reopened)
		pipeServer.exit()

	def test_connection_error(self):
		pipeClient=namedPipe.Client("testpipe")
		with self.assertRaises(namedPipe.PipeServerNotFoundError):
			pipeClient.connect()

	def onConnect(self):
			self.connected=True

	def onDisconnect(self):
		self.disconnected=True

	def onReopen(self):
		self.reopened=True
