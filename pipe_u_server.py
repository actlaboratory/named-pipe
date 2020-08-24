import win32pipe, win32file, pywintypes
import os
import threading
import time
import winerror

MODE_DUPLEX = win32pipe.PIPE_ACCESS_DUPLEX
MODE_INBOUND = win32pipe.PIPE_ACCESS_INBOUND
MODE_OUTBOUND = win32pipe.PIPE_ACCESS_OUTBOUND


def exist(name):
	return os.path.exists(r"\\.\pipe\%s" % (name))

class server(threading.Thread):
	def __init__(self, name, openMode = MODE_DUPLEX, max = 1, outsize = 64*1024+1, insize = 64*1024+1):
		super().__init__()
		self.name = name
		self.openMode = openMode
		self.max = max
		self.outsize = outsize
		self.insize = insize
		self.pipeHandle = None
		self.canceled = False
		self.openPipe()
		self.inbox = []
		self.outbox = []

	def openPipe(self):
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
				raise Pipe_already_exist(e.strerror)
			else:
				raise e

	def run(self):
		while True:		
			message = b""
			if self.canceled:
				break
			try:
				win32pipe.ConnectNamedPipe(self.pipeHandle, None)
			except pywintypes.error as e:
				self.close()
				self.openPipe()
				print("reOpen: " + str(e))
			#end except
			while True:
				try:
					resp = win32file.ReadFile(self.pipeHandle, 64*1024)
				except pywintypes.error as e:
					if e.winerror == winerror.ERROR_NO_DATA:
						break
					else:
						print("Error while receiving: %s" % str(e))
						break
				print(resp)
				if resp[0] == 0:
					message += resp[1]
					break
				else:
					message += resp[1]
					print(message)
					continue

			self.inbox.append(message.decode())
			for out in self.outbox:
				win32file.WriteFile(self.pipeHandle, out)

	def getInbox(self):
		returnbox = self.inbox
		self.inbox.clear()
		return returnbox

	def setOutbox(self, data):
		self.outbox.append(data)

	def stop(self):
		self.canceled = True

	def close(self):
		win32file.CloseHandle(self.pipeHandle)

	def __dell__(self):
		win32file.CloseHandle(self.pipeHandle)

class Pipe_already_exist(Exception): pass

if __name__ == '__main__':
	s = server("test_develop")
	s.start()
	while True:
		data = s.getInbox()
		time.sleep(0.01)
		if len(data) > 0:
			print(data[0])
			print("it will break")
			break
	s.close()

