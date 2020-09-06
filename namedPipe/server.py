# -*- coding: utf-8 -*-

"""Named pipe server object."""

import win32pipe, win32file, pywintypes, win32event
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
		self.setDaemon(True)
		self.name = name
		self.openMode = openMode
		self.max = max
		self.outsize = outsize
		self.insize = insize
		self.pipeHandle = None
		self.should_exit=False
		self.onConnect=None
		self.onReceive=None
		self.onDisconnect=None
		self.onReopen=None
		self.get_buffer=[]
		self._openPipe()

	def setConnectCallback(self,callable):
			"""Set a callback triggered when a client connects."""
			self.onConnect=callable

	def setReceiveCallback(self,callable):
			"""Set a callback triggered when this server receives data."""
			self.onReceive=callable

	def setDisconnectCallback(self,callable):
			"""Set a callback triggered when the client disconnects. After triggering this callback, this module recreates pipe."""
			self.onDisconnect=callable

	def setReopenCallback(self,callable):
			"""Set a callback triggered when the pipe is reopened after client disconnection."""
			self.onReopen=callable

	def _openPipe(self):
		"""Internal function to open a named pipe."""
		try:
			self.pipeHandle = win32pipe.CreateNamedPipe(
				"\\\\.\\pipe\\%s" % (self.name),
				self.openMode | win32file.FILE_FLAG_OVERLAPPED,
				win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE,
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
			self._handleClient()
			if self.should_exit: break
			self._handleMessage()
			if self.should_exit: break

	def _handleClient(self):
		"""Internal function to wait for client connection."""
		overlapped=pywintypes.OVERLAPPED()
		overlapped.hEvent=win32event.CreateEvent(None, 0, 0, None)
		try:
			win32pipe.ConnectNamedPipe(self.pipeHandle, overlapped)
		except pywintypes.error as e:
			raise PipeError(e.strerror())
			should_exit=True
			return
		#end except
		while True:
			try:
				size=win32file.GetOverlappedResult(self.pipeHandle,overlapped,False)
			except pywintypes.error: pass
			if win32event.WaitForSingleObject(overlapped.hEvent,1000)==win32event.WAIT_OBJECT_0:
				self._handleConnect()
				break
			#end connect
			if self.should_exit:
				break

	def _handleConnect(self):
		"""Called when a client connects."""
		if self.onConnect: self.onConnect()

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
			msg=resp[1].decode()
			self.get_buffer.append(msg)
			if self.onReceive: self.onReceive(msg)
		#end while
	#end _handleClient

	def reopen(self):
		"""Reopens this pipe."""
		self.close()
		self._openPipe()
		if self.onReopen: self.onReopen()

	def close(self):
		"""Closes this named pipe."""
		win32file.CloseHandle(self.pipeHandle)

	def getNewMessageList(self):
		"""Checks if this pipe has new messages since the last call."""
		if len(self.get_buffer)==0: return None
		return [e for e in self.get_buffer]

	def exit(self):
		"""Exits the pipe processing"""
		self.should_exit=True
		self.join()
