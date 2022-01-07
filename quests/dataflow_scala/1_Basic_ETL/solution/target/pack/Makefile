
#--------------------------------------------------------------------------
#  Copyright 2012 Taro L. Saito
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
# 
#      http://www.apache.org/licenses/LICENSE-2.0
# 
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#--------------------------------------------------------------------------

PREFIX:=${HOME}/local
INSTALL:=install

.PHONY: all install archive

all: 
	@echo "Run make install"

# program package name
PROG:=ScioLabs

# VERSION file will be generated after 'sbt pack'. This file contains 'version' variable
include VERSION

PROG_BASE_DIR:=$(PREFIX)/$(PROG)
PROG_DIR:=$(PROG_BASE_DIR)/$(PROG)-$(version)

archive: target/$(PROG)-$(version).tar.gz

target/$(PROG)-$(version).tar.gz:
	-mkdir -p $(@D)
	tar --exclude=target/* -cvzf $@ .

install:
	@echo "Clean up $(PROG_DIR)/lib folder"
	if [ -d "$(PROG_DIR)/lib" ]; then rm -rf "$(PROG_DIR)/lib"; fi
	$(INSTALL) -d "$(PROG_DIR)"
	cp -pr ./* "$(PROG_DIR)"
	ln -sfn "$(PROG)-$(version)" "$(PROG_BASE_DIR)/current"
	$(INSTALL) -d "$(PREFIX)/bin"
	ln -sf "../$(PROG)/current/bin/my-pipeline" "$(PREFIX)/bin/my-pipeline"
