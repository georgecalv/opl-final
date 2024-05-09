"""The MyPL Lexer class.

NAME: George Calvert
DATE: Spring 2024
CLASS: CPSC 326

"""

from mypl_token import *
from mypl_error import *


class Lexer:
    """For obtaining a token stream from a program."""

    def __init__(self, in_stream):
        """Create a Lexer over the given input stream.

        Args:
            in_stream -- The input stream. 

        """
        self.in_stream = in_stream
        self.line = 1
        self.column = 0


    def read(self):
        """Returns and removes one character from the input stream."""
        self.column += 1
        return self.in_stream.read_char()

    
    def peek(self):
        """Returns but doesn't remove one character from the input stream."""
        return self.in_stream.peek_char()

    
    def eof(self, ch):
        """Return true if end-of-file character"""
        return ch == ''

    
    def error(self, message, line, column):
        raise LexerError(f'{message} at line {line}, column {column}')

    
    def next_token(self):
        """Return the next token in the lexer's input stream."""
        # initialize
        ch = self.read()
        # new line or space
        if ch.isspace():
            if ch == "\n":
                self.line += 1
                self.column = 0
            return self.next_token()
        # dot
        elif ch == ".":
            return Token(TokenType.DOT, ".", self.line, self.column)
        # end of file
        elif self.eof(ch):
            return Token(TokenType.EOS, '', self.line, self.column)
        # semicolon
        elif ch == ";":
            return Token(TokenType.SEMICOLON, ";", self.line, self.column)
        # comments
        elif ch == "/" and self.peek() == "/":
            temp_col = self.column
            ch = " "
            self.read()
            self.read()
            n = self.peek()
            while not(self.eof(n)):
                if n == "\n":
                    break
                ch = ch + self.read()
                n = self.peek()
            return Token(TokenType.COMMENT, ch, self.line, temp_col)
        # comma
        elif ch == ",":
            return Token(TokenType.COMMA, ",", self.line, self.column)
        # plus
        elif ch == "+":
            return Token(TokenType.PLUS, "+", self.line, self.column)
        # minus
        elif ch == "-":
            return Token(TokenType.MINUS, "-", self.line, self.column)
        # times
        elif ch == "*":
            return Token(TokenType.TIMES, "*", self.line, self.column)
        # divide
        elif ch == "/":
            return Token(TokenType.DIVIDE, "/", self.line, self.column)
        # left paren
        elif ch == "(":
            return Token(TokenType.LPAREN, "(", self.line, self.column)
        # r paren
        elif ch == ")":
            return Token(TokenType.RPAREN, ")", self.line, self.column)
        # l bracket
        elif ch == "[":
            return Token(TokenType.LBRACKET, "[", self.line, self.column)
        # r bracket
        elif ch == "]":
            return Token(TokenType.RBRACKET, "]", self.line, self.column)
        # l cbrace
        elif ch == "{":
            return Token(TokenType.LBRACE, "{", self.line, self.column)
        # r cbrace
        elif ch == "}":
            return Token(TokenType.RBRACE, "}", self.line, self.column)
        # assign
        elif ch == "=":
            if self.peek() == "=":
                t_col = self.column
                self.read()
                return Token(TokenType.EQUAL, "==", self.line, t_col)
            else:
                return Token(TokenType.ASSIGN, "=", self.line, self.column)
        # less than
        elif ch == "<":
            if self.peek() == "=":
                t_col = self.column
                self.read()
                return Token(TokenType.LESS_EQ, "<=", self.line, t_col)
            else:
                return Token(TokenType.LESS, "<", self.line, self.column)
        # greater than
        elif ch == ">":
            if self.peek() == "=":
                t_col = self.column
                self.read()
                return Token(TokenType.GREATER_EQ, ">=", self.line, t_col)
            else:
                return Token(TokenType.GREATER, ">", self.line, self.column)
        # check for not equal
        elif ch == "!":
            t_col = self.column
            if self.peek() == "=":
                self.read()
                return Token(TokenType.NOT_EQUAL, "!=", self.line, t_col)
            else:
                self.error("LexerError: Invalid Use of !", self.line, t_col)
        # string vals
        elif ch == "\"":
            t = self.column
            end_check = True
            n = self.peek()
            
            if n == ch:
                self.read()
                return Token(TokenType.STRING_VAL, "", self.line, t)
            else:
                ch = self.read()
                n = self.peek()

                while n != "\"" or self.eof(n):
                    if n == "\n":
                        end_check = False
                    ch += self.read()
                    n = self.peek()
                self.read()
                if end_check:
                    return Token(TokenType.STRING_VAL, ch, self.line, t)
                else:
                    self.error("MyPLError: No Endquotes", self.line, t)
        # digits
        elif ch.isdecimal():
            type = TokenType.INT_VAL
            n = self.peek()
            t = self.column
            if ch == "0" and n.isdigit():
                self.error("LexerError: Leading Zero", self.line, t)
            check = False
            while n.isdecimal() or n == ".":
                if n == "." and not(check):
                    check = True
                    type = TokenType.DOUBLE_VAL
                    ch += self.read()
                    n = self.peek()
                    if n.isspace() or n == "":
                        self.error("LexerError: trailing decimal", self.line, t)
                        break
                elif n == "." and check: 
                    break
                else:
                    ch += self.read()
                    n = self.peek()
            if n.isalpha():
                self.error("LexerError: Invalid Number", self.line, t)
            return Token(type, ch, self.line, t)
        # keywords
        elif ch.isalpha():  
            n = self.peek()
            t = self.column
            while not(self.eof(n)):
                # end of read
                if n.isspace() or n == "(" or n == ")" or n == "=" or n == "," or n == '[' or n == ']' or n == '.' or n == '+' or n == '-' or n == '*' or n == '/' or n == '\n':
                    break
                # check ;
                elif ch == ";":
                    self.error("Lexer Error")
                # null
                elif ch == "null" and n.isspace():
                    return Token(TokenType.NULL_VAL, ch, self.line, t)
                # bool vals
                elif ch == "true" or ch == "false":
                    return Token(TokenType.BOOL_VAL, ch, self.line, t)
                # string type
                elif ch == "string" and (n.isspace() or n == "["):
                    return Token(TokenType.STRING_TYPE, ch, self.line, t)
                # int type
                elif ch == "int" and (n.isspace() or n == "["):
                    return Token(TokenType.INT_TYPE, ch, self.line, t)
                # bool type
                elif ch == "bool" and (n.isspace() or n == "["):
                    return Token(TokenType.BOOL_TYPE, ch, self.line, t)
                # double type
                elif ch == "double" and (n.isspace() or n == "["):
                    return Token(TokenType.DOUBLE_TYPE, ch, self.line, t)
                # void
                elif ch == "void" and n.isspace():
                    return Token(TokenType.VOID_TYPE, ch, self.line, t)
                # and
                elif ch == "and" and n.isspace():
                    return Token(TokenType.AND, ch, self.line, t)
                # not
                elif ch == "not" and n.isspace():
                    return Token(TokenType.NOT, ch, self.line, t)
                # or
                elif ch == "or" and n.isspace():
                    return Token(TokenType.OR, ch, self.line, t)
                # if
                elif ch == "if" and (n.isspace() or n == "("):
                    return Token(TokenType.IF, ch, self.line, t)
                # else
                elif ch == "else":
                    #elseif
                    if n == "i":
                        ch += self.read()
                        if self.peek() == "f":
                            ch += self.read()
                            return Token(TokenType.ELSEIF, ch, self.line, t)
                    return Token(TokenType.ELSE, ch, self.line, t)
                # while
                elif ch == "while" and (n.isspace() or n == "("):
                    return Token(TokenType.WHILE, ch, self.line, t)
                # for
                elif ch == "for" and (n.isspace() or n == "("):
                    return Token(TokenType.FOR, ch, self.line, t)
                # return
                elif ch == "return" and n.isspace():
                    return Token(TokenType.RETURN, ch, self.line, t)
                # struct
                elif ch == "struct" and n.isspace():
                    return Token(TokenType.STRUCT, ch, self.line, t)
                # array
                elif ch == "array" and n.isspace():
                    return Token(TokenType.ARRAY, ch, self.line, t)
                elif ch == "dict" and n.isspace():
                    return Token(TokenType.DICT, ch, self.line, t)
                # new
                elif ch == "new" and n.isspace():
                    return Token(TokenType.NEW, ch, self.line, t)
                # check ids
                elif n == "<" or n == ">" or n == "=" or n == ";":
                    if ch == "null":
                        return Token(TokenType.NULL_VAL, ch, self.line, t)
                    return Token(TokenType.ID, ch ,self.line, t)
                ch += self.read()
                n = self.peek()
            dict = {
                "null": TokenType.NULL_VAL,
                "true": TokenType.BOOL_VAL,
                "false": TokenType.BOOL_VAL,
                "string": TokenType.STRING_TYPE,
                "int": TokenType.INT_TYPE,
                "bool": TokenType.BOOL_TYPE,
                "double": TokenType.DOUBLE_TYPE,
                "void": TokenType.VOID_TYPE,
                "and": TokenType.AND,
                "if": TokenType.IF,
                "else": TokenType.ELSE,
                "elseif": TokenType.ELSEIF,
                "and": TokenType.AND,
                "not": TokenType.NOT,
                "or": TokenType.OR,
                "while": TokenType.WHILE,
                "for": TokenType.FOR,
                "return": TokenType.RETURN,
                "struct": TokenType.STRUCT,
                "array": TokenType.ARRAY,
                "new": TokenType.NEW,
                "dict": TokenType.DICT
            }
            try:
                return Token(dict[ch], ch, self.line, t)
            # ID
            except:
                return Token(TokenType.ID, ch, self.line, t)
        else:
            self.error("LexerError: Invalid Symbol", self.line, self.column)