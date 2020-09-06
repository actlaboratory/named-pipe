# -*- coding: utf-8 -*-

"""Named pipe client object."""

import sys
import win32pipe, win32file, pywintypes
import winerror

class Client():
	"""named pipe client"""
	def __init__(self, name):
		"""
			Sets the name of the pipe to connect.

			:param name: Name of the pipe to connect.
			:type name: str
		"""
		self.name=name

	def connect(self):
		"""Connects to the pipe specified in the constructor."""
		try:
			self.handle = win32file.CreateFile("\\\\.\\pipe\\%s" % (self.name), win32file.GENERIC_READ | win32file.GENERIC_WRITE, 0, None, win32file.OPEN_EXISTING, 0, None)
		except pywintypes.error as e:
			if e.winerror == winerror.ERROR_FILE_NOT_FOUND:
				raise PipeServerNotFoundError(e.strerror)
			else:
				raise e
		#end except
		res = win32pipe.SetNamedPipeHandleState(self.handle, win32pipe.PIPE_READMODE_MESSAGE, None, None)
		if res == 0:
			raise PipeError("SetNamedPipeHandleState failed.")

	def disconnect(self):
		"""Disconnects from the pipe."""
		if self.handle: win32file.CloseHandle(self.handle)

	def write(self, message):
		"""
			Writes string data to the connected pipe.
		"""
		try:
			data = str.encode(f"{message}")
			win32file.WriteFile(self.handle, data)
			return True
		except:
			return False

class PipeServerNotFoundError(Exception): pass
class PipeBusyError(Exception): pass
class PipeError(Exception): pass

