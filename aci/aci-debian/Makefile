CWD=$(shell pwd)

PROJECT=$(CWD)/../..
RUNTIME=$(PROJECT)/runtime
RKT=$(RUNTIME)/rkt/rkt
ACI=$(PROJECT)/aci


DEBIAN=debian
default: push

$(DEBIAN):
	@echo ENV IMAGE=$(ACI)/aci-$@
	IMAGE=$(ACI)/aci-$@ make -C $(RUNTIME) install 
	IMAGE=$(ACI)/aci-$@ make -C $(RUNTIME) push

prepare: $(DEBIAN)

install: prepare
	@echo ENV IMAGE=$(ACI)/aci-$(DEBIAN)
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) install

test: install
	@echo ENV IMAGE=$(ACI)/aci-$(DEBIAN)
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) test

push: test
	@echo ENV IMAGE=$(ACI)/aci-$(DEBIAN)
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) push

gc:
	$(RKT) --local-config=$(RUNTIME) gc --grace-period=0s
	$(RKT) --local-config=$(RUNTIME) image gc --grace-period=0s

clean: gc
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) clean

fclean: clean

re: clean default

re_quick:
	@echo ENV IMAGE=$(ACI)/aci-$(DEBIAN)
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) build
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) push
