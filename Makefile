build:
	python setup.py upload

test:
	TERM=xterm-color jython mframe_test.py	
	python mframe_test.py

testci:
ifneq ($(wildcard ~/jython/.*),)
	TERM=xterm-color ~/jython/bin/jython mframe_test.py
else
	python mframe_test.py
endif