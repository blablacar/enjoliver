PYTHON=python3.5

default:
	@echo targets: venv clean

venv: bin/activate bin/pip

bin/activate:
	$(PYTHON) -mvenv .
	
bin/pip: requirements.txt
	$@ install -U wheel setuptools
	$@ install -Ur $<
	touch $@

clean:
	$(RM) -r bin lib lib64 include share pyvenv.cfg
