# -*- coding: utf-8 -*-

"""Named pipe server object."""

import win32pipe, win32file, pywintypes
import os
import threading
import time
import winerror

MODE_DUPLEX = win32pipe.PIPE_ACCESS_DUPLEX
MODE_INBOUND = win32pipe.PIPE_ACCESS_INBOUND
MODE_OUTBOUND = win32pipe.PIPE_ACCESS_OUTBOUND

READ_SIZE=65535
ERROR_BROKEN_PIPE=109


class Server(threading.Thread):
	"""Instantiate this class with pipe name to create a named pipe."""
	def __init__(self, name, openMode = MODE_DUPLEX, max = 1, outsize = 64*1024+1, insize = 64*1024+1):
		super().__init__()
		self.name = name
		self.openMode = openMode
		self.max = max
		self.outsize = outsize
		self.insize = insize
		self.pipeHandle = None
		self.canceled = False
		self._openPipe()
		self.inbox = []
		self.outbox = []

	def _openPipe(self):
		"""Internal function to open a named pipe."""
		try:
			self.pipeHandle = win32pipe.CreateNamedPipe(
				"\\\\.\\pipe\\%s" % (self.name),
				self.openMode,
				win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
				self.max,
				self.outsize,
				self.insize,
				0,
				None)
		except pywintypes.error as e:
			if e.winerror == winerror.ERROR_PIPE_BUSY:
				raise PipeAlreadyExistsError(e.strerror)
			else:
				raise e
		#end except

	def run(self):
		while True:		
			if self.canceled: break
			self._handleClient()

	def _handleClient(self):
		"""Internal function to wait for client connection and receive messages."""
		try:
			win32pipe.ConnectNamedPipe(self.pipeHandle, None)
		except pywintypes.error as e:
			self.reopen()
			print("Reopened pipe due to error: %s" % e)
		#end except
		while True:
			try:
				resp = win32file.ReadFile(self.pipeHandle, READ_SIZE)
			except pywintypes.error as e:
				if e.winerror == winerror.ERROR_NO_DATA:
					break
				if e.winerror==ERROR_BROKEN_PIPE:
					print("Pipe ended, reopening...")
					self.reopen()
					break
				else:
					print("Error while receiving: %s" % str(e))
					break
			#end except
			self.inbox.append(resp[1])
			print("Received message: %s" % resp[1])
			if resp[0] == 0: break
			#end while
		#end _handleClient

	def reopen(self):
		"""Reopens this pipe."""
		self.close()
		self._openPipe()

	def close(self):
		"""Closes this named pipe."""
		win32file.CloseHandle(self.pipeHandle)
