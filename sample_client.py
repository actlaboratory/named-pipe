# -*- coding: utf-8 -*-
# namedPipe sample client
#Copyright (C) 2020 Yukio Nozawa <personal@nyanchangames.com>
import namedPipe
import time

pipeClient=namedPipe.Client("testpipe")
pipeClient.connect()
print("pipe connected.")
time.sleep(3)
pipeClient.disconnect()
print("disconnected.")
