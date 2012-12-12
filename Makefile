ZIP_OUTFILE=submit.zip
ZIP_EXCLUDE=tests ForPrinting original

TEX_TEXFILE=pydocs.tex
TEX_EXTRAFL=pydocs.toc pydocs.tex.backup pydocs.aux pydocs.log pydocs.pdf

P0_FILES_PY=$(shell find ./tests/p0/ -name '*.py')
P0_FILES_AS=${P0_FILES_PY:%.py=%.s}
P1_FILES_PY=$(shell find ./tests/p1/ -name '*.py')
P1_FILES_AS=${P1_FILES_PY:%.py=%.s}
P2_FILES_PY=$(shell find ./tests/p2/ -name '*.py')
P2_FILES_AS=${P2_FILES_PY:%.py=%.s}
P3_FILES_PY=$(shell find ./tests/p3/ -name '*.py')
P3_FILES_AS=${P3_FILES_PY:%.py=%.s}

%.s: %.py
	python compiler.py $*.py

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
clean: clean-submit


	
gen-asm-p0: ${P0_FILES_AS}
gen-asm-p1: ${P1_FILES_AS}
gen-asm-p2: ${P2_FILES_AS}
gen-asm-p3: ${P3_FILES_AS}

gen-asm-tests: gen-asm-p0 gen-asm-p1 gen-asm-p2 gen-asm-p3
	
