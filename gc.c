#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <unistd.h>
#include <string.h>
#include "gc.h"

//
// This file defines the "skeleton" of your garbage collector
// implementation. This version simply uses 'malloc' to
// allocate storage (not a good solution)
//


void *root_set[ROOT_SET_LENGTH] = {ROOT_SET_NULL};

int gc_alloc_slab_counter = 0;

int *start_pointers[1000] = {ROOT_SET_NULL};
int *end_pointers[1000] = {ROOT_SET_NULL};

int * alloc;
int root_alloc = 0;

/*
int * start_pointers[1000];
memset(start_pointers, NULL, 1000);
int * end_pointers[1000];
memset(end_pointers, NULL, 1000);
*/

void print_debug_info(){
  printf("=========DEBUG SHIT========\nstart_pointer[%u]: %u\nalloc: %u\nalloc[0]:%u\nalloc[1]:%u\n==========END DEBUG SHIT==========\n",gc_alloc_slab_counter,start_pointers[gc_alloc_slab_counter],alloc,alloc[0],alloc[1]);
}


void gc_init()
{
	while(start_pointers[gc_alloc_slab_counter] != 0) 	gc_alloc_slab_counter++;
	if(gc_alloc_slab_counter > 999)           //rolls over to 0 "circular array"
		gc_alloc_slab_counter = 0;
	
	int page_size = getpagesize();
	int slab_size = page_size * 10;

	
	start_pointers[gc_alloc_slab_counter] = (int *) mmap(NULL, slab_size, 
		  			PROT_READ | PROT_WRITE, 
		 		 	MAP_ANONYMOUS | MAP_SHARED,
		  			0, 0);
	end_pointers[gc_alloc_slab_counter] = (int *)((int)start_pointers[gc_alloc_slab_counter] + slab_size);
	alloc = start_pointers[gc_alloc_slab_counter];
}

void* py_alloc(int o_size){
    printf("Allocating %d...\n",o_size);
	gc_type_info info = { .size_in_bytes = o_size, .pointers = {0}, .tenured = 0 };
	return gc_alloc(&info);
}

//
// This lamest of lame allocators simply allocates new space.
// If there isn't enough space, we allocate a new slab
//

void* gc_alloc(gc_type_info *info)
{
	//return malloc(info -> size_in_bytes);
	  
	if(!have_room(info))
	{
		gc_collect();
		if(!have_room(info))
			gc_init();
		//return gc_alloc(info);
	}
    printf("=========STRT DEBUG SHIT========\nstart_pointer[%d]: %d\nalloc: %d\nalloc[0]:%d\nalloc[1]:%d\n==========END DEBUG SHIT==========\n",gc_alloc_slab_counter,start_pointers[gc_alloc_slab_counter],alloc,alloc[0],alloc[1]);
	alloc[0] = (int)info;                                              //use interger arithmatic, sets metadata for type
	alloc[1] = (int)NULL;                                              //set meta data for copy pointer
	printf("=========STRT DEBUG SHIT========\nstart_pointer[%d]: %d\nalloc: %d\nalloc[0]:%d\nalloc[1]:%d\n==========END DEBUG SHIT==========\n",gc_alloc_slab_counter,start_pointers[gc_alloc_slab_counter],alloc,alloc[0],alloc[1]);
	alloc = (int *)((int)alloc + size_in_bytes(info) + 8);             //move allocate to the end of the item you just put in

	if(root_alloc < ROOT_SET_LENGTH)
	{
		while(root_set[root_alloc] != ROOT_SET_NULL)
			root_alloc++;
		root_set[root_alloc] = (void *)((int)alloc - size_in_bytes(info));
	} else
	{
		root_alloc = 0;
		return gc_alloc(info);
	}
	return (void *)((int)alloc - size_in_bytes(info));

	//return (void *)((int)alloc - size_in_bytes(info));                 //return front of payload
}

int * gc_copy(int * node)                                                  //takes in ptr to payload
{
	if(node == NULL)                                                   //if no payload return NULL
		return NULL;
	
	if((int *)(((int *)node)[-1]) != NULL)                             //Check if it has been copied or not
		return (void *)(((int *)node)[-1]);                            //Return address of where payload has been copied to
		
	void * new_node = gc_alloc((gc_type_info *)(((int*)node)[-2]));            //Create new Block, saves pointer into new node
	
	memcpy(new_node, node,                                                //Copies over payload into new node
			(size_t)size_in_bytes((gc_type_info *)(((int *)node)[-2])));
	
	int * temp = &((int*)node)[-1];                                    //sets the meta data of the old payload
	*temp = (int)new_node;                                             //to the address of the new payload
	
	temp = &((int*)new_node)[1];                                       //connects the new nodes
	*temp = (int)gc_copy(((int*)((int*)node)[1]));                     //recursive connecting
	
	return new_node;                                                   //return the address of the new_ payload
}


void gc_collect()
{
	int temp_gc_alloc_slab_counter = gc_alloc_slab_counter;
	int page_size = getpagesize();
	int slab_size = page_size * 10;
	int i, j;
	gc_init();                                                         //grab new slab to make sure we dont overwrite
	
	for(i = 0; i < ROOT_SET_LENGTH; i++)
	{
		if((int)root_set[i] > (int)start_pointers[temp_gc_alloc_slab_counter] && (int)root_set[i] < (int)end_pointers[temp_gc_alloc_slab_counter])
			root_set[i] = gc_copy(root_set[i]);
	}
	
	if(munmap(start_pointers[temp_gc_alloc_slab_counter], slab_size))                       //unmaps old slab (nodes in the linked list)
			printf("%s", "munmap error");
}

int size_in_bytes(gc_type_info *info)
{
	return ((info->size_in_bytes + 7) - (info->size_in_bytes + 7) % 8);//makes it 8 byte alligned without metadata, useful for functions like memcopy
}

int have_room(gc_type_info *info)
{
	if(((int)alloc + size_in_bytes(info) + 8) > ((int)end_pointers[gc_alloc_slab_counter]))   //Calls size+8 for meta data. Looks at  and size. checks to see if theres room using alloc and endptr
		return 0;                                                      //return false if no room
	return 1;                                                          //return true if there is room
}

void gc_set_null(void * index)
{
	index = (int)NULL;
}
