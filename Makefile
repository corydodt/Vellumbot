
start:
	hg serve --daemon --port 28092 --pid-file hgserve.pid

stop:
	kill `cat hgserve.pid`
