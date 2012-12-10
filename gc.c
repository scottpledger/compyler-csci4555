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

int gc_alloc_slab_counter = -1;

int * start_pointers[1000] = {ROOT_SET_NULL};
int * end_pointers[1000] = {ROOT_SET_NULL};
int * alloc;
int root_alloc = 0;





void gc_init()
{
	gc_alloc_slab_counter++;                                                                                
	if(gc_alloc_slab_counter > 999)           //rolls over to 0 "circular array"
		gc_alloc_slab_counter = 0;

	int page_size = getpagesize();
	int slab_size = page_size * 1000;
	
	start_pointers[gc_alloc_slab_counter] = (int *) mmap(NULL, slab_size, 
		  			PROT_READ | PROT_WRITE, 
		 		 	MAP_ANON | MAP_PRIVATE,
		  			0, 0);
	end_pointers[gc_alloc_slab_counter] = (int *)((int)start_pointers[gc_alloc_slab_counter] + slab_size);
	alloc = start_pointers[gc_alloc_slab_counter];
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
	alloc[0] = (int)info;                                              //use interger arithmatic, sets metadata for type
	alloc[1] = (int)NULL;                                              //set meta data for copy pointer
	
	alloc = (int *)((int)alloc + size_in_bytes(info) + 8);             //move allocate to the end of the item you just put in
	
	root_set[root_alloc] = alloc;
	root_alloc++;
	if(!(root_alloc < ROOT_SET_LENGTH))
		printf(stderr, "too many objects");

	return (void *)((int)alloc - size_in_bytes(info));                 //return front of payload
}

int * gc_copy(int * node)                                              //takes in ptr to payload
{
	if(node == NULL)                                                   //if no payload return NULL
		return NULL;
	
	if((int *)(((int *)node)[-1]) != NULL)                             //Check if it has been copied or not
		return (void *)(((int *)node)[-1]);                            //Return address of where payload has been copied to
		
	void * new_node = gc_alloc((void *)(((int*)node)[-2]));            //Create new Block, saves pointer into new node
	
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
	
	int i, j;
	gc_init();     
	int page_size = getpagesize();
	int slab_size = page_size * 1000;                                                    //grab new slab to make sure we dont overwrite
	
	for(i = 0; i < ROOT_SET_LENGTH; i++)                               //if there is something there
	{
		root_set[i] = gc_copy(root_set[i]);                            //rootset = start of new linked list
	}
	
	for(j = 0; j <= temp_gc_alloc_slab_counter; j++)
	{
		if(munmap(start_pointers[j], slab_size))                       //unmaps old slabs (nodes in the linked list)
			printf("%s", "munmap error");

	}
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

void gc_nullify(int * index)
{
	index[0] = (int)NULL;
}

void gc_collet_all()
{
	int page_size = getpagesize();
	int slab_size = page_size * 1000;
	int i;
	for(i = 0; i < 1000; i++)
	{
		munmap(start_pointers[i], slab_size);
	}
}
