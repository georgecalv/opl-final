"""MyPL simple syntax checker (parser) implementation.

NAME: George Calvert
DATE: Spring 2024
CLASS: CPSC 326
"""

from mypl_error import *
from mypl_token import *
from mypl_lexer import *


class SimpleParser:
    def __init__(self, lexer):
        """Create a MyPL syntax checker (parser). 
        
        Args:
            lexer -- The lexer to use in the parser.

        """
        self.lexer = lexer
        self.curr_token = None

        
    def parse(self):
        """Start the parser."""
        self.advance()
        while not self.match(TokenType.EOS):
            if self.match(TokenType.STRUCT):
                self.struct_def()
            else:
                self.fun_def()
        
        
        self.eat(TokenType.EOS, 'expecting EOF')

        
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
        """Returns true if the current token is a binary operation token."""
        ts = [TokenType.PLUS, TokenType.MINUS, TokenType.TIMES, TokenType.DIVIDE,
              TokenType.AND, TokenType.OR, TokenType.EQUAL, TokenType.LESS,
              TokenType.GREATER, TokenType.LESS_EQ, TokenType.GREATER_EQ,
              TokenType.NOT_EQUAL]
        return self.match_any(ts)

    
    #----------------------------------------------------------------------
    # Recursive descent functions
    #----------------------------------------------------------------------
        
    def struct_def(self):
        """Check for well-formed struct definition."""
        # start
        self.eat(TokenType.STRUCT, "Expecting Struct in struct_def")
        self.eat(TokenType.ID, "Expecting ID in struct_def")
        self.eat(TokenType.LBRACE, "Expecting Left Brace in struct_def")
        # fields
        self.fields()
        self.eat(TokenType.RBRACE, "Expecting Right Brace in struct_def")

        
    def fields(self):
        """Check for well-formed struct fields."""
        # check if that is the last field
        if not self.match(TokenType.RBRACE):
            # field
            self.data_type()
            self.eat(TokenType.ID, "Expecting ID in fields")
            self.eat(TokenType.SEMICOLON, "Expecting ; in fields")
            self.fields()


    def fun_def(self):
        """Check for well-formed function definition."""
        # void
        if self.match(TokenType.VOID_TYPE):
            self.eat(TokenType.VOID_TYPE, "Expecting void in fun_def")
        # data type 
        else:
            self.data_type()
        self.eat(TokenType.ID, "Expecting ID in fun_def")
        self.eat(TokenType.LPAREN, "Expecting ( in fun_def")

        # parameters
        if not self.match(TokenType.RPAREN):
            self.params()
        self.eat(TokenType.RPAREN, "Expecting ) in fun_def")
        self.eat(TokenType.LBRACE, "Expecting { in fun_def")
        while not(self.match(TokenType.RBRACE)):
            self.stmt()
        self.eat(TokenType.RBRACE, "Expecting } in fun_def")

    def data_type(self):
        """Check for well formed data type"""
        # id
        if self.match(TokenType.ID):
            self.eat(TokenType.ID, "Expecting ID in data_type")
        # array
        elif self.match(TokenType.ARRAY):
            self.eat(TokenType.ARRAY, "Expecting array in data_type")
            # check for base type or id
            if self.match(TokenType.ID):
                self.eat(TokenType.ID, "Expecting ID in data_type")
            else:
                self.base_type()

        # base type
        else:
            self.base_type()

    def base_type(self):
        """Check for a Base type"""
        if not (self.match_any([TokenType.INT_TYPE, TokenType.DOUBLE_TYPE, TokenType.BOOL_TYPE, TokenType.STRING_TYPE, TokenType.EOS])):
            self.error("Expecting Base Type in base_type")
        else:
            self.advance()


    def params(self):
        """Check for well-formed function formal parameters."""
        self.data_type()
        self.eat(TokenType.ID, "Expecting ID in params")
        # recursive case
        if self.match(TokenType.COMMA):
            self.eat(TokenType.COMMA, "Expecting , in params")
            self.params()

    def stmt(self):
        """Check for a well formed statement"""
        # while
        if self.match(TokenType.WHILE):
            self.while_stmt()
        # if
        elif self.match(TokenType.IF):
            self.if_stmt()
        # for
        elif self.match(TokenType.FOR):
            self.for_stmt()
        # return
        elif self.match(TokenType.RETURN):
            self.return_stmt()
            self.eat(TokenType.SEMICOLON, "Expecting ; in stmt")
        # assign or call or vdecl
        elif self.match(TokenType.ID): 
            check = True
            self.advance()
            # call expr
            if self.match(TokenType.LPAREN):
                self.eat(TokenType.LPAREN, "Expecting ( in stmt call_expr")
                while not(self.match(TokenType.RPAREN)):
                    self.expr()
                    while self.match(TokenType.COMMA):
                        self.expr()
                self.eat(TokenType.RPAREN, "Expecting ) in stmt call_expr")
                self.eat(TokenType.SEMICOLON, "Expecting ; in stmt call_expr")
            # assign
            else:
                # lvalue
                # lBRACKET
                if self.match(TokenType.LBRACKET):
                    self.advance()
                    self.expr()
                    self.eat(TokenType.RBRACKET, "Expecting ] in stmt assign")
                # dot
                while self.match(TokenType.DOT):
                    self.advance()
                    self.eat(TokenType.ID, "Expecting ID in stmt assign dot")
                    if self.match(TokenType.LBRACKET):
                        self.advance()
                        self.expr()
                        self.eat(TokenType.RBRACKET, "Expecting ] in stmt assign dot")
                # struct type declaration
                if self.match(TokenType.ID):
                    self.advance()
                    if self.match(TokenType.SEMICOLON):
                        check = False
                # check for double id
                if check:
                    self.eat(TokenType.ASSIGN, "Expecting = in stmt assign")
                    self.expr()
                self.eat(TokenType.SEMICOLON, "Expecting ; in stmt assign")
        # vdecl
        else:
            self.vdecl_stmt()
            self.eat(TokenType.SEMICOLON, "Expecting ; in stmt")    
    
    def vdecl_stmt(self):
        """Check for well declared variable delaration"""
        self.data_type()
        self.eat(TokenType.ID, "Expecting ID in vdecl_stmt")
        if self.match(TokenType.ASSIGN):
            self.advance()
            self.expr()
            
    def assign_stmt(self):
        """Check for well formed assign statement"""
        self.l_value()
        self.eat(TokenType.ASSIGN, "Expecting = in assign_stmt")
        self.expr()

    def l_value(self):
        """Check for well formed l value"""
        self.eat(TokenType.ID, "Expecting ID in l_value")
        if self.match(TokenType.LBRACKET):
            self.advance()
            self.expr()
            self.eat(TokenType.RBRACKET, "Expecting ] in l_value")
        if self.match(TokenType.DOT):
            self.advance()
            while self.match(TokenType.DOT):
                self.eat(TokenType.ID, "Expecting ID in l_value")
                if self.match(TokenType.LBRACKET):
                    self.advance()
                    self.expr()
                    self.eat(TokenType.RBRACKET, "Expecting ] in l_value")
                self.advance()
        # advance when it is struct_def id = expr()
        if self.match(TokenType.ID):
            self.advance()
        # self.advance()
                     


    def return_stmt(self):
        """Check for well formed return statement"""
        self.advance()
        self.expr()


    def expr(self):
        """Check for well formed expression"""
        # not
        if self.match(TokenType.NOT):
            self.advance()
            self.expr()
        # parens
        elif self.match(TokenType.LPAREN):
            self.advance()
            self.expr()
            self.eat(TokenType.RPAREN, "Expecting ) in expr")
        # r value
        else:
            self.r_value()

        # check for more expressions
        # binary operator
        if self.is_bin_op():
            self.advance()
            self.expr()
        
        
        
        
    def r_value(self):
        """Check for well formed r value"""
        # null or base r vals
        if not(self.match_any([TokenType.INT_VAL, TokenType.DOUBLE_VAL, TokenType.BOOL_VAL, TokenType.STRING_VAL, TokenType.NULL_VAL])):
            # new
            if self.match(TokenType.NEW):
                self.new_r_value()
            # var r value or call expr
            else:
                self.advance()
                # call expr
                if self.match(TokenType.LPAREN):
                    self.eat(TokenType.LPAREN, "Expecting ( in r_value call_expr")
                    while not(self.match(TokenType.RPAREN)):
                        self.expr()
                        while self.match(TokenType.COMMA):
                            self.expr()
                    self.eat(TokenType.RPAREN, "Expecting ) in r_value call_expr")
                # var rvalue
                else:
                    if self.match(TokenType.LBRACKET):
                        self.advance()
                        self.expr()
                        self.eat(TokenType.RBRACKET, "Expecting ] in var_rvalue")
                    
                    while self.match(TokenType.DOT):
                        self.advance()
                        self.eat(TokenType.ID, "Expecting ID in var_rvalue")
                        if self.match(TokenType.LBRACKET):
                            self.advance()
                            self.expr()
                            self.eat(TokenType.RBRACKET, "Expecting ] in var_rvalue") 
                    
        else:
            self.advance()


    def call_expr(self):
        """Check for well formed call expression"""
        self.eat(TokenType.ID, "Expecting ID in call_expr")
        self.eat(TokenType.LPAREN, "Expecting (")
        if not self.match(TokenType.RPAREN):
            self.expr()
            self.advance()
            # multiple expressions
            while self.match(TokenType.COMMA):
                self.expr()
                self.advance()
        self.eat(TokenType.RPAREN, "Expecting ) in call_expr")


    def var_rvalue(self):
        """Check for well formed variable r value"""
        self.eat(TokenType.ID, "Expecting ID in var_rvalue")

        if self.match(TokenType.LBRACKET):
            self.advance()
            self.expr()
            self.eat(TokenType.RBRACKET, "Expecting ] in var_rvalue")
        
        while self.match(TokenType.DOT):
            self.advance()
            self.eat(TokenType.ID, "Expecting ID in var_rvalue")
            if self.match(TokenType.LBRACKET):
                self.advance()
                self.expr()
                self.eat(TokenType.RBRACKET, "Expecting ] in var_rvalue")           


    def new_r_value(self):
        """check for well formed new r value"""
        self.advance()
        # check for id
        if self.match(TokenType.ID):
            self.advance()
            # check if lPAren or lbracket
            if self.match(TokenType.LPAREN):
                self.advance()
                # check if ther is an expression
                # expression
                if not(self.match(TokenType.RPAREN)):
                    self.expr()
                    # check for comma
                    while self.match(TokenType.COMMA):
                        self.advance()
                        self.expr()
                        # self.advance()
                self.eat(TokenType.RPAREN, "Expected ) in new_rvalue")

            # not lparen then it is bracket
            else:
                self.eat(TokenType.LBRACKET, "Expected [ in newrvalue")
                self.expr()
                self.eat(TokenType.RBRACKET, "Expected ] in new_rvalue")

        # base type if not id
        else:
            self.base_type()
            self.eat(TokenType.LBRACKET, "Expected [ in new_rvalue")
            self.expr()
            self.eat(TokenType.RBRACKET, "Expected ] in new_rvalue")
        
        

        
    def while_stmt(self):
        """Check for well formed while statement"""
        self.eat(TokenType.WHILE, "Expecting while in while_stmt")
        self.eat(TokenType.LPAREN, "Expecting ( in while_stmt")
        self.expr()
        self.eat(TokenType.RPAREN, "Expecting ) in while_stmt")
        self.eat(TokenType.LBRACE, "Expecting { in while_stmt")
        while not(self.match(TokenType.RBRACE)):
            self.stmt()
        self.eat(TokenType.RBRACE, "Expecting } in while_stmt")

    def if_stmt(self):
        """Check for well formed if statement"""
        self.advance()
        self.eat(TokenType.LPAREN, "Expecting ( in if_stmt")
        self.expr()
        self.eat(TokenType.RPAREN, "Expecting ) in if_stmt")
        self.eat(TokenType.LBRACE, "Expecting { in if_stmt")
        while not(self.match(TokenType.RBRACE)):
            self.stmt()
        self.eat(TokenType.RBRACE, "Expecting } in if_stmt")
        # elses
        if self.match_any([TokenType.ELSE, TokenType.ELSEIF]):
            self.if_stmt_t()

    def if_stmt_t(self):
        """Check for well formed else if and else statments"""
        # elseif
        if self.match(TokenType.ELSEIF):
            self.advance()
            self.eat(TokenType.LPAREN, "Expecting ( in if_stmt_t")
            self.expr()
            self.eat(TokenType.RPAREN, "Expecting )in if_stmt_t")
            self.eat(TokenType.LBRACE, "Expecting { in if_stmt_t")
            while not(self.match(TokenType.RBRACE)):
                self.stmt()
            self.eat(TokenType.RBRACE, "Expecting } in if_stmt_t")
            self.if_stmt_t()
        # else
        elif self.match(TokenType.ELSE):
            self.advance()
            self.eat(TokenType.LBRACE, "Expecting { in if_stmt_t")
            while not(self.match(TokenType.RBRACE)):
                self.stmt()
            self.eat(TokenType.RBRACE, "Expecting } in if_stmt_t")
        # nothing


    def for_stmt(self):
        """Check for well formed for loop"""
        self.eat(TokenType.FOR, "Expecting for in fot_stmt")
        self.eat(TokenType.LPAREN, "Expecting ( in fot_stmt")

        self.vdecl_stmt()
        self.eat(TokenType.SEMICOLON, "Expecting ; in fot_stmt")

        self.expr()
        self.eat(TokenType.SEMICOLON, "Expecting ; in fot_stmt")

        self.assign_stmt()
        self.eat(TokenType.RPAREN, "Expecting ) in fot_stmt")
        self.eat(TokenType.LBRACE, "Expecting { in fot_stmt")
        while not(self.match(TokenType.RBRACE)):
            self.stmt()
        self.eat(TokenType.RBRACE, "Expected } in fot_stmt")
