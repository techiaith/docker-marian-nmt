SHELL := /usr/bin/bash
UID ?= $(shell id -u)
GID ?= $(shell getent group docker | cut -d: -f3)

define print-help
	$(if $(need-help),$(info $1 -- $2))
endef

need-help := $(filter help,$(MAKECMDGOALS))

help: ; @echo $(if $(need-help),,Type \'$(MAKE)$(dash-f) help\' to get help)

setup-hunspell: $(call print-help,setup-hunspell,Configure hunspell dictionaries.)
	@mkdir -p -m 770 dictionaries
	@./setup-hunspell-dictionaries.sh dictionaries

lab-build: $(call print-help,lab-build,Builds the docker container for the bombe Lab.) setup-hunspell
	@mkdir -p -m 770 experiments/{logs,config} notebooks
	@chown -R ${UID}:${GID} experiments/{logs,config} notebooks
	@./dc.sh _dc build bombe-lab \
                     --build-arg uid=${UID} \
                     --build-arg gid=${GID} \
                     --build-arg app_user=techiaith \
                     --force-rm

lab-build-release: $(call print-help,server-release-build,Build docker image for release.)
	@mkdir -p -m 770 experiments/{logs,config} notebooks
	@chown -R ${UID}:${GID} experiments/{logs,config} notebooks
	@cd lab; python setup.py bdist_wheel -d ${PWD}/lab
	@./dc.sh _dc build bombe-lab \
                     --build-arg uid=${UID} \
                     --build-arg gid=${GID} \
                     --build-arg app_user=techiaith \
                     --build-arg release_wheel=techiaith_marian_nmt_lab-${VERSION}-py3-none-any.whl \
                     --force-rm
	-rm -f lab/*.whl

lab-restart: $(call print-help,lab-restart,Restart the NMT lab.)
	@./dc.sh _dc restart bombe-lab

lab-run: $(call print-help,lab-run,Run the NMT Lab.)
	@./dc.sh _dc_up bombe-lab

lab-status: $(call print-help,lab-status,Show the status of the NMT Lab.)
	@./dc.sh _dc ps bombe-lab

lab-stop: $(call print-help,lab-stop,Stop the NMT Lab.)
	@./dc.sh _dc stop bombe-lab

lab-supervisor: $(call print-help,lab-supervisor,Access superverisorctl on the NMT lab.)
	@./dc.sh supervisorctl bombe-lab ${SUPERVISORCTL_ARGS}

server-build: $(call print-help,server-build,Builds the docker container for the server.)
	@mkdir -p -m 770 server-models
	@chown -R ${UID}:${GID} server-models
	@./dc.sh _dc build bombe-server \
                     --build-arg uid=${UID} \
                     --build-arg gid=${GID} \
                     --build-arg app_user=techiaith \
                     --force-rm

server-build-release: $(call print-help,server-release-build,Build docker image for release.)
	@mkdir -p -m 770 server-{config,logs,models}
	@chown -R ${UID}:${GID} server-{config,logs,models}
	@cd server; python setup.py bdist_wheel -d ${PWD}/server
	@./dc.sh _dc build bombe-server \
                     --build-arg uid=${UID} \
                     --build-arg gid=${GID} \
                     --build-arg app_user=techiaith \
                     --build-arg release_wheel=techiaith_marian_nmt_api-${VERSION}-py3-none-any.whl
	-rm -f server/*.whl

server-run: $(call print-help,server-run,Run the API server.)
	@./dc.sh _dc up --remove-orphans -d bombe-server

server-status: $(call print-help,server-status,Show the status of the API server.)
	@./dc.sh _dc ps bombe-server

server-stop: $(call print-help,server-stop,Stop the API server.)
	@./dc.sh _dc stop bombe-server

server-restart: $(call print-help,server-restart,Restart the API server.)
	@./dc.sh _dc restart bombe-server

server-supervisor: $(call print-help,server-supervisor,Access superverisorctl on the API server.)
	@./dc.sh supervisorctl bombe-server
