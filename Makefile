

clean-pydocs:
	rm -f pydocs.toc pydocs.tex.backup pydocs.aux pydocs.log pydocs.pdf

pydocs:
	pdflatex pydocs.tex
	pdflatex pydocs.tex
	pdflatex pydocs.tex
	pdflatex pydocs.tex
	

clean-submit: clean-pydocs
	rm -f *.pyc *~ *.zip 

submit: clean-submit
	zip submit.zip *

clean-all: clean-pydocs clean-submit
all: submit pydocs
	
