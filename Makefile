ZIP_OUTFILE=submit.zip
ZIP_EXCLUDE=tests ForPrinting original

TEX_TEXFILE=pydocs.tex
TEX_EXTRAFL=pydocs.toc pydocs.tex.backup pydocs.aux pydocs.log pydocs.pdf

P0_FILES_PY=$(shell find ./tests/p0/ -name '*.py')
P0_FILES_AS=${P0_FILES_PY:%.py=%.s}
P0_FILES_EX=${P0_FILES_PY:%.py=%.bin}
P1_FILES_PY=$(shell find ./tests/p1/ -name '*.py')
P1_FILES_AS=${P1_FILES_PY:%.py=%.s}
P1_FILES_EX=${P1_FILES_PY:%.py=%.bin}
P2_FILES_PY=$(shell find ./tests/p2/ -name '*.py')
P2_FILES_AS=${P2_FILES_PY:%.py=%.s}
P2_FILES_EX=${P2_FILES_PY:%.py=%.bin}
P3_FILES_PY=$(shell find ./tests/p3/ -name '*.py')
P3_FILES_AS=${P3_FILES_PY:%.py=%.s}
P3_FILES_EX=${P3_FILES_PY:%.py=%.bin}
RUNTIME_FILES=$(shell find ./ -maxdepth 1 -name '*.c')
RUNTIME_HDRS =$(shell find ./ -maxdepth 1 -name '*.h')
RUNTIME_FILES_LIB=${RUNTIME_FILES:%.c=%.o}
RUNTIME_FILES_LINK=${RUNTIME_FILES_LIB:./%.o=-l%}
PWD=$(shell pwd)


GCC_INCLUDES= -I. ${RUNTIME_HDRS}
GCC_LINKS = -L. -lcompyler -lm

%.o: %.c
	gcc -c -fPIC -m32 -g $*.c -o $*.o
	
runtime-files: ${RUNTIME_FILES_LIB}
	gcc -shared -m32 -lm -Wl,--as-needed,-soname,libcompyler.so -o libcompyler.so  ${RUNTIME_FILES_LIB}

%.s: %.py
	python compile.py $*.py

%.bin: %.s runtime-files
	gcc -m32 $*.s -o $*.bin -O -g $(GCC_LINKS)
	

pydocs:
	pdflatex $(TEX_TEXFILE)
	pdflatex $(TEX_TEXFILE)
	pdflatex $(TEX_TEXFILE)
	pdflatex $(TEX_TEXFILE)


clean-pydocs:
	rm -f $(TEX_EXTRAFL)

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

clean-exe-p0:
	rm -f ./tests/p0/*.bin
	rm -f ./tests/p0/*.ast
	rm -f ./tests/p0/*.apy
	rm -f ./tests/p0/*.err
	rm -f ./tests/p0/*.out
	rm -f ./tests/p0/*.pst

gen-asm-p1: ${P1_FILES_AS}

gen-exe-p1: ${P1_FILES_EX}

clean-asm-p1:
	rm -f ./tests/p1/*.s

clean-exe-p1:
	rm -f ./tests/p1/*.bin
	rm -f ./tests/p1/*.ast
	rm -f ./tests/p1/*.apy
	rm -f ./tests/p1/*.err
	rm -f ./tests/p1/*.out
	rm -f ./tests/p1/*.pst

gen-asm-p2: ${P2_FILES_AS}

gen-exe-p2: ${P2_FILES_EX}

clean-asm-p2:
	rm -f ./tests/p2/*.s

clean-exe-p2:
	rm -f ./tests/p2/*.bin
	rm -f ./tests/p2/*.ast
	rm -f ./tests/p2/*.apy
	rm -f ./tests/p2/*.err
	rm -f ./tests/p2/*.out
	rm -f ./tests/p2/*.pst

gen-asm-p3: ${P3_FILES_AS}

gen-exe-p3: ${P3_FILES_EX}

clean-asm-p3:
	rm -f ./tests/p3/*.s

clean-exe-p3:
	rm -f ./tests/p3/*.bin
	rm -f ./tests/p3/*.ast
	rm -f ./tests/p3/*.apy
	rm -f ./tests/p3/*.err
	rm -f ./tests/p3/*.out
	rm -f ./tests/p3/*.pst


gen-asm-tests: gen-asm-p0 gen-asm-p1 gen-asm-p2 gen-asm-p3

gen-exe-tests: gen-exe-p0 gen-exe-p1 gen-exe-p2 gen-exe-p3

clean-tests-exe: clean-exe-p0 clean-exe-p1 clean-exe-p2 clean-exe-p3

clean-tests-asm: clean-asm-p0 clean-asm-p1 clean-asm-p2 clean-asm-p3

clean-tests: clean-tests-exe clean-tests-asm
	rm -f ./tests/*/*.out
	rm -f ./tests/*/*.err

P0_TEST_IN  = ${P0_FILES_PY:%.py=%.in}
P0_TEST_EXP = ${P0_FILES_PY:%.py=%.expected}
P1_TEST_IN  = ${P1_FILES_PY:%.py=%.in}
P1_TEST_EXP = ${P1_FILES_PY:%.py=%.expected}
P2_TEST_IN  = ${P2_FILES_PY:%.py=%.in}
P2_TEST_EXP = ${P2_FILES_PY:%.py=%.expected}
P3_TEST_IN  = ${P3_FILES_PY:%.py=%.in}
P3_TEST_EXP = ${P3_FILES_PY:%.py=%.expected}

%.in:
	wget -O $*.in http://csci4555.cs.colorado.edu/test_$(shell basename $(shell dirname $*) )/$(shell basename $*).in
	

%.expected:
	rm -f $*.expected
	python $*.py >> $*.expected
	

get-tests-p%:
	rm -fR ./tests/p$*/*
	wget -P ./tests/p$*/ -i ./tests/p$*.list

get-tests: get-tests-p0 get-tests-p1 get-tests-p2 get-tests-p3

get-test-data-p0: ${P0_TEST_IN} ${P0_TEST_EXP}
get-test-data-p1: ${P1_TEST_IN} ${P1_TEST_EXP}
get-test-data-p2: ${P2_TEST_IN} ${P2_TEST_EXP}
get-test-data-p3: ${P3_TEST_IN} ${P3_TEST_EXP}

get-test-data: get-test-data-p0 get-test-data-p1 get-test-data-p2 get-test-data-p3