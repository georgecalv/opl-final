"""Semantic Checker Visitor for semantically analyzing a MyPL program.

NAME: George Calvert
DATE: Spring 2024
CLASS: CPSC 326

"""

from dataclasses import dataclass
from mypl_error import *
from mypl_token import Token, TokenType
from mypl_ast import *
from mypl_symbol_table import SymbolTable


BASE_TYPES = ['int', 'double', 'bool', 'string', 'dict']
BUILT_INS = ['print', 'input', 'itos', 'itod', 'dtos', 'dtoi', 'stoi', 'stod',
             'length', 'get', 'keys', 'in']

class SemanticChecker(Visitor):
    """Visitor implementation to semantically check MyPL programs."""

    def __init__(self):
        self.structs = {}
        self.functions = {}
        self.symbol_table = SymbolTable()
        self.curr_type = None


    # Helper Functions

    def error(self, msg, token):
        """Create and raise a Static Error."""
        if token is None:
            raise StaticError(msg)
        else:
            m = f'{msg} near line {token.line}, column {token.column}'
            raise StaticError(m)


    def get_field_type(self, struct_def, field_name):
        """Returns the DataType for the given field name of the struct
        definition.

        Args:
            struct_def: The StructDef object 
            field_name: The name of the field

        Returns: The corresponding DataType or None if the field name
        is not in the struct_def.

        """
        for var_def in struct_def.fields:
            if var_def.var_name.lexeme == field_name:
                return var_def.data_type
        return None

        
    # Visitor Functions
    
    def visit_program(self, program):
        # check and record struct defs
        for struct in program.struct_defs:
            struct_name = struct.struct_name.lexeme
            if struct_name in self.structs:
                self.error(f'duplicate {struct_name} definition', struct.struct_name)
            self.structs[struct_name] = struct
        # check and record function defs
        for fun in program.fun_defs:
            fun_name = fun.fun_name.lexeme
            if fun_name in self.functions: 
                self.error(f'duplicate {fun_name} definition', fun.fun_name)
            if fun_name in BUILT_INS:
                self.error(f'redefining built-in function', fun.fun_name)
            if fun_name == 'main' and fun.return_type.type_name.lexeme != 'void':
                self.error('main without void type', fun.return_type.type_name)
            if fun_name == 'main' and fun.params: 
                self.error('main function with parameters', fun.fun_name)
            self.functions[fun_name] = fun
        # check main function
        if 'main' not in self.functions:
            self.error('missing main function', None)
        # check each struct
        for struct in self.structs.values():
            struct.accept(self)
        # check each function
        for fun in self.functions.values():
            fun.accept(self)
        
        
    def visit_struct_def(self, struct_def):
        self.symbol_table.push_environment()
        # go through statements
        for stmt in struct_def.fields:
            stmt.accept(self)
        self.symbol_table.pop_environment()


    def visit_fun_def(self, fun_def):
        # check return type
        self.symbol_table.push_environment()
        # check for struct
        if fun_def.return_type.type_name.lexeme not in BASE_TYPES and fun_def.return_type.type_name.lexeme != 'void':
            if fun_def.return_type.type_name.lexeme not in self.structs:
                self.error(f'Invalid return type {fun_def.return_type.type_name.lexeme}', fun_def.return_type.type_name)
        
        # self.symbol_table.add('return', fun_def.return_type.type_name.lexeme)
        self.symbol_table.add('return', fun_def.return_type.type_name)

        # check params
        for param in fun_def.params:
            name = param.var_name.lexeme
            if self.symbol_table.exists_in_curr_env(name):
                self.error(f'duplicate param name used in {fun_def.fun_name.lexeme}', param.var_name)
            else:
                self.symbol_table.add(name, param.data_type)

        # check statements
        for stmt in fun_def.stmts:
            stmt.accept(self)

        # done with environment
        self.symbol_table.pop_environment()
    


        
    def visit_return_stmt(self, return_stmt):
        # accept expr and check what type it is to return type in cur env
        return_type = self.symbol_table.get('return')
        return_stmt.expr.accept(self)
        expr_type = self.curr_type
        # check types
        if return_type.token_type != expr_type.type_name.token_type:
            if expr_type.type_name.token_type != TokenType.VOID_TYPE:
                self.error(f'Return type mismatch. Received {expr_type.type_name.lexeme}, expecting {return_type.lexeme}', expr_type.type_name)

        
            
    def visit_var_decl(self, var_decl):
        lhs_type = var_decl.var_def.data_type
        name = var_decl.var_def.var_name.lexeme
        array_bool = var_decl.var_def.data_type.is_array
        is_dict = var_decl.var_def.data_type.is_dict
        # expression is present
        if var_decl.expr:
            var_decl.expr.accept(self)
            rhs_type = self.curr_type
            if lhs_type.type_name.token_type == rhs_type.type_name.token_type or rhs_type.type_name.lexeme == 'void':
                # check if already in environment
                if self.symbol_table.exists_in_curr_env(name):
                    type_name = self.symbol_table.get(name)
                    # check shadowing redeclaration
                    if type_name.type_name.token_type != lhs_type.type_name.token_type:
                        self.error(f'Duplicate variable declarations for {lhs_type.type_name.lexeme} {name}', var_decl.var_def.data_type.type_name)
                    else:
                        self.symbol_table.add(name, type_name)
                # add since not in env
                else:
                    if not is_dict and array_bool != self.curr_type.is_array and rhs_type.type_name.lexeme != 'void':
                        self.error("Mismatch of array declaration", self.curr_type.type_name)
                    # elif is_dict != self.curr_type.is_dict and rhs_type.type_name.lexeme != 'void':
                    #     self.error("Mismatch of dict declaration", self.curr_type.type_name)
                    self.symbol_table.add(name, lhs_type)
            else:
                self.error(f'Mismatch of types {lhs_type.type_name.lexeme} and {self.curr_type.type_name.lexeme}', var_decl.var_def.data_type.type_name)
        # no expression
        else:
            # check if already in environment
            if self.symbol_table.exists_in_curr_env(name):
                self.error(f'Duplicate variable declarations for {lhs_type} {name}', var_decl.var_def.var_name)
            # add since not in env
            else:
                self.symbol_table.add(name, lhs_type)          
        
    def visit_assign_stmt(self, assign_stmt):
        # lvalue
        lhs_type = None
        first = assign_stmt.lvalue[0]
        if not self.symbol_table.exists(first.var_name.lexeme):
            self.error(f'Use before def {first.var_name.lexeme}', first.var_name)
        first_type = self.symbol_table.get(assign_stmt.lvalue[0].var_name.lexeme)

        # change first type to element type to check
        if first_type.is_dict:
            # check indexing
            temp_type = DataType(False, False, None, None, first_type.key_type_name)
            if assign_stmt.lvalue[0].array_expr:
                assign_stmt.lvalue[0].array_expr.accept(self)
                if temp_type.type_name.token_type != self.curr_type.type_name.token_type:
                    self.error("Invalid type for indexing dictionary", self.curr_type.type_name)
                first_type = DataType(False, False, None, None, first_type.element_type_name)
        lvals_list = assign_stmt.lvalue
        for lval in range(1, len(lvals_list)):
            array_flag = False
            # array_expr
            if lvals_list[lval].array_expr:
                array_flag = True
                lvals_list[lval].array_expr.accept(self)
                if self.curr_type.type_name.token_type != TokenType.INT_TYPE:
                    self.error('Invalid type for indexing array', self.curr_type.type_name)
                # check dict type
            # check if it is in struct declaration
            if first_type.type_name.lexeme in self.structs:
                struct = self.structs[first_type.type_name.lexeme]
                # check var is a field
                # get type of field
                try:
                    first_type = self.get_field_type(struct, lvals_list[lval].var_name.lexeme)
                except:
                    self.error(f'field {lvals_list[lval].var_name.lexeme} not in struct type {struct.struct_name.lexeme}', lvals_list[lval].var_name)
                # array declaration
                if first_type.is_array and not lvals_list[lval].array_expr and type(assign_stmt.expr.first.rvalue) != NewRValue:
                    self.error(f'No array expression given for array type {lvals_list[lval].var_name.lexeme}', lvals_list[lval].var_name)
        lhs_type = first_type
        # expr
        assign_stmt.expr.accept(self)
        if lhs_type.type_name.token_type != self.curr_type.type_name.token_type and self.curr_type.type_name.token_type != TokenType.VOID_TYPE:
            self.error(f'Mismatch of types {lhs_type.type_name.lexeme} and {self.curr_type.type_name.lexeme}', self.curr_type.type_name)
        
            
    def visit_while_stmt(self, while_stmt):
        self.symbol_table.push_environment()
        while_stmt.condition.accept(self)
        if self.curr_type.type_name.token_type != TokenType.BOOL_TYPE or self.curr_type.is_array:
            self.error("Non boolean expression in condition of While Statement", self.curr_type.type_name)
        for stmt in while_stmt.stmts:
            stmt.accept(self)
        self.symbol_table.pop_environment()

    def visit_for_stmt(self, for_stmt):
        self.symbol_table.push_environment()
        # var_decl
        for_stmt.var_decl.accept(self)
        # condition
        for_stmt.condition.accept(self)
        if self.curr_type.type_name.token_type != TokenType.BOOL_TYPE or self.curr_type.is_array:
            self.error('Bad Boolean expression in for loop', self.curr_type.type_name)

        # stmts
        for stmt in for_stmt.stmts:
            stmt.accept(self)
        self.symbol_table.pop_environment()

    def visit_if_stmt(self, if_stmt):
        self.symbol_table.push_environment()
        # basic ifs
        # condition
        if_stmt.if_part.condition.accept(self)
        if self.curr_type.type_name.token_type != TokenType.BOOL_TYPE or self.curr_type.is_array:
            self.error("Non boolean expression in condition of If Statement", self.curr_type.type_name)
        # statements
        for stmt in if_stmt.if_part.stmts:
            stmt.accept(self)
        self.symbol_table.pop_environment()

        # else ifs
        if if_stmt.else_ifs:
            for else_ifs in if_stmt.else_ifs:
                self.symbol_table.push_environment()
                # basic ifs
                # condition
                else_ifs.condition.accept(self)
                if self.curr_type.type_name.token_type != TokenType.BOOL_TYPE or self.curr_type.is_array:
                    self.error("Non boolean expression in condition of if Statement", self.curr_type.type_name)
                # statements
                for stmt in else_ifs.stmts:
                    stmt.accept(self)
                self.symbol_table.pop_environment()
        # else
        if if_stmt.else_stmts:
            self.symbol_table.push_environment()
            for stmt in if_stmt.else_stmts:
                stmt.accept(self)
            self.symbol_table.pop_environment()
        
        
    def visit_call_expr(self, call_expr):
        # check function exists
        fun_list = list(self.functions.keys())
        if call_expr.fun_name.lexeme not in fun_list and call_expr.fun_name.lexeme not in BUILT_INS:
            self.error(f'Undeclared Function {call_expr.fun_name.lexeme}', call_expr.fun_name)
        func_name = call_expr.fun_name.lexeme
        line = call_expr.fun_name.line
        column = call_expr.fun_name.column
        type_token = None
        is_array = False
        # check for built in functions
        if call_expr.fun_name.lexeme in BUILT_INS:
            # print
            if func_name == 'print':
                # set cur to void since print returns a void 
                # one argument but can be no arguments
                if len(call_expr.args) > 1:
                    self.error('Too many arguments for built in function, print', call_expr.fun_name)
                call_expr.args[0].accept(self)
                arg_type = self.curr_type
                accepted_tokens = [TokenType.STRING_TYPE, TokenType.BOOL_TYPE, TokenType.DOUBLE_TYPE, TokenType.INT_TYPE, TokenType.VOID_TYPE]
                if arg_type.type_name.token_type not in accepted_tokens or arg_type.is_array == True:
                    self.error(f'Arguments of type {arg_type.type_name.lexeme} not allowed for function, print', arg_type.type_name)
                type_token = Token(TokenType.VOID_TYPE, 'void', line, column)
            # input
            elif func_name == 'input':
                # check if params is not zero
                if len(call_expr.args) != 0:
                    self.error(f'Too many arguments for bult in function, input', call_expr.fun_name)
                type_token = Token(TokenType.STRING_TYPE, 'string', line, column)
            # itos
            elif func_name == 'itos':
                if len(call_expr.args) != 1:
                    self.error('Too many arguments for built in function, itos', call_expr.fun_name)
                call_expr.args[0].accept(self)
                arg_type = self.curr_type
                if arg_type.type_name.token_type != TokenType.INT_TYPE:
                    self.error(f'Expecting type int, received type {arg_type.type_name.lexeme}', call_expr.fun_name)
                type_token = Token(TokenType.STRING_TYPE, 'string', line, column)
            # dtos
            elif func_name == 'dtos':
                if len(call_expr.args) != 1:
                    self.error('Too many arguments for built in function, dtos', call_expr.fun_name)
                call_expr.args[0].accept(self)
                arg_type = self.curr_type
                if arg_type.type_name.token_type != TokenType.DOUBLE_TYPE:
                    self.error(f'Expecting type double, received type {arg_type.type_name.lexeme}', call_expr.fun_name)
                type_token = Token(TokenType.STRING_TYPE, 'string', line, column)
            # stoi
            elif func_name == 'stoi':
                if len(call_expr.args) != 1:
                    self.error('Too many arguments for built in function, stoi', call_expr.fun_name)
                call_expr.args[0].accept(self)
                arg_type = self.curr_type
                if arg_type.type_name.token_type != TokenType.STRING_TYPE:
                    self.error(f'Expecting type string, received type {arg_type.type_name.lexeme}', call_expr.fun_name)
                type_token = Token(TokenType.INT_TYPE, 'int', line, column)
            # dtoi
            elif func_name == 'dtoi':
                if len(call_expr.args) != 1:
                    self.error('Too many arguments for built in function, dtoi', call_expr.fun_name)
                call_expr.args[0].accept(self)
                arg_type = self.curr_type
                if arg_type.type_name.token_type != TokenType.DOUBLE_TYPE:
                    self.error(f'Expecting type double, received type {arg_type.type_name.lexeme}', call_expr.fun_name)
                type_token = Token(TokenType.INT_TYPE, 'int', line, column)
            # stod
            elif func_name == 'stod':
                if len(call_expr.args) != 1:
                    self.error('Too many arguments for built in function, stod', call_expr.fun_name)
                call_expr.args[0].accept(self)
                arg_type = self.curr_type
                if arg_type.type_name.token_type != TokenType.STRING_TYPE:
                    self.error(f'Expecting type string, received type {arg_type.type_name.lexeme}', call_expr.fun_name)
                type_token = Token(TokenType.DOUBLE_TYPE, 'double', line, column)
            # itod
            elif func_name == 'itod':
                if len(call_expr.args) != 1:
                    self.error('Too many arguments for built in function, itod', call_expr.fun_name)
                call_expr.args[0].accept(self)
                arg_type = self.curr_type
                if arg_type.type_name.token_type != TokenType.INT_TYPE:
                    self.error(f'Expecting type itod, received type {arg_type.type_name.lexeme}', call_expr.fun_name)
                type_token = Token(TokenType.DOUBLE_TYPE, 'double', line, column)
            # length
            elif func_name == 'length':
                if len(call_expr.args) != 1:
                    self.error('Too many arguments for built in function, length', call_expr.fun_name)
                call_expr.args[0].accept(self)
                arg_type = self.curr_type
                accepted_tokens = [TokenType.STRING_TYPE, TokenType.BOOL_TYPE, TokenType.DOUBLE_TYPE, TokenType.INT_TYPE]
                if arg_type.type_name.token_type == TokenType.BOOL_TYPE or arg_type.type_name.token_type == TokenType.INT_TYPE or arg_type.type_name.token_type == TokenType.DOUBLE_TYPE:
                    # check if it is an array
                    if not arg_type.is_array:
                        self.error(f'Cannot find length for type {arg_type.type_name.lexeme}', arg_type.type_name)
                if arg_type.type_name.token_type not in accepted_tokens:
                    self.error(f'Cannot find length for type {arg_type.type_name.lexeme}', arg_type.type_name)
                type_token = Token(TokenType.INT_TYPE, 'int', line, column)
            # get
            elif func_name == 'get':
                if len(call_expr.args) != 2:
                    self.error('Too many arguments for built in function, get', call_expr.fun_name)
                # first_arg
                call_expr.args[0].accept(self)
                first_arg = self.curr_type
                # second_arg
                call_expr.args[1].accept(self)
                second_arg = self.curr_type

                if first_arg.type_name.token_type != TokenType.INT_TYPE:
                    self.error(f'Expecting type int for first argument, received {first_arg.type_name.token_type} for function, get', call_expr.fun_name)
                if second_arg.type_name.token_type != TokenType.STRING_TYPE:
                    self.error(f'Expecting type string for second argument, received {second_arg.type_name.token_type} for function, get', call_expr.fun_name)
                # check array
                elif second_arg.is_array:
                    self.error(f'Expecting type string for second argument, received arrayfor function, get', call_expr.fun_name)
                type_token = Token(TokenType.STRING_TYPE, 'string', line, column)
            # keys
            elif func_name == 'keys':
                if len(call_expr.args) != 1:
                    self.error('Too many arguments for built in function, get', call_expr.fun_name)
                call_expr.args[0].accept(self)
                arg_type = self.curr_type
                # check dict type 
                if not arg_type.is_dict:
                    self.error(f'Expecting type dict for in argument for keys, received {arg_type.type_name.lexeme}', call_expr.fun_name)
                is_array = True
                type_token = Token(arg_type.key_type_name.token_type, arg_type.key_type_name.lexeme, line, column)
            # in
            elif func_name == 'in':
                if len(call_expr.args) != 2:
                    self.error('Too many arguments for built in function, get', call_expr.fun_name)
                call_expr.args[0].accept(self)
                arg_type = self.curr_type
                # check dict type 
                if not arg_type.is_dict:
                    self.error(f'Expecting type dict for in argument for keys, received {arg_type.type_name.lexeme}', call_expr.fun_name)
                call_expr.args[1].accept(self)
                arg_type = self.curr_type

                type_token = Token(TokenType.BOOL_TYPE, 'bool', line, column)            
            self.curr_type = DataType(is_array, False, None, None, type_token)
        else:
            # check params
            func = self.functions[call_expr.fun_name.lexeme]
            if len(call_expr.args) != len(func.params):
                self.error(f"Arguments do not match function definition of {func.fun_name.lexeme}", call_expr.fun_name)
            # check type matching of arguments passed
            for param in range(len(func.params)):
                call_expr.args[param].accept(self)
                arg_type = self.curr_type
                if (func.params[param].data_type.type_name.token_type != arg_type.type_name.token_type):
                    if (arg_type.type_name.token_type != TokenType.VOID_TYPE):
                        self.error(f'Mismatch of types in arguments passed to function {func.fun_name.lexeme} expecting {func.params[param].data_type.type_name.lexeme} received {arg_type.type_name.lexeme}', func.params[param].data_type.type_name)
            type_token = Token(func.return_type.type_name.token_type, func.return_type.type_name.lexeme, line, column)
            flag = False
            if func.return_type.is_array:
                flag = True
            self.curr_type = DataType(flag, False, None, None, type_token)



    def visit_expr(self, expr):
        # check lhs term
        expr.first.accept(self)
        # store inferred type
        lhs_type = self.curr_type
        type_token = None
        # check if more
        if expr.op:
            line = lhs_type.type_name.line
            column = lhs_type.type_name.column 
            op = expr.op
            # check rest of expr
            expr.rest.accept(self)
            # save rhs type
            rhs_type = self.curr_type
            math_ops = [TokenType.PLUS, TokenType.MINUS, TokenType.TIMES, TokenType.DIVIDE]
            comparison_ops = [TokenType.LESS, TokenType.GREATER, TokenType.LESS_EQ, TokenType.GREATER_EQ,TokenType.NOT_EQUAL, TokenType.EQUAL]
            bool_ops = [TokenType.AND, TokenType.OR, TokenType.NOT_EQUAL, TokenType.EQUAL]
            # ints
            if lhs_type.type_name.token_type == TokenType.INT_TYPE and rhs_type.type_name.token_type == TokenType.INT_TYPE:
                if op.token_type in math_ops:
                    type_token = Token(TokenType.INT_TYPE, 'int', line, column)
                elif op.token_type in comparison_ops:
                    type_token = Token(TokenType.BOOL_TYPE, 'bool', line, column)
                else:
                    self.error(f'Invalid operator {op} for type int and int', op)
            elif (lhs_type.type_name.token_type == TokenType.VOID_TYPE or lhs_type.type_name.token_type == TokenType.INT_TYPE) and (rhs_type.type_name.token_type == TokenType.VOID_TYPE or rhs_type.type_name.token_type == TokenType.INT_TYPE):
                if op.token_type in bool_ops:
                    type_token = Token(TokenType.BOOL_TYPE, 'bool', line, column)
                else:
                    self.error(f'Cannot use {op.lexeme} with a void type', op)
            # doubles
            elif lhs_type.type_name.token_type == TokenType.DOUBLE_TYPE and rhs_type.type_name.token_type == TokenType.DOUBLE_TYPE:
                if op.token_type in math_ops:
                    type_token = Token(TokenType.DOUBLE_TYPE, 'double', line, column)
                elif op.token_type in comparison_ops or op.token_type in bool_ops:
                    type_token = Token(TokenType.BOOL_TYPE, 'bool', line, column)
                else:
                    self.error(f'Invalid operator {op.lexeme} for type double and double', op)
            elif (lhs_type.type_name.token_type == TokenType.VOID_TYPE or lhs_type.type_name.token_type == TokenType.DOUBLE_TYPE) and (rhs_type.type_name.token_type == TokenType.VOID_TYPE or rhs_type.type_name.token_type == TokenType.DOUBLE_TYPE):
                if op.token_type in bool_ops or op.token_type in comparison_ops:
                    type_token = Token(TokenType.BOOL_TYPE, 'bool', line, column)
                else:
                    self.error(f'Cannot use {op.lexeme} with a void type', op)               
            # strings
            elif (lhs_type.type_name.token_type == TokenType.STRING_TYPE or lhs_type.type_name.token_type == TokenType.VOID_TYPE) and (rhs_type.type_name.token_type == TokenType.STRING_TYPE or rhs_type.type_name.token_type == TokenType.VOID_TYPE):
                if op.lexeme == '+':
                    type_token = Token(TokenType.STRING_TYPE, 'string', line, column)
                elif op.token_type in bool_ops or op.token_type in comparison_ops:
                    type_token = Token(TokenType.BOOL_TYPE, 'bool', line, column)
                else:
                    self.error(f'Invalid operator {op.lexeme} for type string and string', op)
            # bools
            elif (lhs_type.type_name.token_type == TokenType.BOOL_TYPE or lhs_type.type_name.token_type == TokenType.VOID_TYPE) and (rhs_type.type_name.token_type == TokenType.BOOL_TYPE or rhs_type.type_name.token_type == TokenType.VOID_TYPE):
                if op.token_type in bool_ops:
                    type_token = Token(TokenType.BOOL_TYPE, 'bool', line, column)
                else:
                    self.error(f'Cannot use operator {op.lexeme} with a boolean expression', op)
            # structs
            elif (lhs_type.type_name.token_type == TokenType.ID or lhs_type.type_name.token_type == TokenType.VOID_TYPE) and (rhs_type.type_name.token_type == TokenType.ID or rhs_type.type_name.token_type == TokenType.VOID_TYPE):
                if op.token_type in bool_ops:
                    type_token = Token(TokenType.BOOL_TYPE, 'bool', line, column)
                else:
                    self.error(f'Cannot use operator {op.lexeme} with Struct Comparison', op)
            # dict_type
            elif (lhs_type.type_name.token_type == TokenType.DICT or lhs_type.type_name.token_type == TokenType.VOID_TYPE) and (rhs_type.type_name.token_type == TokenType.DICT or rhs_type.type_name.token_type == TokenType.VOID_TYPE):
                if op.token_type in bool_ops:
                    type_token = Token(TokenType.BOOL_TYPE, 'bool', line, column)
                else:
                    self.error(f'Cannot use operator {op.lexeme} with Dictionary Comparison', op)
            # mismatch of types
            else:
                self.error(f'Mismatch of types {lhs_type.type_name.lexeme} and {rhs_type.type_name.lexeme}', op)
            self.curr_type = DataType(False, False, None, None, type_token)
        #if there is a not operator
        if expr.not_op:
            if self.curr_type.type_name.token_type != TokenType.BOOL_TYPE:
                self.error(f'Cannot use not operator on a non boolean expression of type {lhs_type.type_name.lexeme}', lhs_type.type_name)
            type_token = Token(TokenType.BOOL_TYPE, 'bool', self.curr_type.type_name.line, self.curr_type.type_name.column)
            self.curr_type = DataType(False, False, None, None, type_token)
        
        

    def visit_data_type(self, data_type):
        # note: allowing void (bad cases of void caught by parser)
        name = data_type.type_name.lexeme
        if name == 'void' or name in BASE_TYPES or name in self.structs:
            self.curr_type = data_type
        else: 
            self.error(f'invalid type "{name}"', data_type.type_name)
            
    
    def visit_var_def(self, var_def):
        typ = var_def.data_type.type_name.lexeme
        name = var_def.var_name.lexeme
        # type not right
        if typ not in BASE_TYPES and typ not in self.structs:
            self.error(f'Unknown Type {typ}', var_def.data_type.type_name)
        # cehck if already declared
        if self.symbol_table.exists_in_curr_env(name):
            self.error(f'Duplicate name {name}', var_def.var_name)

        self.symbol_table.add(name, var_def.data_type)
        
    def visit_simple_term(self, simple_term):
        simple_term.rvalue.accept(self)
        
    
    def visit_complex_term(self, complex_term):
        complex_term.expr.accept(self)

    def visit_simple_rvalue(self, simple_rvalue):
        value = simple_rvalue.value
        line = simple_rvalue.value.line
        column = simple_rvalue.value.column
        type_token = None
        if value.token_type == TokenType.INT_VAL:
            type_token = Token(TokenType.INT_TYPE, 'int', line, column)
        elif value.token_type == TokenType.DOUBLE_VAL:
            type_token = Token(TokenType.DOUBLE_TYPE, 'double', line, column)
        elif value.token_type == TokenType.STRING_VAL:
            type_token = Token(TokenType.STRING_TYPE, 'string', line, column)
        elif value.token_type == TokenType.BOOL_VAL:
            type_token = Token(TokenType.BOOL_TYPE, 'bool', line, column)
        elif value.token_type == TokenType.NULL_VAL:
            type_token = Token(TokenType.VOID_TYPE, 'void', line, column)
        self.curr_type = DataType(False, False, None, None, type_token)

        
    def visit_new_rvalue(self, new_rvalue):
        type_token = new_rvalue.type_name
        is_array = False
        is_dict = False
        # check array expr
        if new_rvalue.array_expr:
            if new_rvalue.type_name.token_type == TokenType.DICT:
                is_dict = True 
            else:
                is_array = True
            new_rvalue.array_expr.accept(self)
            arr = self.curr_type
            if arr.type_name.token_type != TokenType.INT_TYPE:
                self.error(f'Mismatch of new expression types {type_token.lexeme} and {arr.type_name.lexeme}', type_token)
        # struct params
        if new_rvalue.type_name.token_type == TokenType.ID:
            # check struct has been defined
            struct_list = list(self.structs.keys())
            if new_rvalue.type_name.lexeme not in struct_list:
                self.error(f'Struct {new_rvalue.type_name.lexeme} not defined', new_rvalue.type_name)
            struct = self.structs[new_rvalue.type_name.lexeme]
            # check params
            if not is_array and len(new_rvalue.struct_params) != len(struct.fields):
                self.error(f'Mismatch of fields given for struct {struct.struct_name.lexeme}', struct.struct_name)
            param_list = new_rvalue.struct_params
            for param in range(len(param_list)):
                param_list[param].accept(self)
                temp_type = self.curr_type
                if temp_type.type_name.token_type != struct.fields[param].data_type.type_name.token_type and temp_type.type_name.token_type != TokenType.VOID_TYPE:
                    self.error(f'Mismatch of types for field {temp_type.type_name.lexeme} and {struct.fields[param].data_type.type_name.lexeme}', temp_type.type_name)
                # check dictionary
                elif temp_type.is_dict and struct.fields[param].data_type.is_dict:
                    if (struct.fields[param].data_type.key_type_name.token_type != temp_type.key_type_name.token_type) or (struct.fields[param].data_type.element_type_name.token_type != temp_type.element_type_name.token_type):
                        self.error(f'Mismatch of types for field {temp_type.type_name.lexeme} and {struct.fields[param].data_type.type_name.lexeme}', temp_type.type_name)
        self.curr_type = DataType(is_array, is_dict, None, None, type_token)

        
            
    def visit_var_rvalue(self, var_rvalue):
        first = var_rvalue.path[0]
        line = first.var_name.line
        column = first.var_name.column
        if not self.symbol_table.exists(first.var_name.lexeme):
            self.error(f'Use before def error for {first.var_name.lexeme}', first.var_name)
        first_type = self.symbol_table.get(first.var_name.lexeme)
        token = self.symbol_table.get(first.var_name.lexeme).type_name.token_type
        key_type = first_type.key_type_name
        element_type = first_type.element_type_name
        is_array = self.symbol_table.get(first.var_name.lexeme).is_array
        is_dict = self.symbol_table.get(first.var_name.lexeme).is_dict

        # check for array expr on first
        if first.array_expr:
            first.array_expr.accept(self)
            if first_type.is_array:
                is_array = False
                # check that it is an integer
                if self.curr_type.type_name.token_type != TokenType.INT_TYPE:
                    self.error('Invalid type for indexing array', self.curr_type.type_name)
            elif first_type.is_dict:
                # check index type
                is_dict = False
                key_type_name = first_type.key_type_name
                if self.curr_type.type_name.token_type != key_type_name.token_type:
                    self.error(f'Invalid type for indexing dictionary {first.var_name.lexeme}', self.curr_type.type_name)
                # check element type and set that to first type
                element_type = first_type.element_type_name
                first_type = DataType(False, False, None, None, element_type)
        # go through more path if there
        if len(var_rvalue.path) > 1:
            for var in range(1, len(var_rvalue.path)):
                # check for a struct field
                if first_type.type_name.lexeme in self.structs:
                    struct = self.structs[first_type.type_name.lexeme]
                    # check var is a field
                    fields = {}
                    for field in struct.fields:
                        fields[field.var_name.lexeme] = field.data_type
                    try:
                         first_type = fields[var_rvalue.path[var].var_name.lexeme]
                    except:
                        self.error(f"field variable {var_rvalue.path[var].var_name.lexeme} doesnt exist for type {first_type.type_name.lexeme}", self.curr_type.type_name)
                # check for array_expr
                if var_rvalue.path[var].array_expr:
                    var_rvalue.path[var].array_expr.accept(self)
                    # array check
                    if first_type.is_array:
                        if self.curr_type.type_name.token_type != TokenType.INT_TYPE:
                            self.error('Invalid type for indexing array', self.curr_type.type_name)
                    # dictionary check
                    elif first_type.is_dict:
                        if first_type.key_type_name.token_type != self.curr_type.type_name.token_type:
                            self.error(f'Invalid type for indexing dictionary {var_rvalue.path[var].var_name.lexeme}', self.curr_type.type_name)
                        # update token
                        is_dict = False
                        key_type = None
                        element_type = None
                        first_type.type_name = first_type.element_type_name
                    else:
                        self.error('Invalid type for indexing', self.curr_type.type_name)
        token = Token(first_type.type_name.token_type, first_type.type_name.lexeme, line, column)
        self.curr_type = DataType(is_array, is_dict, key_type, element_type, token)

            

