#ifndef _gc_h_
#define _gc_h_

#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
extern void* gc_malloc(int size);
extern void* py_alloc(int o_size,int p_size,int num);

//
// These definitions describe the "root set" or the pointers
// into the allocated heap.
//
// We define a limited number of pointers into the root set
// and in general, a system would identify global and local
// variables that are pointers.
//

#define ROOT_SET_LENGTH 1024
#define ROOT_SET_NULL   NULL
extern void *root_set[ROOT_SET_LENGTH];

//
// Each object that is allocated is marked with a specific "type"
// The type indicates the size of the object and offset of up
// to 16 pointers in the object. The location of the pointers
// is expressed using an offset from the (user) part of the
// object in terms of integratl 4-byte offsets. For example,
// 0 means 0 bytes, 1 means 4 bytes, 2 means 8 bytes and so on.
//

#define GC_TYPE_INFO_MAX_POINTERS 16
typedef struct {
  int size_in_bytes;  
  int pointers[GC_TYPE_INFO_MAX_POINTERS];
  int tenured;
  //
  // you can add additional fields to the gc_type_info as you
  // see fit. Some example might include pointers for a
  // freelist of items (should that be useful).
  //
} gc_type_info;


void gc_nullify(int * index);

//
// The gc_init() routine should be called before anything is allocated.
// This is used to initialize your code & data structures.
//
extern void gc_init();


//
// Allocate an object of the appropriate type and return a pointer to
// the user portion of the space. The returned address should be
// aligned for a double (i.e. 8 byte aligned).
//
extern void *gc_alloc(gc_type_info *);


//
// This routine inserts a check that the returned item is 8-byte aligned
// (the bottom 3 bits are zero);
// 
static inline void *gc_alloc_check(gc_type_info *info)
{
  void *ret = gc_alloc(info);
  int iret = (int) ret;
  if ( (iret & 0x7) != 0 ) {
    fprintf(stderr,"Allocation of object not 8-byte aligned\n");
    exit(1);
  }
  return ret;
}


//
// Start a collection phase. This can be called by the user program
// but your garbage collector is free to do whatever it wants when
// this is called.
//
extern void gc_collect();


//
// Returns an eight byte alligned size value based on the size value
// in passed gc_type_info *
//
extern int size_in_bytes(gc_type_info *);


//
// returns 1 if there is enough room for payload + type meta-data
// returns 0 if not
//
extern int have_room(gc_type_info *);


//
// takes pointer to an object, copys that object to heap, then returns
// the new pointer to that object
//
extern int * gc_copy(int *);

extern void gc_collect_all();

#endif
