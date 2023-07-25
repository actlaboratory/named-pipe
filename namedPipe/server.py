# -*- coding: utf-8 -*-

"""Named pipe server object."""

import codecs
import win32pipe
import win32file
import pywintypes
import win32event
import os
import threading
import time
import winerror

MODE_DUPLEX = win32pipe.PIPE_ACCESS_DUPLEX
MODE_INBOUND = win32pipe.PIPE_ACCESS_INBOUND
MODE_OUTBOUND = win32pipe.PIPE_ACCESS_OUTBOUND

READ_SIZE = 65535
ERROR_BROKEN_PIPE = 109

class PipeAlreadyExistsError(Exception): pass

class Server(threading.Thread):
    """
        Instantiate this class with pipe name to create a named pipe.
    """

    def __init__(self, name):
        """
                Initializes a new named pipe.

                :param name: Name of the pipe.
                :type name: str
        """

        super().__init__()
        self.daemon = True
        self.name = name
        self.openMode = MODE_DUPLEX
        self.max = 1
        self.outsize = 65535
        self.insize = 65535
        self.handle = None
        self.should_exit = False
        self.onConnect = None
        self.onReceive = None
        self.onDisconnect = None
        self.onReopen = None
        self.get_buffer = []
        self.decodeOption="replace"
        self._setupDecoder()
        self._openPipe()

    def _setupDecoder(self):
        """Internal function to setup decoder."""
        self.decoder = codecs.getincrementaldecoder("UTF-8")(errors = self.decodeOption)

    def setConnectCallback(self, callable):
        """
                Set a callback triggered when a client connects.

                :param callable: Callback function to call.
                :type callable: callable
        """
        self.onConnect = callable

    def setReceiveCallback(self, callable):
        """
                Set a callback triggered when this server receives data.

                :param callable: Callback function to call.
                :type callable: callable
        """
        self.onReceive = callable

    def setDisconnectCallback(self, callable):
        """
                Set a callback triggered when the client disconnects. After triggering this callback, this module recreates pipe.

                :param callable: Callback function to call.
                :type callable: callable
        """
        self.onDisconnect = callable

    def setReopenCallback(self, callable):
        """
                Set a callback triggered when the pipe is reopened after client disconnection.

                :param callable: Callback function to call.
                :type callable: callable
        """
        self.onReopen = callable

    def _openPipe(self):
        """Internal function to open a named pipe."""
        try:
            self.handle = win32pipe.CreateNamedPipe(
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
        # end except

    def run(self):
        """Thread entry point. Do not call this function maunally."""
        while True:
            self._handleClient()
            if self.should_exit:
                break
            self._handleMessage()
            if self.should_exit:
                break

    def _handleClient(self):
        """Internal function to wait for client connection."""
        overlapped = pywintypes.OVERLAPPED()
        overlapped.hEvent = win32event.CreateEvent(None, 0, 0, None)
        try:
            win32pipe.ConnectNamedPipe(self.handle, overlapped)
        except pywintypes.error as e:
            raise PipeError(e.strerror())
            should_exit = True
            return
        # end except
        while True:
            try:
                size = win32file.GetOverlappedResult(
                    self.handle, overlapped, False)
            except pywintypes.error:
                pass
            if win32event.WaitForSingleObject(overlapped.hEvent, 1000) == win32event.WAIT_OBJECT_0:
                self._handleConnect()
                break
            # end connect
            if self.should_exit:
                break

    def _handleConnect(self):
        """Internal function called when a client connects."""
        if self.onConnect:
            self.onConnect()

    def _handleMessage(self):
        """Internal function to handle incoming messages from the client."""
        while True:
            try:
                resp = win32file.ReadFile(self.handle, READ_SIZE)
            except pywintypes.error as e:
                if e.winerror == winerror.ERROR_NO_DATA:
                    break
                if e.winerror == ERROR_BROKEN_PIPE:
                    if self.onDisconnect:
                        self.onDisconnect()
                    self.reopen()
                    break
                # end if disconnected
            # end except
            msg = self.decoder.decode(resp[1])
            self.get_buffer.append(msg)
            if self.onReceive:
                self.onReceive(msg)
        # end while
    # end _handleClient

    def reopen(self):
        """Reopens this pipe."""
        self.close()
        self._openPipe()
        if self.onReopen:
            self.onReopen()

    def close(self):
        """Closes this named pipe."""
        win32file.CloseHandle(self.handle)

    def getNewMessageList(self):
        """Checks if this pipe has new messages since the last call. Returns None if no message is received."""
        if len(self.get_buffer) == 0:
            return None
        ret=[e for e in self.get_buffer]
        self.get_buffer=[]
        return ret

    def write(self, msg):
        """
            Writes a string data to the pipe.

            :param msg: Message to send.
            :type msg: str
        """
        data = str.encode(f"{msg}")
        win32file.WriteFile(self.handle, data)

    def getFullName(self):
        return "\\\\.\\pipe\\%s" % (self.name)

    def exit(self):
        """Exits the pipe processing. You must call this function to safely exit pipe."""
        self.should_exit = True
        self.join()

    def setDecodeOption(self,option):
        """
            Sets the decode option.
            Please note that calling this method after receiving the data will reset the decoder, so some data may be lost.
        """
        allowed_options = ["strict", "replace", "surrogateescape", "ignore", "backslashreplace"]
        if option not in allowed_options:
            raise ValueError("option must be one of " + " ".join(["\"" + e + "\"" for e in allowed_options]))
        self.decodeOption = option
        self._setupDecoder()
