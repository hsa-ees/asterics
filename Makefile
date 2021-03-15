PREFIX = /opt

all: help

.PHONY: help
help:
	@echo "help:        Show this message"
	@echo "update-docs: Rebuild all documentation into ./doc"
	@echo "reset-docs:  Reset all documentation to current state of the git repository"
	@echo "install:     Install ASTERICS on this system."
	@echo "             Use PREFIX=\"path\" to choose installation target. Default is \"/opt/\""

PHONY: update-docs
update-docs:
	$(MAKE) -C ./doc-src update-doxygen-all
	$(MAKE) -C ./doc-src update-doc-free
	$(MAKE) -C ./doc-src veryclean
	

PHONY: reset-docs
reset-docs:
	$(MAKE) -C ./doc-src reset-doxygen-all
	$(MAKE) -C ./doc-src reset-doc-free


PHONY: install
install:
	@echo "Copying files to \"$(PREFIX)/asterics/\" ..."
	mkdir -p $(PREFIX)/asterics/systems
	mkdir -p $(PREFIX)/asterics/bin/ees
	mkdir -p $(PREFIX)/asterics/lib
	cp -r ./doc $(PREFIX)/asterics/
	cp -r ./tools/ees $(PREFIX)/asterics/bin/
	cp ./tools/as-automatics/as_automatics*.py $(PREFIX)/asterics/lib
	cp ./tools/as-automatics/asterics.py $(PREFIX)/asterics/lib
	cp ./tools/as-automatics/packaging.tcl $(PREFIX)/asterics/lib
	cp ./tools/as-automatics/as-module-browser* $(PREFIX)/asterics/bin
	cp ./tools/as-automatics/as-gui $(PREFIX)/asterics/bin
	cp ./tools/as-automatics/gui.ui $(PREFIX)/asterics/lib
	cp ./tools/as-automatics/main_gui.py $(PREFIX)/asterics/lib
	cp -r ./tools/as-automatics/images $(PREFIX)/asterics/lib
	cp -r ./modules $(PREFIX)/asterics
	cp -r ./ipcores $(PREFIX)/asterics
	cp -r ./support $(PREFIX)/asterics
	cp -r ./systems/as_refdesign_zynq $(PREFIX)/asterics/systems
	cp ./systems/README $(PREFIX)/asterics/systems
	cp ./settings.sh $(PREFIX)/asterics
	cp ./README.md $(PREFIX)/asterics
	cp ./LICENSE $(PREFIX)/asterics
	
	@echo ""
	@echo "Installation complete!"
	@echo "To use ASTERICS, the settings file '$(PREFIX)/asterics/settings.sh' must be sourced."
	@echo "For convenience, consider adding the following to your .bashrc or .aliases:"
	@echo "alias source-asterics='source $(PREFIX)/asterics/settings.sh'"


