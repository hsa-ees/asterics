# Makefile for building and managing ASTERICS documenation

CONF = asterics-manual
TEXFILES = *.tex
FIGURES = figs/01-asterics-example.png figs/cc-by-sa.png figs/hsa_logo.png

.PHONY: all
all: free

.PHONY: help
help:
	@echo "Makefile for building and managing ASTERICS documenation"
	@echo ""
	@echo "Targets:"
	@echo "help: Show this message."
	@echo ""
	@echo "ASTERICS book targets:"
	@echo "free: Build the ASTERICS book. This is the default target."
	@echo "full: Build the ASTERICS book including internal modules/code."
	@echo "    Only available from the nonfree repository."
	@echo "view[-full]: Open the PDF using evince."
	@echo "update-doc-free: Copy the PDF to the asterics/doc folder."
	@echo "update-doc-full: Copy the internal PDF to the asterics/doc folder." 
	@echo "reset-doc-free: Use Git to rollback the PDF to the current commit."
	@echo "reset-doc-full: Use Git to rollback the internal PDF to the current commit."
	@echo "clean: Remove build artifacts from the LaTeX building process."
	@echo "veryclean: Remove everything but the LaTeX source files."
	@echo ""
	@echo "Doxygen targets:"
	@echo "update-doxygen-[c, python, vhdl]: Run Doxygen for C/Python/VHDL code."
	@echo "update-doxygen-all: Run Doxygen for all three languages."
	@echo "view-doxygen-[c, python, vhdl]: Open the Doxygen documentation for "
	@echo "    C/Python/VHDL code using firefox."
	@echo "reset-doxygen-[c, python, vhdl]: Use Git to rollback all files for"
	@echo "    the C/Python/VHDL Doxygen documentation to the current commit."
	@echo "reset-doxygen-all: Use Git to rollback all Doxygen documentation files"
	@echo "    to the current commit."


# Set default targets for typing only "make" on command line
.PHONY: free
free:
	cd ./manual ;\
	make free

.PHONY: full
full:
	cd ./manual ;\
	make full

# View the generated output:
.PHONY: view
view: free
	cd manual ; \
	evince $(CONF).pdf &

.PHONY: view-full
view-full:  full
	cd manual ; \
	evince $(CONF)-full.pdf &

.PHONY: update-doc-free
update-doc-free: free
	cp manual/$(CONF).pdf ../doc/
	@echo "'asterics/doc/$(CONF).pdf' has been updated!"

.PHONY: update-doc-full
update-doc-full: full
	cp manual/$(CONF)-full.pdf ../doc/
	@echo "'asterics/doc/$(CONF)-full.pdf' has been updated!"

.PHONY: reset-doc-free
reset-doc-free:
	git checkout -- ./../doc/$(CONF).pdf

.PHONY: reset-doc-full
reset-doc-full:
	git checkout -- ./../doc/$(CONF)-full.pdf

# Remove all byproducts of building the LaTeX manual
.PHONY: clean
clean:
	cd manual ; \
	make clean

# Remove all output products of building the LaTeX manual
.PHONY: veryclean
veryclean: clean
	cd manual ; \
	make veryclean

.PHONY: reset-doxygen-all
reset-doxygen-all: reset-doxygen-c reset-doxygen-python reset-doxygen-vhdl

.PHONY: reset-doxygen-c
reset-doxygen-c:
	git checkout -- ./../doc/C_doxygen/**

.PHONY: reset-doxygen-python
reset-doxygen-python:
	git checkout -- ./../doc/Python_doxygen/**

.PHONY: reset-doxygen-vhdl
reset-doxygen-vhdl:
	git checkout -- ./../doc/VHDL_doxygen/**

.PHONY: view-doxygen-c
view-doxygen-c:
	firefox ./../doc/C_doxygen/html/index.html

.PHONY: view-doxygen-python
view-doxygen-python:
	firefox ./../doc/Python_doxygen/html/index.html

.PHONY: view-doxygen-vhdl
view-doxygen-vhdl:
	firefox ./../doc/VHDL_doxygen/html/index.html

.PHONY: update-doxygen-all
update-doxygen-all: update-doxygen-c update-doxygen-python update-doxygen-vhdl
	echo "Done"

.PHONY: update-doxygen-c
update-doxygen-c:
	rm -rf ../doc-src/C_doxygen/*
	cd ./c ; \
	doxygen Doxyfile

.PHONY: update-doxygen-python
update-doxygen-python:
	rm -rf ../doc-src/Python_doxygen/*
	cd ./python ; \
	doxygen ./Doxyfile

.PHONY: update-doxygen-vhdl
update-doxygen-vhdl:
	rm -rf ../doc-src/VHDL_doxygen/*
	cd ./vhdl ; \
	doxygen ./Doxyfile


