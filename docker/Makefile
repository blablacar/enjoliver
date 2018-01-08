DOCKER=docker
NAME=enjoliver-garage
REPO=shtouff
TAGS=latest v0.0.1

help:
	@echo Available targets are:
	@$(MAKE) list

build:
	$(DOCKER) build . -t $(NAME)

run:
	$(DOCKER) run $(NAME)

run-bash:
	$(DOCKER) run -ti $(NAME) /bin/bash

tag-targets = $(addprefix tag-, $(TAGS))
tag: $(tag-targets)
$(tag-targets): tag-%:
	$(DOCKER) tag $(NAME) $(REPO)/$(NAME):$*

push-targets = $(addprefix push-, $(TAGS))
push: $(push-targets)
$(push-targets): push-%:
	$(DOCKER) push $(REPO)/$(NAME):$*

list:
	@echo build run run-bash tag $(tag-targets) push $(push-targets)
