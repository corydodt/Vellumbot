
start:
	hg serve --daemon --port 28092 --pid-file hgserve.pid

stop:
	kill `cat hgserve.pid`

buildable: VERSION := $(shell hg tags | head -2 | grep -v tip | cut -d\  -f1 || echo '')
buildable: PNAME := python-vellumbot-"$(VERSION)"
buildable:
	cd ..; cp -a Vellumbot $(PNAME); \
			cd $(PNAME)/; hg purge --all; rm -rf .hg; \
			cd ..; tar cvfz $(PNAME).tar.gz $(PNAME)/

tests:
	@if ! which trial >/dev/null 2>&1;then echo "** Install Twisted" 1>&2;  exit 1; fi
	trial vellumbot.test
