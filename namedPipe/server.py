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
		self.onReceive=None
		self.onDisconnect=None
		self._openPipe()

	def setReceiveCallback(self,callable):
			"""Set a callback triggered when this server receives data."""
			self.onReceive=callable

	def setReceiveCallback(self,callable):
			"""Set a callback triggered when the client disconnects. After triggering this callback, this module recreates pipe."""
			self.onDisconnect=callable

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
		"""Thread entry point. Do not call this function maunally."""
		while True:		
			if self.canceled: break
			self._handleClient()
			self._handleMessage()

	def _handleClient(self):
		"""Internal function to wait for client connection."""
		try:
			win32pipe.ConnectNamedPipe(self.pipeHandle, None)
		except pywintypes.error as e:
			self.reopen()
		#end except

	def _handleMessage(self):
		"""Internal function to handle incoming messages from the client."""
		while True:
			try:
				resp = win32file.ReadFile(self.pipeHandle, READ_SIZE)
			except pywintypes.error as e:
				if e.winerror == winerror.ERROR_NO_DATA: break
				if e.winerror==ERROR_BROKEN_PIPE:
					if self.onDisconnect: self.onDisconnect()
					self.reopen()
					break
			#end if disconnected
			#end except
			if self.onReceive: self.onReceive(resp[1].decode())
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
