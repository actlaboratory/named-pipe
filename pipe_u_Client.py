import sys
import win32pipe, win32file, pywintypes
import winerror

AUTO_CLOSE = 2001
NO_AUTO_CLOSE = 2000

def writeToServer(name, message):
    try:
        return client(name).write(message, AUTO_CLOSE)
    except:
        return False


class client():
    def __init__(self, name):
        try:
            self.handle = win32file.CreateFile(
                "\\\\.\\pipe\\" + name,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0,
                None,
                win32file.OPEN_EXISTING,
                0,
                None
            )
        except pywintypes.error as e:
            if e.winerror == winerror.ERROR_FILE_NOT_FOUND:
                raise PipeServerNotFoundError(e.strerror)
            else:
                raise e
        res = win32pipe.SetNamedPipeHandleState(self.handle, win32pipe.PIPE_READMODE_MESSAGE, None, None)
        if res == 0:
            raise PipeError("Create NamedPipeClient process is failed.")

    def read(self, mode = NO_AUTO_CLOSE):
        returnMessage = ""
        try:
            while True:
                resp = win32file.ReadFile(handle, 64*1024)
                if resp[0] == 0:
                    returnMessage += resp[1]
                else:
                    returnMessage += resp[1]
                    break
        except:
            return False
        if mode == AUTO_CLOSE:
            win32file.CloseHandle(self.handle)
        return returnMessage

    def write(self, message, mode = NO_AUTO_CLOSE):
        try:
            data = str.encode(f"{message}")
            win32file.WriteFile(self.handle, data)
            if mode == AUTO_CLOSE:
                win32file.CloseHandle(self.handle)
            return True
        except:
            return False

class PipeServerNotFoundError(Exception): pass
class PipeBusyError(Exception): pass
class PipeError(Exception):
    pass

if __name__ == '__main__':
    c = client("testpipe")
    print("create Client (OK)")
    c.write("aaaaaaa")
    print("write (OK)")
