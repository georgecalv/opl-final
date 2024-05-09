"""MyPL AST parser implementation.

NAME: George Calvert
DATE: Spring 2024
CLASS: CPSC 326
"""

from mypl_error import *
from mypl_token import *
from mypl_lexer import *
from mypl_ast import *


class ASTParser:

    def __init__(self, lexer):
        """Create a MyPL syntax checker (parser). 
        
        Args:
            lexer -- The lexer to use in the parser.

        """
        self.lexer = lexer
        self.curr_token = None

        
    def parse(self):
        """Start the parser, returning a Program AST node."""
        program_node = Program([], [])
        self.advance()
        while not self.match(TokenType.EOS):
            if self.match(TokenType.STRUCT):
                self.struct_def(program_node)
            else:
                self.fun_def(program_node)
        self.eat(TokenType.EOS, 'expecting EOF')
        return program_node

        
    #----------------------------------------------------------------------
    # Helper functions
    #----------------------------------------------------------------------

    def error(self, message):
        """Raises a formatted parser error.

        Args:
            message -- The basic message (expectation)

        """
        lexeme = self.curr_token.lexeme
        line = self.curr_token.line
        column = self.curr_token.column
        err_msg = f'{message} found "{lexeme}" at line {line}, column {column}'
        raise ParserError(err_msg)


    def advance(self):
        """Moves to the next token of the lexer."""
        self.curr_token = self.lexer.next_token()
        # skip comments
        while self.match(TokenType.COMMENT):
            self.curr_token = self.lexer.next_token()

            
    def match(self, token_type):
        """True if the current token type matches the given one.

        Args:
            token_type -- The token type to match on.

        """
        return self.curr_token.token_type == token_type

    
    def match_any(self, token_types):
        """True if current token type matches on of the given ones.

        Args:
            token_types -- Collection of token types to check against.

        """
        for token_type in token_types:
            if self.match(token_type):
                return True
        return False

    
    def eat(self, token_type, message):
        """Advances to next token if current tokey type matches given one,
        otherwise produces and error with the given message.

        Args: 
            token_type -- The totken type to match on.
            message -- Error message if types don't match.

        """
        if not self.match(token_type):
            self.error(message)
        self.advance()

        
    def is_bin_op(self):
        """Returns true if the current token is a binary operator."""
        ts = [TokenType.PLUS, TokenType.MINUS, TokenType.TIMES, TokenType.DIVIDE,
              TokenType.AND, TokenType.OR, TokenType.EQUAL, TokenType.LESS,
              TokenType.GREATER, TokenType.LESS_EQ, TokenType.GREATER_EQ,
              TokenType.NOT_EQUAL]
        return self.match_any(ts)


    #----------------------------------------------------------------------
    # Recursive descent functions
    #----------------------------------------------------------------------



    def struct_def(self, prog_node):
        """Check for well-formed struct definition."""
        struct_node = StructDef(None, [])
        # start
        self.eat(TokenType.STRUCT, "Expecting Struct in struct_def")
        struct_node.struct_name = self.curr_token
        self.eat(TokenType.ID, "Expecting ID in struct_def")
        self.eat(TokenType.LBRACE, "Expecting Left Brace in struct_def")
        # fields
        self.fields(struct_node)
        self.eat(TokenType.RBRACE, "Expecting Right Brace in struct_def")
        prog_node.struct_defs.append(struct_node)

    
    def fields(self, struct_node):
        """Check for well-formed struct fields."""
        # check if that is the last field
        if not self.match(TokenType.RBRACE):
            var_node = VarDef(None, None)
            # field
            var_node.data_type = self.data_type()
            if var_node.data_type.is_dict:
                self.advance()
                self.eat(TokenType.LPAREN, "Expecting ( in dict field")
                var_node.data_type.key_type_name = self.curr_token
                self.advance()
                self.eat(TokenType.COMMA, "Expecting , in dict field")
                var_node.data_type.element_type_name = self.curr_token 
                self.advance()
                self.eat(TokenType.RPAREN, "Expecting ) in dict field")
                var_node.var_name = self.curr_token
                self.eat(TokenType.ID, "Expecting ID in fields")
                self.eat(TokenType.SEMICOLON, "Expecting ; in fields")
                struct_node.fields.append(var_node)
                self.fields(struct_node)
            else:
                self.advance()
                var_node.var_name = self.curr_token
                self.eat(TokenType.ID, "Expecting ID in fields")
                self.eat(TokenType.SEMICOLON, "Expecting ; in fields")
                struct_node.fields.append(var_node)
                self.fields(struct_node)


    def fun_def(self, prog_node):
        """Check for well-formed function definition."""

        fun_node = FunDef(None, None, [], [])
        # void
        if self.match(TokenType.VOID_TYPE):
            data_type_node = DataType(False, False, None, None, self.curr_token)
            fun_node.return_type = data_type_node
            self.advance()
        # data type 
        else:
            if self.curr_token.token_type == TokenType.DICT:
                return_node = DataType(False, True, None, None, None)
                return_node.type_name = self.curr_token
                self.advance()
                self.eat(TokenType.LPAREN, "Expecting ( in dict return")
                return_node.key_type_name = self.curr_token
                self.advance()
                self.eat(TokenType.COMMA, "Expecting , in dict return")
                return_node.element_type_name = self.curr_token
                self.advance()
                self.eat(TokenType.RPAREN, "Expecting ) in dict return")
                fun_node.return_type = return_node
            else:
                fun_node.return_type = self.data_type()
                self.advance()

        fun_node.fun_name = self.curr_token
        self.eat(TokenType.ID, "Expecting ID in fun_def")
        self.eat(TokenType.LPAREN, "Expecting ( in fun_def")

        # parameters
        if not self.match(TokenType.RPAREN):
            self.params(fun_node)
        

        self.eat(TokenType.RPAREN, "Expecting ) in fun_def")
        self.eat(TokenType.LBRACE, "Expecting { in fun_def")


        while not self.match(TokenType.RBRACE):
            fun_node.stmts.append(self.stmt())
        self.eat(TokenType.RBRACE, "Expecting } in fun_def")
        prog_node.fun_defs.append(fun_node)

    def data_type(self):       
        """Check for well formed data type"""
        data_type_node = DataType(None, False, None, None,  None)
        # id
        if self.match(TokenType.ID):
            data_type_node.is_array = False
            data_type_node.type_name = self.curr_token
        # array
        elif self.match(TokenType.ARRAY):
            data_type_node.is_array = True
            self.advance()
            if self.match(TokenType.ID):
                data_type_node.type_name = self.curr_token
            else:
                data_type_node.type_name = self.base_type()
        elif self.match(TokenType.DICT):
            data_type_node.is_dict = True
            data_type_node.type_name = self.curr_token
            data_type_node.is_array = False
        
        else:
            data_type_node.is_array = False
            data_type_node.type_name  = self.base_type()
        return data_type_node


    def base_type(self):
        """Check for a Base type"""
        if not (self.match_any([TokenType.INT_TYPE, TokenType.DOUBLE_TYPE, TokenType.BOOL_TYPE, TokenType.STRING_TYPE, TokenType.EOS, TokenType.DICT])):
            self.error("Expecting Base Type in base_type")
        else:
            return self.curr_token


    def params(self, fun_node):
        """Check for well-formed function formal parameters."""
        var_node = VarDef(None, None)
        var_node.data_type = self.data_type()
        self.advance()
        # check for dictionary
        if var_node.data_type.is_dict:
            self.eat(TokenType.LPAREN, "Expecting ( in dict param)")
            var_node.data_type.key_type = self.curr_token
            self.advance()
            self.eat(TokenType.COMMA, "Expecting , in dict param")
            var_node.data_type.element_type_name = self.curr_token
            self.advance()
            self.eat(TokenType.RPAREN, "Expecting ) in dict param")
        var_node.var_name = self.curr_token
        self.eat(TokenType.ID, "Expecting ID in params")
        fun_node.params.append(var_node)
        # recursive case
        if self.match(TokenType.COMMA):
            self.eat(TokenType.COMMA, "Expecting , in params")
            self.params(fun_node)

    def stmt(self):
        """Check for a well formed statement"""
        # while
        if self.match(TokenType.WHILE):
            return self.while_stmt()
        # if
        elif self.match(TokenType.IF):
            return self.if_stmt()
        # for
        elif self.match(TokenType.FOR):
            return self.for_stmt()
        # return
        elif self.match(TokenType.RETURN):
            return_node = self.return_stmt()
            self.eat(TokenType.SEMICOLON, "Expecting ; in stmt")
            return return_node
        # assign or call or vdecl
        elif self.match(TokenType.ID): 
            id =  self.curr_token
            self.advance()
            # call expr
            if self.match(TokenType.LPAREN):
                call_expr_node = CallExpr(id, [])
                self.eat(TokenType.LPAREN, "Expecting ( in stmt call_expr")
                while not(self.match(TokenType.RPAREN)):
                    expr_node = Expr(False, None, None, None)
                    if self.match(TokenType.COMMA):
                        self.advance()
                    call_expr_node.args.append(self.expr(expr_node))
                self.eat(TokenType.RPAREN, "Expecting ) in stmt call_expr")
                self.eat(TokenType.SEMICOLON, "Expecting ; in stmt call_expr")
                return call_expr_node
            # assign
            else:
                check_assign = True
                check_cur = self.curr_token.token_type
                var_ref_node = VarRef(id, None)
                assign_node = AssignStmt([], None)

                if check_cur == TokenType.ASSIGN:
                    check_assign = False
                    self.advance()
                    expr_node = Expr(False, None, None, None)
                    assign_node.expr = self.expr(expr_node)
                # check if array reference
                if self.match(TokenType.LBRACKET):
                    self.advance()
                    expr_node = Expr(False, None, None, None)
                    var_ref_node.array_expr = self.expr(expr_node)
                    self.eat(TokenType.RBRACKET, "Expecting ] in stmt assign")
                assign_node.lvalue.append(var_ref_node)
                # dot reference
                while self.match(TokenType.DOT):
                    self.advance()
                    temp_var_node = VarRef(self.curr_token, None)
                    self.eat(TokenType.ID, "Excpecting ID is stmt assign dot")
                    # array reference
                    if self.match(TokenType.LBRACKET):
                        self.advance()
                        expr_node = Expr(False, None, None, None)
                        temp_var_node.array_expr = self.expr(expr_node)
                        self.eat(TokenType.RBRACKET, "Expecting ] in stmt assign dot")
                    assign_node.lvalue.append(temp_var_node)
                # struct type declaration so var decl
                if self.match(TokenType.ID):
                    # false since we know its not an array
                    struct_data_type = DataType(False, False, None, None, id)
                    struct_var_def_node = VarDef(struct_data_type, self.curr_token)
                    struct_var_node = VarDecl(struct_var_def_node, None)
                    self.advance()
                    if self.match(TokenType.ASSIGN):
                        check_assign = False
                        self.advance()
                        expr_node = Expr(False, None, None, None)
                        struct_var_node.expr = self.expr(expr_node)
                    self.eat(TokenType.SEMICOLON, "Expected ; in stmt assign struct")
                    return struct_var_node
                if check_assign:
                    self.eat(TokenType.ASSIGN, "Expecting = in stmt assign")
                    expr_node = Expr(False, None, None, None)
                    assign_node.expr = self.expr(expr_node)
                self.eat(TokenType.SEMICOLON, "Expecting ; in stmt assign")
                return assign_node
        elif self.match(TokenType.DICT):
            dict_data_type = DataType(False, True, None, None, self.curr_token)
            self.advance()
            
            # get types 
            self.eat(TokenType.LPAREN, "Expecting ( for dict declaration")
            key_type = self.curr_token
            self.advance()
            self.eat(TokenType.COMMA, "Expecting , for dict declaration")
            element_type = self.curr_token
            dict_data_type.key_type_name = key_type
            dict_data_type.element_type_name = element_type
            self.advance()
            self.eat(TokenType.RPAREN, "Expecting ) for dict declaration")
            # get name
            dict_var_def_node = VarDef(dict_data_type, self.curr_token)
            dict_var_node = VarDecl(dict_var_def_node, None)
            self.eat(TokenType.ID, "Expecting id in dict declaration")

            if self.match(TokenType.ASSIGN):
                self.advance()
                expr_node = Expr(None, None, None, None)
                dict_var_node.expr = self.expr(expr_node)

            
            self.eat(TokenType.SEMICOLON, "Expecting ; in stmt")
            return dict_var_node
        # vdecl
        else:
            v_decl_node = VarDecl(None, None)
            self.vdecl_stmt(v_decl_node)
            self.eat(TokenType.SEMICOLON, "Expecting ; in stmt") 
            return v_decl_node   

    def vdecl_stmt(self, v_decl_node):
        """Check for well declared variable delaration"""
        var_def_node = VarDef(None, None)
        var_def_node.data_type = self.data_type()
        self.advance()
        var_def_node.var_name = self.curr_token
        self.eat(TokenType.ID, "Expecting ID in vdecl_stmt")
        if self.match(TokenType.ASSIGN):
            self.advance()
            expr_node = Expr(False, None, None, None)
            v_decl_node.expr = self.expr(expr_node)
        v_decl_node.var_def = var_def_node
            
    def assign_stmt(self, assign_node):
        """Check for well formed assign statement"""
        self.l_value(assign_node)
        self.eat(TokenType.ASSIGN, "Expecting = in assign_stmt")
        expr_node = Expr(False, None, None, None)
        self.expr(expr_node)
        assign_node.expr = expr_node
        return assign_node

    def l_value(self, assign_node):
        """Check for well formed l value"""
        var_ref_node = VarRef(self.curr_token, None)
        self.eat(TokenType.ID, "Expecting ID in l_value")
        if self.match(TokenType.LBRACKET):
            self.advance()
            expr_node = Expr(False, None, None, None)
            var_ref_node.array_expr = self.expr(expr_node)
            self.eat(TokenType.RBRACKET, "Expecting ] in l_value")

        # dots
        if self.match(TokenType.DOT):
            self.advance()
            var_ref_node.var_name = self.curr_token
            var_ref_node.array_expr = None
            self.eat(TokenType.ID, "Expecting ID in l_value")
            # check for array reference
            if self.match(TokenType.LBRACKET):
                self.advance()
                expr_node = Expr(False, None, None, None)
                var_ref_node.array_expr = self.expr(expr_node)
                self.eat(TokenType.RBRACKET, "Expecting ] in l_value")
            assign_node.l_value.append(var_ref_node)    
            # cehck for more dots
            while self.match(TokenType.DOT):
                var_ref_node.var_name = self.curr_token
                var_ref_node.array_expr = None
                self.eat(TokenType.ID, "Expecting ID in l_value")
                if self.match(TokenType.LBRACKET):
                    self.advance()
                    expr_node = Expr(False, None, None, None)
                    var_ref_node.array_expr = self.expr(expr_node)
                    self.eat(TokenType.RBRACKET, "Expecting ] in l_value")
                assign_node.lvalue.append(var_ref_node)
                self.advance()
        assign_node.lvalue.append(var_ref_node)
                        


    def return_stmt(self):
        """Check for well formed return statement"""
        self.advance()
        return_node = ReturnStmt(None)
        expr_node = Expr(False, None, None, None)
        return_node.expr = self.expr(expr_node)
        return return_node


    def expr(self, expr_node):
        """Check for well formed expression"""
        # not 
        if self.match(TokenType.NOT):
            expr_node.not_op = True
            self.advance()
            self.expr(expr_node)
        elif self.match(TokenType.LPAREN):
            self.advance()
            tmp_node = Expr(False, None, None, None)
            complex_node = ComplexTerm(self.expr(tmp_node))
            expr_node.first = complex_node
            self.eat(TokenType.RPAREN, "Expecting ) in expr")
        # rvalue
        else:
            simple_node = SimpleTerm(self.r_value())
            expr_node.first = simple_node
        if self.is_bin_op():
            expr_node.op = self.curr_token
            self.advance()
            rest_node = Expr(False, None, None, None)
            expr_node.rest = self.expr(rest_node)
        return expr_node 
        
    def r_value(self):
        """Check for well formed r value"""
        # null or base r vals
        if not(self.match_any([TokenType.INT_VAL, TokenType.DOUBLE_VAL, TokenType.BOOL_VAL, TokenType.STRING_VAL, TokenType.NULL_VAL])):
            # new
            if self.match(TokenType.NEW):
                return self.new_r_value()
            # var r value or call expr
            else:
                id = self.curr_token
                varRvalue_node = VarRValue([])
                self.advance()
                # call expr
                if self.match(TokenType.LPAREN):
                    rval_call_expr_node = CallExpr(id, [])
                    self.eat(TokenType.LPAREN, "Expecting ( in r_value call_expr")
                    while not(self.match(TokenType.RPAREN)):
                        expr_node = Expr(False, None, None, None)
                        rval_call_expr_node.args.append(self.expr(expr_node))
                        while self.match(TokenType.COMMA):
                            self.advance()
                            expr_node = Expr(False, None, None, None)
                            rval_call_expr_node.args.append(self.expr(expr_node))
                    self.eat(TokenType.RPAREN, "Expecting ) in r_value call_expr")
                    return rval_call_expr_node
                # var rvalue
                else:
                    rval_var_ref_node = VarRef(id, None)
                    if self.match(TokenType.LBRACKET):
                        self.advance()
                        expr_node = Expr(False, None, None, None)
                        rval_var_ref_node.array_expr = self.expr(expr_node)
                        self.eat(TokenType.RBRACKET, "Expecting ] in var_rvalue")
                    varRvalue_node.path.append(rval_var_ref_node)
                    while self.match(TokenType.DOT):
                        self.advance()
                        temp_node = VarRef(self.curr_token, None)
                        self.eat(TokenType.ID, "Expecting ID in var_rvalue")
                        if self.match(TokenType.LBRACKET):
                            self.advance()
                            expr_node = Expr(False, None, None, None)
                            temp_node.array_expr = self.expr(expr_node)
                            self.eat(TokenType.RBRACKET, "Expecting ] in var_rvalue") 
                        varRvalue_node.path.append(temp_node)
                    return varRvalue_node
        #simple r value 
        else:
            simple_r_value_node = SimpleRValue(self.curr_token)
            self.advance()
            return simple_r_value_node


    def call_expr(self):
        """Check for well formed call expression"""
        call_expr_node = CallExpr(self.curr_token, [])
        self.eat(TokenType.ID, "Expecting ID in call_expr")
        self.eat(TokenType.LPAREN, "Expecting (")
        if not self.match(TokenType.RPAREN):
            expr_node = Expr(False, None, None, None)
            call_expr_node.args.append(self.expr(expr_node))
            self.advance()
            # multiple expressions
            while self.match(TokenType.COMMA):
                self.advance()
                expr_node = Expr(False, None, None, None)
                call_expr_node.args.append(self.expr(expr_node))
                self.advance()
                # expr_node = Expr(False, None, None, None)
                # call_expr_node.args.append(self.expr(expr_node))
                # self.advance()
        self.eat(TokenType.RPAREN, "Expecting ) in call_expr")
        return call_expr_node


    def var_rvalue(self):
        """Check for well formed variable r value"""
        var_ref_node = VarRef(None, None)
        var_ref_node.var_name = self.curr_token
        self.eat(TokenType.ID, "Expecting ID in var_rvalue")
        var_r_val_node = VarRValue([])

        # array
        if self.match(TokenType.LBRACKET):
            self.advance()
            expr_node = Expr(False, None, None, None)
            var_ref_node.array_expr = self.expr(expr_node)
            self.eat(TokenType.RBRACKET, "Expecting ] in var_rvalue")
        var_r_val_node.path.append(var_ref_node)
        # dots
        while self.match(TokenType.DOT):
            self.advance()
            var_ref_node.var_name = self.curr_token
            var_ref_node.array_expr = None
            self.eat(TokenType.ID, "Expecting ID in var_rvalue")

            if self.match(TokenType.LBRACKET):
                self.advance()
                expr_node = Expr(False, None, None, None)
                var_ref_node.array_expr = self.expr(expr_node)
                self.eat(TokenType.RBRACKET, "Expecting ] in var_rvalue")  
            var_r_val_node.path.append(var_ref_node)
        return var_r_val_node         


    def new_r_value(self):
        """check for well formed new r value"""
        self.advance()
        new_r_value_node = NewRValue(None, None, [])
        # check for id
        if self.match(TokenType.ID):
            new_r_value_node.type_name = self.curr_token
            self.advance()
            # check if lPAren or lbracket
            if self.match(TokenType.LPAREN):
                self.advance()
                new_r_value_node.struct_params = []
                # check if there is an expression
                # expression
                if not(self.match(TokenType.RPAREN)):
                    expr_node = Expr(False, None, None, None)
                    new_r_value_node.struct_params.append(self.expr(expr_node))
                    # check for comma
                    while self.match(TokenType.COMMA):
                        self.advance()
                        expr_node = Expr(False, None, None, None)
                        new_r_value_node.struct_params.append(self.expr(expr_node))
                self.eat(TokenType.RPAREN, "Expected ) in new_rvalue")
                return new_r_value_node

            # not lparen then it is bracket
            else:
                self.eat(TokenType.LBRACKET, "Expected [ in newrvalue")
                expr_node = Expr(False, None, None, None)
                self.expr(expr_node)
                new_r_value_node.array_expr = expr_node
                self.eat(TokenType.RBRACKET, "Expected ] in new_rvalue")

        # base type if not id
        else:
            # check for dictionary declaration
            if self.curr_token.token_type == TokenType.DICT:
                new_r_value_node.type_name = self.base_type()
                self.advance()
                self.eat(TokenType.LPAREN, "Expected ( in newrvalue")
                # expr_node = Expr(False, None, None, None)
                # self.expr(expr_node)
                # new_r_value_node.array_expr = expr_node
                self.eat(TokenType.RPAREN, "Expected ) in newrvalue")
            else:
                new_r_value_node.type_name = self.base_type()
                self.advance()
                self.eat(TokenType.LBRACKET, "Expected [ in new_rvalue")
                expr_node = Expr(False, None, None, None)
                new_r_value_node.array_expr = self.expr(expr_node)
                self.eat(TokenType.RBRACKET, "Expected ] in new_rvalue")
        return new_r_value_node
        
        

        
    def while_stmt(self):
        """Check for well formed while statement"""
        self.eat(TokenType.WHILE, "Expecting while in while_stmt")
        self.eat(TokenType.LPAREN, "Expecting ( in while_stmt")
        while_node = WhileStmt(None, []) 
        expr_node = Expr(False, None, None, None)
        while_node.condition = self.expr(expr_node)
        self.eat(TokenType.RPAREN, "Expecting ) in while_stmt")
        self.eat(TokenType.LBRACE, "Expecting { in while_stmt")
        while not(self.match(TokenType.RBRACE)):
            while_node.stmts.append(self.stmt())
        self.eat(TokenType.RBRACE, "Expecting } in while_stmt")
        return while_node

    def if_stmt(self):
        """Check for well formed if statement"""
        self.advance()
        if_stmt_node = IfStmt(None, [], [])
        self.eat(TokenType.LPAREN, "Expecting ( in if_stmt")
        basic_if_node = BasicIf(None, [])
        expr_node = Expr(False, None, None, None)
        basic_if_node.condition = self.expr(expr_node)
        self.eat(TokenType.RPAREN, "Expecting ) in if_stmt")
        self.eat(TokenType.LBRACE, "Expecting { in if_stmt")
        while not(self.match(TokenType.RBRACE)):
            basic_if_node.stmts.append(self.stmt())
        self.eat(TokenType.RBRACE, "Expecting } in if_stmt")
        if_stmt_node.if_part = basic_if_node

        # elses
        if self.match_any([TokenType.ELSE, TokenType.ELSEIF]):
            self.if_stmt_t(if_stmt_node)

        return if_stmt_node


    def if_stmt_t(self, if_stmt_node):
        """Check for well formed else if and else statments"""
        # elseif
        if self.match(TokenType.ELSEIF):
            basic_elseif_node = BasicIf(None, [])
            self.advance()
            self.eat(TokenType.LPAREN, "Expecting ( in if_stmt_t")
            expr_node = Expr(False, None, None, None)
            basic_elseif_node.condition = self.expr(expr_node)
            self.eat(TokenType.RPAREN, "Expecting )in if_stmt_t")
            self.eat(TokenType.LBRACE, "Expecting { in if_stmt_t")
            while not(self.match(TokenType.RBRACE)):
                basic_elseif_node.stmts.append(self.stmt())
            self.eat(TokenType.RBRACE, "Expecting } in if_stmt_t")
            if_stmt_node.else_ifs.append(basic_elseif_node)
            self.if_stmt_t(if_stmt_node)
        # else
        elif self.match(TokenType.ELSE):
            self.advance()
            self.eat(TokenType.LBRACE, "Expecting { in if_stmt_t")
            while not(self.match(TokenType.RBRACE)):
                if_stmt_node.else_stmts.append(self.stmt())
            self.eat(TokenType.RBRACE, "Expecting } in if_stmt_t")
        # nothing


    def for_stmt(self):
        for_loop_node = ForStmt(None, None, None, [])
        """Check for well formed for loop"""
        self.eat(TokenType.FOR, "Expecting for in fot_stmt")
        self.eat(TokenType.LPAREN, "Expecting ( in fot_stmt")
        var_decl_node = VarDecl(None, None)
        self.vdecl_stmt(var_decl_node)
        self.eat(TokenType.SEMICOLON, "Expecting ; in fot_stmt")

        for_loop_node.var_decl = var_decl_node
        expr_node = Expr(False, None, None, None)
        for_loop_node.condition = self.expr(expr_node)
        self.eat(TokenType.SEMICOLON, "Expecting ; in fot_stmt")
    
        assign_node = AssignStmt([], None)

        for_loop_node.assign_stmt = self.assign_stmt(assign_node)

        self.eat(TokenType.RPAREN, "Expecting ) in fot_stmt")
        self.eat(TokenType.LBRACE, "Expecting { in fot_stmt")
        while not(self.match(TokenType.RBRACE)):
            for_loop_node.stmts.append(self.stmt())
        self.eat(TokenType.RBRACE, "Expected } in fot_stmt")
        return for_loop_node
    

    
                
            
