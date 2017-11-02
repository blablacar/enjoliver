default:
	@echo targets: venv pip clean

venv:
	[[ -d bin ]] || python3.6 -mvenv . | true

pip: venv
	bin/pip install -U setuptools
	bin/pip install -Ur requirements.txt

clean:
	rm -rf bin lib include share pyvenv.cfg
