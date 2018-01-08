CWD=$(shell pwd)

PROJECT=$(CWD)/../../
RUNTIME=$(PROJECT)/runtime
RKT=$(RUNTIME)/rkt/rkt
ACI=$(PROJECT)/aci


FLEET=fleet
DEBIAN=debian
GO=go
UPX=upx
BUILDER_HYPERKUBE=builder-hyperkube
HYPERKUBE=hyperkube

default: push

$(DEBIAN):
	@echo ENV IMAGE=$(ACI)/aci-$(DEBIAN)
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) install
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) push

$(GO): $(DEBIAN)
	@echo ENV IMAGE=$(ACI)/aci-$(GO)
	IMAGE=$(ACI)/aci-$(GO) make -C $(RUNTIME) install
	IMAGE=$(ACI)/aci-$(GO) make -C $(RUNTIME) push

$(BUILDER_HYPERKUBE): $(GO)
	@echo ENV IMAGE=$(ACI)/aci-$(BUILDER_HYPERKUBE)
	IMAGE=$(ACI)/aci-$(BUILDER_HYPERKUBE) make -C $(RUNTIME) install
	IMAGE=$(ACI)/aci-$(DEBIAN) make -C $(RUNTIME) push
	IMAGE=$(ACI)/aci-$(BUILDER_HYPERKUBE) make -C $(RUNTIME) push

build: $(BUILDER_HYPERKUBE)
	@echo ENV IMAGE=$(ACI)/aci-$(FLEET)
	IMAGE=$(ACI)/aci-$(FLEET) make -C $(RUNTIME) build

test: build
	@echo ENV IMAGE=$(ACI)/aci-$(FLEET)
	IMAGE=$(ACI)/aci-$(FLEET) make -C $(RUNTIME) test

push: test
	@echo ENV IMAGE=$(ACI)/aci-$(RKT_ACI)
	IMAGE=$(ACI)/aci-$(FLEET) make -C $(RUNTIME) push

gc:
	$(RKT) --local-config=$(RUNTIME) gc --grace-period=0s
	$(RKT) --local-config=$(RUNTIME) image gc --grace-period=0s

clean: gc
	IMAGE=$(ACI)/aci-$(FLEET) make -C $(RUNTIME) clean

fclean: clean

re: clean default
