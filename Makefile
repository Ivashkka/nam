#nam_server Makefile
#DO NOT CHANGE ANY OF THIS PARAMETERS, OR YOU WILL NEED TO CHANGE THEM IN nam_server.service, namctl ALSO
DIST_DIR := /usr/local/bin/nam_server
CONF_DIR := /etc/nam_server
SYSD_DIR := /etc/systemd/system
BIN_DIR := /usr/local/bin
VENV_DIR := $(DIST_DIR)/nam_server_venv

CONF_FILES := ./conf.yaml ./users.json
BIN_FILES := ./namctl
SYSD_FILES := ./nam_server.service

SIDE_FILES := $(DIST_DIR)/Makefile $(DIST_DIR)/nam_server.service $(DIST_DIR)/namctl $(DIST_DIR)/LICENSE $(DIST_DIR)/.gitignore $(DIST_DIR)/README.md $(DIST_DIR)/conf.yaml $(DIST_DIR)/users.json
EXEC_FILES := $(BIN_DIR)/namctl
REQ_FILE := $(DIST_DIR)/requirements.txt

CLEAN_LAST := $(SYSD_DIR)/nam_server.service

USER := nam
GROUP := nam

all: install

install:
        echo installing nam_server...
        #cp all files to dist_dir andr rm unnecessary
        mkdir $(DIST_DIR)
        cp -r . $(DIST_DIR)
        rm $(SIDE_FILES)
        #cp other files to system folders
        cp $(BIN_FILES) $(BIN_DIR)
        mkdir $(CONF_DIR)
        cp $(CONF_FILES) $(CONF_DIR)
        cp $(SYSD_FILES) $(SYSD_DIR)
        #create nam user and chown related files
        adduser --system --no-create-home --group $(USER)
        chown -R $(USER):$(GROUP) $(DIST_DIR)
        chown -R $(USER):$(GROUP) $(CONF_DIR)
        chown $(USER):$(GROUP) $(EXEC_FILES)
        #chmod all excecutables
        chmod 755 $(EXEC_FILES)
        #generate venv and install python dependencies
        python3 -m venv $(VENV_DIR)
        $(VENV_DIR)/bin/pip3 install -r $(REQ_FILE)
        systemctl daemon-reload
        echo done
clean:
        #rm all files
        echo uninstalling nam_server...
        systemctl stop nam_server.service
        rm $(EXEC_FILES)
        rm -r $(DIST_DIR)
        rm -r $(CONF_DIR)
        rm $(CLEAN_LAST)
        systemctl daemon-reload
        echo done
