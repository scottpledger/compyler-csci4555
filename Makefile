ZIP_OUTFILE=submit.zip
ZIP_EXCLUDE=tests ForPrinting original

TEX_TEXFILE=pydocs.tex
TEX_EXTRAFL=pydocs.toc pydocs.tex.backup pydocs.aux pydocs.log pydocs.pdf

P0_FILES_PY=$(shell find ./tests/p0/ -name '*.py')
P0_FILES_AS=${P0_FILES_PY:%.py=%.s}
P0_FILES_EX=${P0_FILES_PY:%.py=%.out}
P1_FILES_PY=$(shell find ./tests/p1/ -name '*.py')
P1_FILES_AS=${P1_FILES_PY:%.py=%.s}
P1_FILES_EX=${P1_FILES_PY:%.py=%.out}
P2_FILES_PY=$(shell find ./tests/p2/ -name '*.py')
P2_FILES_AS=${P2_FILES_PY:%.py=%.s}
P2_FILES_EX=${P2_FILES_PY:%.py=%.out}
P3_FILES_PY=$(shell find ./tests/p3/ -name '*.py')
P3_FILES_AS=${P3_FILES_PY:%.py=%.s}
P3_FILES_EX=${P3_FILES_PY:%.py=%.out}
RUNTIME_FILES=$(shell find ./ -maxdepth 1 -name '*.c')
RUNTIME_HDRS =$(shell find ./ -maxdepth 1 -name '*.h')
RUNTIME_FILES_LIB=${RUNTIME_FILES:%.c=%.o}
RUNTIME_FILES_LINK=${RUNTIME_FILES_LIB:./%.o=-l%}
PWD=$(shell pwd)


GCC_INCLUDES= -I. ${RUNTIME_HDRS}
GCC_LINKS = -L. -lcompyler -lm

%.o: %.c
	gcc -c -fPIC -m32 $*.c -o $*.o
	
runtime-files: ${RUNTIME_FILES_LIB}
	gcc -shared -m32 -lm -Wl,--as-needed,-soname,libcompyler.so -o libcompyler.so  ${RUNTIME_FILES_LIB}
	
	

%.s: %.py
	python compile.py $*.py

%.out: %.s runtime-files
	gcc -m32 $*.s -o $*.bin -O -g  $(GCC_LINKS)
	

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

clean-all: clean-pydocs clean-submit clean-asm-p0 clean-asm-p1 clean-asm-p2 clean-asm-p3 clean-runtime-files
all: submit pydocs
clean: clean-submit


clean-runtime-files:
	rm -f *.o
	rm -f *.so*
	
gen-asm-p0: ${P0_FILES_AS}

gen-exe-p0: ${P0_FILES_EX}

clean-asm-p0:
	rm -f ./tests/p0/*.s
	
gen-asm-p1: ${P1_FILES_AS}

gen-exe-p1: ${P1_FILES_EX}

clean-asm-p1:
	rm -f ./tests/p1/*.s
	
gen-asm-p2: ${P2_FILES_AS}

gen-exe-p2: ${P2_FILES_EX}

clean-asm-p2:
	rm -f ./tests/p2/*.s
	
gen-asm-p3: ${P3_FILES_AS}

gen-exe-p3: ${P3_FILES_EX}

clean-asm-p3:
	rm -f ./tests/p3/*.s
	

gen-asm-tests: gen-asm-p0 gen-asm-p1 gen-asm-p2 gen-asm-p3

gen-exe-tests: gen-exe-p0 gen-exe-p1 gen-exe-p2 gen-exe-p3


	
