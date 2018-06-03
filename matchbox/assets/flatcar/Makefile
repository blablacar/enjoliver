VERSION=1632.3.0

SERVE=serve

CHANNEL=https://stable.release.flatcar-linux.net/amd64-usr
VMLINUZ=flatcar_production_pxe.vmlinuz
CPIO=flatcar_production_pxe_image.cpio.gz
TXT=version.txt
BZ2=flatcar_production_image.bin.bz2

KERNEL=$(addprefix $(VERSION)/, $(VMLINUZ))
INITRD=$(addprefix $(VERSION)/, $(CPIO))
TEXT_VERSION=$(addprefix $(VERSION)/, $(TXT))
IMAGE=$(addprefix $(VERSION)/, $(BZ2))

ASC=Flatcar_Image_Signing_Key.asc

KEY=$(addprefix $(VERSION)/, $(ASC))
GPG=gpg

default: $(KEY) $(KERNEL) $(INITRD) $(TEXT_VERSION) $(IMAGE) alter

$(VERSION):
	test $(VERSION)
	mkdir -pv $(VERSION)

$(KEY): $(VERSION)
	curl -Lf https://flatcar-linux.org/security/image-signing-key/$(ASC) -o $(KEY)
	$(GPG) --logger-fd 1 --import < $(KEY)

$(KERNEL): $(KEY) $(VERSION)
	curl -Lf $(CHANNEL)/$(KERNEL) -o $(KERNEL)
	curl -Lf $(CHANNEL)/$(KERNEL).sig -o $(KERNEL).sig
	$(GPG) --logger-fd 1 --verify $(KERNEL).sig

$(INITRD): $(KEY) $(VERSION)
	curl -Lf $(CHANNEL)/$(INITRD) -o $(INITRD)
	curl -Lf $(CHANNEL)/$(INITRD).sig -o $(INITRD).sig
	$(GPG)  --logger-fd 1 --verify $(INITRD).sig

$(TEXT_VERSION): $(VERSION)
	curl -Lf $(CHANNEL)/$(TEXT_VERSION) -o $(TEXT_VERSION)

$(IMAGE):
	curl -Lf $(CHANNEL)/$(IMAGE) -o $(IMAGE)
	curl -Lf $(CHANNEL)/$(IMAGE).sig -o $(IMAGE).sig
	$(GPG) --logger-fd 1 --verify $(IMAGE).sig

ACI_PATH="../../../../../runtime/acserver.d/enjoliver.local"

alter:
	VERSION=$(VERSION) ACI_PATH=$(ACI_PATH) ./alter-distribution.sh
	ln -vsf $(VERSION) $(SERVE)
	ln -vsf $(SERVE) current

clean:
	@rm -rfv $(VERSION) 2>&1 || true

fclean: clean
	@find * -maxdepth 1 -type d -exec rm -Rfv {} \;
	@rm -v $(SERVE) current || true

re: fclean default
