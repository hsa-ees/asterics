# Simple Makefile to build the ASTERICS manual.
CONF = asterics-manual
TEXFILES = *.tex
FIGURES = figs/01-asterics-example.png figs/cc-by-sa.png figs/hsa_logo.png

# Set default targets for typing only "make" on command line
.PHONY: free
free: $(CONF).pdf
.PHONY: full
full: $(CONF)-full.pdf

# Build the asterics-manual without internal repositories
$(CONF).pdf: $(TEXFILES) $(FIGURES) $(BIBFILES)
	pdflatex $(CONF).tex ; \
	bibtex $(CONF) ; \
	pdflatex $(CONF).tex ; \
	pdflatex $(CONF).tex

# Build the asterics-manual, including internal repositories
$(CONF)-full.pdf: $(TEXFILES) $(FIGURES) $(BIBFILES)
	pdflatex -jobname $(CONF)-full "\def\astericsinternal{1} \input{asterics-manual.tex}" $(CONF).tex ; \
	bibtex $(CONF) ; \
	pdflatex -jobname $(CONF)-full "\def\astericsinternal{1} \input{asterics-manual.tex}" $(CONF).tex ; \
	pdflatex -jobname $(CONF)-full "\def\astericsinternal{1} \input{asterics-manual.tex}" $(CONF).tex

clean:
	rm -f *.out *.idx *.aux *.bbl *.blg *.log $(CONF).synctex.gz *.run.xml *.toc *-blx.bib


veryclean: clean
	rm -f $(CONF).pdf $(CONF)-full.pdf