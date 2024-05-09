"""Implementation of the MyPL Virtual Machine (VM).

NAME: George Calvert
DATE: Spring 2024
CLASS: CPSC 326

"""

from mypl_error import *
from mypl_opcode import *
from mypl_frame import *


class VM:

    def __init__(self):
        """Creates a VM."""
        self.struct_heap = {}        # id -> dict
        self.array_heap = {}         # id -> list
        self.dict_heap = {}          # id -> dict
        self.next_obj_id = 2024      # next available object id (int)
        self.frame_templates = {}    # function name -> VMFrameTemplate
        self.call_stack = []         # function call stack

    
    def __repr__(self):
        """Returns a string representation of frame templates."""
        s = ''
        for name, template in self.frame_templates.items():
            s += f'\nFrame {name}\n'
            for instr in template.instructions:
                s += f'  {id}: {instr}\n'
        return s

    
    def add_frame_template(self, template):
        """Add the new frame info to the VM. 

        Args: 
            frame -- The frame info to add.

        """
        self.frame_templates[template.function_name] = template

    
    def error(self, msg, frame=None):
        """Report a VM error."""
        if not frame:
            raise VMError(msg)
        pc = frame.pc - 1
        instr = frame.template.instructions[pc]
        name = frame.template.function_name
        msg += f' (in {name} at {pc}: {instr})'
        raise VMError(msg)

    
    #----------------------------------------------------------------------
    # RUN FUNCTION
    #----------------------------------------------------------------------
    
    def run(self, debug=False):
        """Run the virtual machine."""
        # grab the "main" function frame and instantiate it
        if not 'main' in self.frame_templates:
            self.error('No "main" functrion')
        frame = VMFrame(self.frame_templates['main'])
        frame.variables = []
        self.call_stack.append(frame)

        # run loop (continue until run out of call frames or instructions)
        while self.call_stack and frame.pc < len(frame.template.instructions):
            # get the next instruction
            instr = frame.template.instructions[frame.pc]
            # increment the program count (pc)
            frame.pc += 1
            # for debugging:
            if debug:
                print('\n')
                print('\t FRAME.........:', frame.template.function_name)
                print('\t PC............:', frame.pc)
                print('\t INSTRUCTION...:', instr)
                val = None if not frame.operand_stack else frame.operand_stack[-1]
                print('\t NEXT OPERAND..:', val)
                cs = self.call_stack
                fun = cs[-1].template.function_name if cs else None
                print('\t NEXT FUNCTION..:', fun)

            #------------------------------------------------------------
            # Literals and Variables
            #------------------------------------------------------------

            if instr.opcode == OpCode.PUSH:
                frame.operand_stack.append(instr.operand)
            elif instr.opcode == OpCode.POP:
                frame.operand_stack.pop()
            elif instr.opcode == OpCode.WRITE:
                x = frame.operand_stack.pop()
                # printing nulls
                if x != None:
                    if type(x) == bool:
                        if x:
                            print("true", end="")
                        else:
                            print("false", end="")
                    else:
                        print(x, end="")
                else:
                    print('null', end="")
            elif instr.opcode == OpCode.DUP:
                x = frame.operand_stack.pop()
                frame.operand_stack.append(x)
                frame.operand_stack.append(x)
            elif instr.opcode == OpCode.STORE:
                x = frame.operand_stack.pop()
                addr = instr.operand
                try:
                    temp = frame.variables[addr]
                    frame.variables[addr] = x
                except:
                    frame.variables.insert(addr, x)
            elif instr.opcode == OpCode.LOAD:
                addr = instr.operand
                try:
                    x = frame.variables[addr]
                    frame.operand_stack.append(x)
                except:
                    self.error("address doesnt exist", frame)
            
            #------------------------------------------------------------
            # Operations
            #------------------------------------------------------------

            elif instr.opcode == OpCode.ADD:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                if x == None or y == None:
                    self.error("Cant add type null", frame)
                frame.operand_stack.append(y + x)
            elif instr.opcode == OpCode.SUB:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                if x == None or y == None:
                    self.error("Cant subtract type null", frame)
                frame.operand_stack.append(y - x) 
            elif instr.opcode == OpCode.MUL:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                if x == None or y == None:
                    self.error("Cant multiply type null", frame)
                frame.operand_stack.append(y * x)  
            elif instr.opcode == OpCode.DIV:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                if x == None or y == None or x == 0:
                    self.error("Cant divide type null", frame)
                if type(x) == int and type(y) == int:
                    frame.operand_stack.append(y // x)  
                elif type(x) == float and type(y) == float:
                     frame.operand_stack.append(y / x)  
                else:
                    self.error("Mismatch Types for division", frame)
            elif instr.opcode == OpCode.AND:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                if type(x) != bool or type(y) != bool:
                    self.error("Cant use non bool type in and operator", frame)
                # s = ((str)(y and x)).lower()
                frame.operand_stack.append(y and x)   
            elif instr.opcode == OpCode.OR:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                if type(x) != bool or type(y) != bool:
                    self.error("Cant use non bool type in and operator", frame)
                # s = ((str)(y or x)).lower()
                frame.operand_stack.append(y or x) 
            elif instr.opcode == OpCode.NOT:
                x = frame.operand_stack.pop()
                if type(x) != bool:
                    self.error("Cant use NOT operator on non boolean type", frame)
                # s = ((str)(not x)).lower() 
                frame.operand_stack.append(not x)  
            elif instr.opcode == OpCode.CMPLT:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                if type(x) != type(y) or type(x) == None or type(y) == None:
                    self.error("Mismatch of types for < op", frame)
                # s = ((str)(y < x)).lower()
                frame.operand_stack.append(y < x)
            elif instr.opcode == OpCode.CMPLE:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                if type(x) != type(y) or type(x) == None or type(y) == None:
                    self.error("Mismatch of types for <= op", frame)
                # s = ((str)(y <= x)).lower()
                frame.operand_stack.append(y <= x) 
            elif instr.opcode == OpCode.CMPEQ:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                # s = ((str)(y == x)).lower()
                frame.operand_stack.append(y == x)     
            elif instr.opcode == OpCode.CMPNE:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                # s = ((str)(y != x)).lower()
                frame.operand_stack.append(y != x)      

            #------------------------------------------------------------
            # Branching
            #------------------------------------------------------------

            elif instr.opcode == OpCode.JMP:
                a = instr.operand
                frame.pc = a
            elif instr.opcode == OpCode.JMPF:
                a = instr.operand
                x = frame.operand_stack.pop()
                if not x:
                    frame.pc = a

            
                    
            #------------------------------------------------------------
            # Functions
            # ------------------------------------------------------------

            elif instr.opcode == OpCode.RET:
                # not main so do something
                ret = frame.operand_stack.pop()
                self.call_stack.pop()
                
                if len(self.call_stack) != 0:
                    frame = self.call_stack[-1]
                    frame.operand_stack.append(ret)


            elif instr.opcode == OpCode.CALL:
                func_name = instr.operand
                old_frame = frame
                new_frame = VMFrame(self.frame_templates[func_name])

                self.call_stack.append(new_frame)

                for x in range(new_frame.template.arg_count):
                    a = frame.operand_stack.pop()
                    new_frame.operand_stack.append(a)
                
                frame = new_frame




            
            #------------------------------------------------------------
            # Built-In Functions
            #------------------------------------------------------------

            elif instr.opcode == OpCode.READ:
                x = input()
                frame.operand_stack.append(x)

            elif instr.opcode == OpCode.LEN:
                x = frame.operand_stack.pop()
                if type(x) == str:
                    x = len(x)
                elif type(x) == type(None):
                    self.error("cannot use length null type", frame)
                # array length
                elif type(x) == int:
                    try:
                        length = len(self.array_heap[x])
                        x = length
                    except:
                        # dict
                        try:
                            length = len(self.dict_heap[x])
                            x = length
                        except:
                            self.error("Cant get length of type")
                else:
                    self.error("Cant get length of type other than array or string")
                frame.operand_stack.append(x)

            elif instr.opcode == OpCode.GETC:
                x = frame.operand_stack.pop()
                if type(x) == str:
                    y = frame.operand_stack.pop()
                    if y == None or y < 0 or y >= len(x):
                        self.error("invalid index", frame)
                    frame.operand_stack.append(x[y])
                else:
                    self.error("Cant index non string type", frame)
            elif instr.opcode == OpCode.TOINT:
                x = frame.operand_stack.pop()
                if type(x) == float or type(x) == str:
                    try:
                        x = int(x)
                        frame.operand_stack.append(x)
                    except:
                        self.error("Cant cast type to int", frame)
                else:
                    self.error("Cant cast type to int", frame)
            elif instr.opcode == OpCode.KEYS:
                oid = frame.operand_stack.pop()
                dictionary = None
                try:
                    dictionary = self.dict_heap[oid]
                except:
                    self.error("dictionary doesnt exist", frame)
                keys_list = list(dictionary.keys())
                
                # add keys_list to array_heap then put oid onto stack
                self.array_heap[self.next_obj_id] = keys_list

                frame.operand_stack.append(self.next_obj_id)
                self.next_obj_id += 1

            elif instr.opcode == OpCode.TODBL:
                x = frame.operand_stack.pop()
                if type(x) == int or type(x) == str:
                    try:
                        x = float(x)
                        frame.operand_stack.append(x)
                    except:
                        self.error("Cant cast type to double", frame)  
                else:
                    self.error("Cant cast type to double", frame)     
            elif instr.opcode == OpCode.TOSTR:
                x = frame.operand_stack.pop()
                if type(x) == int or type(x) == float or type(x) == str:
                    x = str(x)
                    frame.operand_stack.append(x)
                else:
                    self.error("Cant cast type to str", frame)      
        
            #------------------------------------------------------------
            # Heap
            #------------------------------------------------------------

            # structs
            elif instr.opcode == OpCode.ALLOCS:
                id = self.next_obj_id
                self.next_obj_id += 1
                self.struct_heap[id] = {}
                frame.operand_stack.append(id)

            elif instr.opcode == OpCode.SETF:
                x = frame.operand_stack.pop()
                id = frame.operand_stack.pop()
                try:
                    self.struct_heap[id][instr.operand] = x
                except:
                    self.error("index error in SETF", frame)

            elif instr.opcode == OpCode.GETF:
                id = frame.operand_stack.pop()
                try:
                    frame.operand_stack.append(self.struct_heap[id][instr.operand])
                except:
                    self.error("index error in GETF", frame)

            # arrays
            elif instr.opcode == OpCode.ALLOCA:
                x = frame.operand_stack.pop()
                if x == None or x < 0:
                    self.error("invalid array size", frame)
                l = []
                for num in range(x):
                    l.append(None)
                self.array_heap[self.next_obj_id] = l
                frame.operand_stack.append(self.next_obj_id)
                self.next_obj_id += 1

            elif instr.opcode == OpCode.SETI:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                oid = frame.operand_stack.pop()

                if y == None:
                    self.error("Invalid index for array")
                
                keys_list = list(self.array_heap.keys())
        
                if oid not in keys_list:
                    self.error("Object id doesnt exist for array")
                
                l = self.array_heap[oid]

                if y >= len(l) or y < 0:
                    self.error("Invalid Index for array")
                
                self.array_heap[oid][y] = x

            elif instr.opcode == OpCode.GETI:
                x = frame.operand_stack.pop()
                if x == None or x < 0:
                    self.error("invalid index given", frame) 
                y = frame.operand_stack.pop()
                try:
                    frame.operand_stack.append(self.array_heap[y][x])
                except:
                    self.error("index error in GETI", frame)
            # Dictionaries
            elif instr.opcode == OpCode.ALLOCD:
                id = self.next_obj_id
                self.next_obj_id += 1
                self.dict_heap[id] = {}
                frame.operand_stack.append(id)

            elif instr.opcode == OpCode.SETD:
                x = frame.operand_stack.pop()
                key = frame.operand_stack.pop()
                oid = frame.operand_stack.pop()
                
                dictionary = None
                # get object
                try:
                    dictionary = self.dict_heap[oid]
                except:
                    self.error("dictionary object not declared", frame)
                
                dictionary[key] = x
            elif instr.opcode == OpCode.IN:
                x = frame.operand_stack.pop()
                oid = frame.operand_stack.pop()

                dictionary = None

                try:
                    dictionary = self.dict_heap[oid]
                except:
                    self.error("dictionary object not declared", frame)
                
                keys = list(dictionary.keys())

                if x in keys:
                    frame.operand_stack.append(True)
                else:
                    frame.operand_stack.append(False)

            elif instr.opcode == OpCode.GETD:
                key = frame.operand_stack.pop()
                oid = frame.operand_stack.pop()

                dictionary = None

                try:
                    dictionary = self.dict_heap[oid]
                except:
                    self.error("dictionary object not declared", frame)
                
                try:
                    value = dictionary[key]
                    frame.operand_stack.append(value)
                except:
                    self.error(f"key {key} doesnt exist in dict", frame)



            
            #------------------------------------------------------------
            # Special 
            #------------------------------------------------------------

            elif instr.opcode == OpCode.DUP:
                x = frame.operand_stack.pop()
                frame.operand_stack.append(x)
                frame.operand_stack.append(x)

            elif instr.opcode == OpCode.NOP:
                # do nothing
                pass

            else:
                self.error(f'unsupported operation {instr}')
