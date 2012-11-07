ZIP_OUTFILE=submit.zip
ZIP_EXCLUDE=tests ForPrinting original

TEX_TEXFILE=pydocs.tex
TEX_EXTRAFL=pydocs.toc pydocs.tex.backup pydocs.aux pydocs.log pydocs.pdf

clean-pydocs:
	rm -f $(TEX_EXTRAFL)

pydocs:
	pdflatex $(TEX_TEXFILE)
	pdflatex $(TEX_TEXFILE)
	pdflatex $(TEX_TEXFILE)
	pdflatex $(TEX_TEXFILE)
	

clean-submit:
	rm -f *.pyc *~ *.zip 

submit: clean-submit
	zip $(ZIP_OUTFILE) *
	zip -d $(ZIP_OUTFILE) $(ZIP_EXCLUDE) $(TEX_TEXFILE) $(TEX_EXTRAFL)

clean-all: clean-pydocs clean-submit
all: submit pydocs
	
