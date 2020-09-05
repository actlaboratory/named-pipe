# -*- coding: utf-8 -*-
# namedPipe sample server
#Copyright (C) 2020 Yukio Nozawa <personal@nyanchangames.com>
import namedPipe
import time

pipeServer=namedPipe.Server("testpipe")
pipeServer.start()
print("Pipe set up. press ctrl+c to stop.")
try:
	while(True):
		time.sleep(10)
except:
	print("Exiting")
	pipeServer.exit()
