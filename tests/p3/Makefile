# -*- makefile -*-

.SUFFIXES: .py .s .out .bc .ll

COMPILER = ../hw6.py

OBJECTS = runtime.o hashtable.o hashtable_itr.o hashtable_utility.o

.py.s:
#	figleaf $(COMPILER) $*.py > $*.s
	python $(COMPILER) $*.py

.py.ll:
	python $(COMPILER) $*.py > $*.ll

.ll.bc:
	llvm-as $*.ll

.bc.s:
	llc $*.bc -o $*.s

.s.out:
	gcc -g $(OBJECTS) $*.s
	./a.out < $*.in > $*.out
	python $*.py < $*.in > $*.expected
	diff $*.out $*.expected

TESTS = class0.py class1.py class2.py class3.py class4.py class5.py class6.py \
	class7.py class8.py class9.py \
	obj0.py obj1.py obj2.py obj3.py \
	method0.py method1.py \
	ifstmt0.py ifstmt1.py \
	while0.py while1.py while2.py

TESTS_S = $(TESTS:.py=.s)

TESTS_OUT = $(TESTS_S:.s=.out)


default: $(OBJECTS) $(TESTS_OUT) 
#	figleaf2html -d figlear-out .figleaf

runtime.o:
	gcc -g -c ../runtime.c

hashtable.o:
	gcc -g -c ../hashtable.c

hashtable_itr.o:
	gcc -g -c ../hashtable_itr.c

hashtable_utility.o:
	gcc -g -c ../hashtable_utility.c




clean:
	rm -f *.s
	rm -f .figleaf
	rm -f *.out
	rm -f *.expected
	rm -f *.bc
	rm -f *.ll
	rm -f *.o
