# -*- coding: utf-8 -*-

"""Named pipe client object."""

import sys
import win32pipe, win32file, pywintypes
import winerror

AUTO_CLOSE = 2001
NO_AUTO_CLOSE = 2000

class Client():
	"""named pipe client"""
	def __init__(self, name):
		self.name=name

	def connect(self):
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
		if self.handle: win32file.CloseHandle(self.handle)

	def read(self, mode = NO_AUTO_CLOSE):
		returnMessage = ""
		try:
			while True:
				resp = win32file.ReadFile(handle, 65535)
				returnMessage += resp[1]
				if resp[0]==1: break
			#end while
		except:
			return False
		#end except
		if mode == AUTO_CLOSE: win32file.CloseHandle(self.handle)
		return returnMessage

	def write(self, message, mode = NO_AUTO_CLOSE):
		try:
			data = str.encode(f"{message}")
			win32file.WriteFile(self.handle, data)
			if mode == AUTO_CLOSE:
				win32file.CloseHandle(self.handle)
			#end auto close
			return True
		except:
			return False

class PipeServerNotFoundError(Exception): pass
class PipeBusyError(Exception): pass
class PipeError(Exception): pass

