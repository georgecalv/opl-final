"""IR code generator for converting MyPL to VM Instructions. 

NAME: <your name here>
DATE: Spring 2024
CLASS: CPSC 326

"""

from mypl_token import *
from mypl_ast import *
from mypl_var_table import *
from mypl_frame import *
from mypl_opcode import *
from mypl_vm import *


class CodeGenerator (Visitor):

    def __init__(self, vm):
        """Creates a new Code Generator given a VM. 
        
        Args:
            vm -- The target vm.
        """
        # the vm to add frames to
        self.vm = vm
        # the current frame template being generated
        self.curr_template = None
        # for var -> index mappings wrt to environments
        self.var_table = VarTable()
        # struct name -> StructDef for struct field info
        self.struct_defs = {}
        # dict_defs = list of dictionary definitions
        self.dict_defs = []

    
    def add_instr(self, instr):
        """Helper function to add an instruction to the current template."""
        self.curr_template.instructions.append(instr)

        
    def visit_program(self, program):
        for struct_def in program.struct_defs:
            struct_def.accept(self)
        for fun_def in program.fun_defs:
            fun_def.accept(self)

    
    def visit_struct_def(self, struct_def):
        # remember the struct def for later
        self.struct_defs[struct_def.struct_name.lexeme] = struct_def
        # find dict_defs
        for val in struct_def.fields:
            if val.data_type.is_dict:
                self.dict_defs.append(val.var_name.lexeme)

        
    def visit_fun_def(self, fun_def):
        # create a new frame
        func_template = VMFrameTemplate(fun_def.fun_name.lexeme, len(fun_def.params), [])
        # set new frame to cur template
        self.curr_template = func_template
        # push new variable env
        self.var_table.push_environment()
        # add each param to variable env and add store instruction
        for param in range(func_template.arg_count):
            self.var_table.add(fun_def.params[param].var_name.lexeme)
            # add store func
            self.curr_template.instructions.append(STORE(param))

        # visit each statement
        for stmt in fun_def.stmts:
            stmt.accept(self)

        # add return if last instruction is not a return
        if len(self.curr_template.instructions) == 0 or type(fun_def.stmts[len(fun_def.stmts) - 1]) != ReturnStmt: 
            self.curr_template.instructions.append(PUSH(None))
            self.curr_template.instructions.append(RET())
            
        # pop environment
        self.var_table.pop_environment()
        # add frame to vm
        self.vm.add_frame_template(func_template)

    
    def visit_return_stmt(self, return_stmt):
        return_stmt.expr.accept(self)
        self.curr_template.instructions.append(RET())

        
    def visit_var_decl(self, var_decl):
        if var_decl.expr:
            var_decl.expr.accept(self)
            self.curr_template.instructions.append(STORE(self.var_table.total_vars))
        else:
            self.curr_template.instructions.append(PUSH(None))
            self.curr_template.instructions.append(STORE(self.var_table.total_vars))
        # cehck for dictionary
        if var_decl.var_def.data_type.is_dict:
            self.dict_defs.append(var_decl.var_def.var_name.lexeme)
        self.var_table.add(var_decl.var_def.var_name.lexeme)
                
                
    
    def visit_assign_stmt(self, assign_stmt):
        var = assign_stmt.lvalue[0]
        index = self.var_table.get(var.var_name.lexeme)
        self.curr_template.instructions.append(LOAD(index))

        # chck if path has more than lvalue statement
        if len(assign_stmt.lvalue) > 1:
            if var.array_expr:
                var.array_expr.accept(self)
                self.curr_template.instructions.append(GETI())
            # go through lvals
            for x in range(1, len(assign_stmt.lvalue)):
                field = assign_stmt.lvalue[x]
                # not last 
                if x != len(assign_stmt.lvalue) - 1:
                    if field.array_expr:
                        self.curr_template.instructions.append(GETF(field.var_name.lexeme))
                        field.array_expr.accept(self)
                        # check for dict
                        if field.var_name.lexeme in self.dict_defs:
                            self.curr_template.instructions.append(GETD())
                        else:
                            self.curr_template.instructions.append(GETI())
                    else:
                        self.curr_template.instructions.append(GETF(field.var_name.lexeme))
                # last
                else:
                    if field.array_expr:
                        self.curr_template.instructions.append(GETF(field.var_name.lexeme))
                        field.array_expr.accept(self)
                        assign_stmt.expr.accept(self)
                        # check for dictionary
                        if field.var_name.lexeme in self.dict_defs:
                            self.curr_template.instructions.append(SETD())
                        else:
                            self.curr_template.instructions.append(SETI())
                    else:
                        assign_stmt.expr.accept(self)
                        self.curr_template.instructions.append(SETF(field.var_name.lexeme))
                
        else:
            var_name = assign_stmt.lvalue[0].var_name.lexeme
            is_array = False
            is_dict = False
            if assign_stmt.lvalue[0].array_expr:
                if var_name in self.dict_defs:
                    is_dict = True
                else:
                    is_array = True
                assign_stmt.lvalue[0].array_expr.accept(self)
            # accept r value
            assign_stmt.expr.accept(self)
            if is_array:
                self.curr_template.instructions.append(SETI())
            elif is_dict:
                self.curr_template.instructions.append(SETD())
            else:
                index_var = self.var_table.get(var_name)
                self.curr_template.instructions.append(STORE(index_var))
    
    def visit_while_stmt(self, while_stmt):
        # grab starting index
        # call accpet on condition
        start = len(self.curr_template.instructions)
        while_stmt.condition.accept(self)
        jmp_loc = len(self.curr_template.instructions)

        # create and add jump false with -1
        self.curr_template.instructions.append(JMPF(-1))
        # push var table env
        self.var_table.push_environment()

        # accept statements
        for stmt in while_stmt.stmts:
            stmt.accept(self)

        # pop var_env
        self.var_table.pop_environment()
        # create and add jump instr using index from start
        self.curr_template.instructions.append(JMP(start))
        # create and add NOP
        self.curr_template.instructions.append(NOP())
        # update jmpf operand with NOP location 
        self.curr_template.instructions[jmp_loc].operand = len(self.curr_template.instructions)

        
    def visit_for_stmt(self, for_stmt):
        # push environment for var decl
        self.var_table.push_environment()
        # vardecl generate
        for_stmt.var_decl.accept(self)
        # condition
        start = len(self.curr_template.instructions)
        for_stmt.condition.accept(self)
        jmp_loc = len(self.curr_template.instructions)

        # create and add jump false with -1
        self.curr_template.instructions.append(JMPF(-1))
        # push var table env
        self.var_table.push_environment()

        # accept statements
        for stmt in for_stmt.stmts:
            stmt.accept(self)
        
        # update i
        self.var_table.pop_environment()
        for_stmt.assign_stmt.accept(self)
        self.curr_template.instructions.append(JMP(start))
        self.var_table.pop_environment()
        # add jmp nop and update JMPF
        self.curr_template.instructions.append(NOP())
        self.curr_template.instructions[jmp_loc].operand = len(self.curr_template.instructions) - 1

    
    def visit_if_stmt(self, if_stmt):
        # basic_if
        basic_if = if_stmt.if_part
        basic_if.condition.accept(self)

        # add jumpf
        first_jmpf_loc = len(self.curr_template.instructions)
        self.curr_template.instructions.append(JMPF(-1))

        # push env and accept statments
        self.var_table.push_environment()
        for stmt in basic_if.stmts:
            stmt.accept(self)
        self.var_table.pop_environment()

        # save jmp location to end of else or elseifs
        first_jmp_loc = len(self.curr_template.instructions)
        self.curr_template.instructions.append(JMP(-1))

        # check for else ifs
        if len(if_stmt.else_ifs) >= 1:
            # update jmpf
            self.curr_template.instructions[first_jmpf_loc].operand = len(self.curr_template.instructions)
            end_jump_locs = []
            for else_if in if_stmt.else_ifs:
                # add NOP
                self.curr_template.instructions.append(NOP())
                # accept condition
                else_if.condition.accept(self)
                # jmpf
                jmpf_loc = len(self.curr_template.instructions)
                self.curr_template.instructions.append(JMPF(-1))
                # statements
                self.var_table.push_environment()
                for stmt in else_if.stmts:
                    stmt.accept(self)
                self.var_table.pop_environment()
                # jump to end
                end_jump_locs.append(len(self.curr_template.instructions))
                self.curr_template.instructions.append(JMP(-1))
                # update jmpf
                self.curr_template.instructions[jmpf_loc].operand = len(self.curr_template.instructions)

            # go through else stmts if there
            self.var_table.push_environment()
            for stmt in if_stmt.else_stmts:
                stmt.accept(self)
            self.var_table.pop_environment()
            # update end_jump_locs
            for loc in end_jump_locs:
                self.curr_template.instructions[loc].operand = len(self.curr_template.instructions)
            self.curr_template.instructions.append(NOP())

            # update if jump
            self.curr_template.instructions[first_jmp_loc].operand = len(self.curr_template.instructions)
            self.curr_template.instructions.append(NOP())

        # no else ifs
        else:
            # update jmpf loc to else statements if there are any
            self.curr_template.instructions[first_jmpf_loc].operand = len(self.curr_template.instructions)
            self.curr_template.instructions.append(NOP())

            # accept else statements
            self.var_table.push_environment()
            for stmt in if_stmt.else_stmts:
                stmt.accept(self)
            self.var_table.pop_environment()

            self.curr_template.instructions.append(NOP())
            # update location for end of if to jmp to 
            self.curr_template.instructions[first_jmp_loc].operand = len(self.curr_template.instructions) - 1 

            
    
    def visit_call_expr(self, call_expr):
        # go through arguments and accept them
        for arg in call_expr.args:
            arg.accept(self)
        
        # check what function
        name = call_expr.fun_name.lexeme
        if name == 'print':
            self.curr_template.instructions.append(WRITE())
        elif name == 'input':
            self.curr_template.instructions.append(READ())
        elif name == 'length':
            self.curr_template.instructions.append(LEN())
        elif name == 'dtoi' or name == 'stoi':
            self.curr_template.instructions.append(TOINT())
        elif name == 'itod' or name == 'stod':
            self.curr_template.instructions.append(TODBL())
        elif name == 'itos' or name == 'dtos':
            self.curr_template.instructions.append(TOSTR())
        elif name == 'get':
            self.curr_template.instructions.append(GETC())
        elif name == 'keys':
            self.curr_template.instructions.append(KEYS())
        elif name == 'in':
            self.curr_template.instructions.append(IN())
        else:
            self.curr_template.instructions.append(CALL(name))

        
    def visit_expr(self, expr):
        # check for operation
        if expr.op:
            # check for greater than comparison
            if expr.op.token_type == TokenType.GREATER or expr.op.token_type == TokenType.GREATER_EQ:
                expr.rest.accept(self)
                expr.first.accept(self)
            else:
                expr.first.accept(self)
                expr.rest.accept(self)
            # determine operation
            if expr.op.token_type == TokenType.PLUS:
                self.curr_template.instructions.append(ADD())
            elif expr.op.token_type == TokenType.MINUS:
                self.curr_template.instructions.append(SUB())
            elif expr.op.token_type == TokenType.TIMES:
                self.curr_template.instructions.append(MUL())
            elif expr.op.token_type == TokenType.DIVIDE:
                self.curr_template.instructions.append(DIV())
            # boolean ops
            elif expr.op.token_type == TokenType.AND:
                self.curr_template.instructions.append(AND())
            elif expr.op.token_type == TokenType.OR:
                self.curr_template.instructions.append(OR())
            elif expr.op.token_type == TokenType.LESS:
                self.curr_template.instructions.append(CMPLT())
            elif expr.op.token_type == TokenType.LESS_EQ:
                self.curr_template.instructions.append(CMPLE())
            elif expr.op.token_type == TokenType.LESS_EQ:
                self.curr_template.instructions.append(CMPLE())
            elif expr.op.token_type == TokenType.GREATER_EQ:
                self.curr_template.instructions.append(CMPLE())
            elif expr.op.token_type == TokenType.GREATER:
                self.curr_template.instructions.append(CMPLT()) 
            elif expr.op.token_type == TokenType.EQUAL:
                self.curr_template.instructions.append(CMPEQ())
            elif expr.op.token_type == TokenType.NOT_EQUAL:
                self.curr_template.instructions.append(CMPNE())           
        # no operation
        else:
            expr.first.accept(self)
        # check for not
        if expr.not_op:
            self.curr_template.instructions.append(NOT())
            

            
    def visit_data_type(self, data_type):
        # nothing to do here
        pass

    
    def visit_var_def(self, var_def):
        # nothing to do here
        pass

    
    def visit_simple_term(self, simple_term):
        simple_term.rvalue.accept(self)

        
    def visit_complex_term(self, complex_term):
        complex_term.expr.accept(self)

        
    def visit_simple_rvalue(self, simple_rvalue):
        val = simple_rvalue.value.lexeme
        if simple_rvalue.value.token_type == TokenType.INT_VAL:
            self.add_instr(PUSH(int(val)))
        elif simple_rvalue.value.token_type == TokenType.DOUBLE_VAL:
            self.add_instr(PUSH(float(val)))
        elif simple_rvalue.value.token_type == TokenType.STRING_VAL:
            val = val.replace('\\n', '\n')
            val = val.replace('\\t', '\t')
            self.add_instr(PUSH(val))
        elif val == 'true':
            self.add_instr(PUSH(True))
        elif val == 'false':
            self.add_instr(PUSH(False))
        elif val == 'null':
            self.add_instr(PUSH(None))

    
    def visit_new_rvalue(self, new_rvalue):
        # check if struct declaration
        if new_rvalue.type_name.lexeme in self.struct_defs and not(new_rvalue.array_expr):
            # struct_def
            self.curr_template.instructions.append(ALLOCS())
            struct_fields = self.struct_defs[new_rvalue.type_name.lexeme].fields
            # params given
            struct_params = new_rvalue.struct_params
            for p in range(len(struct_params)):
                self.curr_template.instructions.append(DUP())
                struct_params[p].accept(self)
                self.curr_template.instructions.append(SETF(struct_fields[p].var_name.lexeme))
        # array or dict
        else:
            # array
            if new_rvalue.array_expr:
                self.curr_template.instructions.append(PUSH(int(new_rvalue.array_expr.first.rvalue.value.lexeme)))
                self.curr_template.instructions.append(ALLOCA())
            # dict
            else:
                self.curr_template.instructions.append(ALLOCD())

            
    
    def visit_var_rvalue(self, var_rvalue):
        # check for path expr
        if len(var_rvalue.path) > 1:
            path = var_rvalue.path
            # get mem location
            struct_mem_loc = self.var_table.get(path[0].var_name.lexeme)
            
            self.curr_template.instructions.append(LOAD(struct_mem_loc))
            # check array_expr for first
            if path[0].array_expr:
                path[0].array_expr.accept(self)
                self.curr_template.instructions.append(GETI())
            
            # # go through rest of path
            for x in range(1, len(path)):
                field = path[x]
                # not last 
                if x != len(path) - 1:
                    if field.array_expr:
                        self.curr_template.instructions.append(GETF(field.var_name.lexeme))
                        field.array_expr.accept(self)
                        if field.var_name.lexeme in self.dict_defs:
                            self.curr_template.instructions.append(GETD())
                        else:
                            self.curr_template.instructions.append(GETI())
                    else:
                        self.curr_template.instructions.append(GETF(field.var_name.lexeme))
                # last
                else:
                    if field.array_expr:
                        self.curr_template.instructions.append(GETF(field.var_name.lexeme))
                        field.array_expr.accept(self)
                        field.expr.accept(self)
                        if field.var_name.lexeme in self.dict_defs:
                            self.curr_template.instructions.append(GETD())
                        else:
                            self.curr_template.instructions.append(GETI())                            
                    else:
                        self.curr_template.instructions.append(GETF(field.var_name.lexeme))
        else:
            name = var_rvalue.path[0].var_name.lexeme
            index = self.var_table.get(name)
            self.curr_template.instructions.append(LOAD(index))
            # check for array expr so getI
            if var_rvalue.path[0].array_expr:
                # push index onto stack
                var_rvalue.path[0].array_expr.accept(self)
                if name in self.dict_defs:
                    self.curr_template.instructions.append(GETD())  
                else:
                    self.curr_template.instructions.append(GETI())

                
