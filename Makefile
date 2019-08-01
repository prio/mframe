build:
	python setup.py upload

test:
	python mframe_test.py
	TERM=xterm-color jython mframe_test.py	