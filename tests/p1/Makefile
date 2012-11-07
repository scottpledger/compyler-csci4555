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
	gcc -g $(OBJECTS) $*.s -lm
	./a.out < $*.in > $*.out
	python $*.py < $*.in > $*.expected
	diff $*.out $*.expected


TESTS = bool0.py bool1.py assign0.py input0.py \
	ifexp0.py ifexp1.py ifexp2.py ifexp3.py ifexp4.py ifexp5.py \
	and0.py or0.py or1.py not0.py not1.py \
	cmp0.py  eq0.py eq1.py neq0.py \
	dict0.py dict1.py \
	list0.py list1.py list2.py list3.py list4.py \
	list5.py list6.py list7.py \
	is0.py


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
