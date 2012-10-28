counter = 0

def generate_name(x):
    global counter
    name = str(counter) + '_' + x
    counter = counter + 1
    return name

def generate_label(x):
    global counter
    name = x + '_' + str(counter)
    counter = counter + 1
    return name

shift = { 'int' : 2, 'bool' : 2, 'big' : 2 }
tag = { 'int' : 0, 'bool' : 1, 'big' : 3 }
mask = 3

builtin_functions = ['input_int', 'input', 'print_any', 'create_dict', 'create_list',
                     'add', 'is_true', 'equal', 'not_equal',
                     'get_fun_ptr', 'get_free_vars',
                     'create_class', 'get_attr', 'set_attr', 'has_attr',
                     'create_object', 'get_class', 'is_class',
                     'get_function', 'get_receiver', 'is_bound_method', 'is_unbound_method']

def unzip(ls):
    ls1 = [x for (x,y) in ls]
    ls2 = [y for (x,y) in ls]
    return (ls1,ls2)
