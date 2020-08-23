# -*- coding: utf-8 -*-

import unittest
import pipeutil

class TestPipe(unittest.TestCase):
	def test_server(self):
		self.server = pipeutil.server("testPipe")
		with self.assertRaises(exception):
			pipeutil.server("testPipe")
		