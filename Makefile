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
	@./dc.sh _dc_build bombe-lab  \
                           techiaith \
                           lab/supervisord.conf experiments/config \
                           experiments/{logs,config} notebooks

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
	@./dc.sh _dc_build bombe-server \
                           techiaith \
                           server/supervisord.conf server-config \
                           server-{config,logs,models}

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
