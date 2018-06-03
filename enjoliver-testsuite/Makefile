CWD=$(shell pwd)


CHAIN_IP_PORT=172.20.0.1:5000
KKK=undionly.kkkpxe
ISO=ipxe.iso

EUID= $(shell id -u -r)
ifneq ($(EUID), 0)
	ROOT=1
endif

PROJECT=$(CWD)/../..
RUNTIME=$(PROJECT)/runtime
RKT=$(RUNTIME)/rkt/rkt

PYTHON=python3

TESTING_RSA=testing.id_rsa


check:
	PYTHONPATH=$(PROJECT) $(PYTHON) -m unittest discover ./


runtime: $(TESTING_RSA)
	$(CWD)/config.py


create_rack0:
	@file $(RKT)
	$(RKT) \
		--local-config=$(CWD) \
		--net=rack0 \
		run --insecure-options=all \
		coreos.com/rkt/stage1-coreos \
		--exec /bin/bash -- -c exit 0

gc:
	-$(RKT) --local-config=$(CWD) gc --grace-period=0s

gci:
	-$(RKT) --local-config=$(CWD) image gc --grace-period=0s

$(TESTING_RSA):
	ssh-keygen -f $(CWD)/$(TESTING_RSA) -t rsa -N ''
	mkdir -vp $(CWD)/test_matchbox/ssh_authorized_keys/
	ln -svf $(CWD)/$(TESTING_RSA).pub $(CWD)/test_matchbox/ssh_authorized_keys/

clean:
	$(RM) $(ISO)
	$(RM) $(KKK)
	$(RM) $(TESTING_RSA)*
	$(RM) -R test_matchbox/ssh_authorized_keys
	$(RM) paths.d/*.json
	$(RM) -R euid/ignition_journal
	$(RM) -R euid/euid.sqlite
	$(RM) -R inte/ignition_journal
	$(RM) -R inte/dbs
	$(RM) -R unit/ignition_journal
	$(RM) -R unit/dbs

fclean: clean gci gc

check_euid_it_plans_enjolivage_disk_2_nodes: runtime
	pytest-3 -x --pdb -v -k TestKVMK8sEnjolivageDisk1

check_euid_it_plans_lifecycle: runtime
	pytest-3 -x --pdb -v -k TestKVMK8SEnjolivageDiskLifecycleLifecycle0

$(KKK):
	@echo Run as USER
	test $(ROOT)
	CHAIN_IP_PORT=$(CHAIN_IP_PORT) make -C $(PROJECT)/chain $(KKK)
	cp -v $(PROJECT)/chain/ipxe/src/bin/$(KKK) $(CWD)/$(KKK)
	file $(KKK)

$(ISO):
	@echo Run as USER
	test $(ROOT)
	CHAIN_IP_PORT=$(CHAIN_IP_PORT) make -C $(PROJECT)/chain $(ISO)
	cp -v $(PROJECT)/chain/ipxe/src/bin/$(ISO) $(CWD)/$(ISO)
	file $(ISO)

re: clean default
