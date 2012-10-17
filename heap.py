
def parent(i):
    return i / 2

def left(i):
    return 2 * i

def right(i):
    return 2 * i + 1

def down_heap(A, A_size, index_of, i, compare):
    l = 2 * i
    r = 2 * i + 1
    if l < A_size and compare(A[i], A[l]):
        largest = l
    else:
        largest = i
    if r < A_size and compare(A[largest], A[r]):
        largest = r
    if largest != i:
        a = A[i]
        b = A[largest]
        A[i] = b
        index_of[b] = i
        A[largest] = a
        index_of[a] = largest
        return down_heap(A, A_size, index_of, largest, compare)
    else:
        return i

def build_heap(A, A_size, index_of, compare):
    i = A_size / 2
    while i != 0:
        down_heap(A, A_size, index_of, i, compare)
        i = i - 1

def up_heap(A, index_of, i, compare):
    elt = A[i]
    while i > 0 and compare(A[i / 2], elt):
        p = A[i / 2]
        A[i] = p
        index_of[p] = i
        i = i / 2
    A[i] = elt
    index_of[elt] = i

def heap_update(A, A_size, index_of, i, compare):
    j = down_heap(A, A_size, index_of, i, compare)
    up_heap(A, index_of, j, compare)
