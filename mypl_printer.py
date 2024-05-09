"""Print Visitor for pretty printing a MyPL program.

NAME: <your name here>
DATE: Spring 2024
CLASS: CPSC 326

"""

from dataclasses import dataclass
from mypl_token import Token, TokenType
from mypl_ast import *


class PrintVisitor(Visitor):
    """Visitor implementation to pretty print MyPL program."""

    def __init__(self):
        self.indent = 0

    # Helper Functions
        
    def output(self, msg):
        """Prints message without ending newline.

        Args:
           msg -- The string to print.

        """
        print(msg, end='')

        
    def output_indent(self):
        """Prints an initial indent string."""
        self.output('  ' * self.indent)


    def output_semicolon(self, stmt):
        """Prints a semicolon if the type of statment should end in a
        semicolon.
        
        Args:
            stmt -- The statement to print a semicolon after.

        """
        if type(stmt) in [VarDecl, AssignStmt, ReturnStmt, CallExpr]:
            self.output(';')

    # Visitor Functions
    
    def visit_program(self, program):
        for struct in program.struct_defs:
            struct.accept(self)
            self.output('\n')
        for fun in program.fun_defs:
            fun.accept(self)
            self.output('\n')            

            
    def visit_struct_def(self, struct_def):
        self.output('struct ' + struct_def.struct_name.lexeme + ' {\n')
        self.indent += 1
        for var_def in struct_def.fields:
            self.output_indent()
            var_def.accept(self)
            self.output(';\n')
        self.indent -= 1
        self.output('}\n')


    def visit_fun_def(self, fun_def):
        fun_def.return_type.accept(self)
        self.output(fun_def.fun_name.lexeme + '(')
        for i in range(len(fun_def.params)):
            fun_def.params[i].accept(self)
            if i < len(fun_def.params) - 1:
                self.output(', ')
        self.output(') {\n')
        self.indent += 1
        for stmt in fun_def.stmts:
            self.output_indent()
            self.visit_stmt_def(stmt)
            self.output_semicolon(stmt)
            self.output('\n')
        self.indent -= 1
        self.output('}\n')


    # TODO: Finish the rest of the visitor functions below
    def visit_stmt_def(self, stmt):
        stmt.accept(self)
        
    def visit_var_decl(self, var_decl):
        var_decl.var_def.accept(self)
        self.output(" = ")
        var_decl.expr.accept(self)
    
    def visit_var_def(self, var_def):
        var_def.data_type.accept(self)
        self.output(var_def.var_name.lexeme)
    
    def visit_data_type(self, data_type):
        if data_type.is_array:
            self.output("array ")
        self.output(data_type.type_name.lexeme + ' ')
    
    def visit_expr(self, expr):
        # not op check
        flag = False
        if expr.not_op:
            self.output('not (')
            falg = True

        # first expression
        f = expr.first
    
        f.accept(self)
   
        # operator
        if type(expr.op) == Token:
            self.output(' ' + expr.op.lexeme + ' ')
            

        # rest
        if type(expr.rest) == Expr:
            expr.rest.accept(self)
            if flag:
                self.output(')')

    def visit_simple_rvalue(self, simple_rvalue):
        if simple_rvalue.value.token_type == TokenType.STRING_VAL:
            self.output('\"' + simple_rvalue.value.lexeme + '\"')
        else:
            self.output(simple_rvalue.value.lexeme)

    def visit_simple_term(self, simple_term):
        simple_term.rvalue.accept(self)
    
    def visit_complex_term(self, complex_term):
        self.output('(')
        complex_term.expr.accept(self)
        self.output(')')

    def visit_call_expr(self, call_expr):
        self.output(call_expr.fun_name.lexeme + '(')
        
        for i in range(len(call_expr.args)):
            call_expr.args[i].accept(self)
            if i < len(call_expr.args) - 1:
                self.output(', ')
        self.output(')')

    def visit_return_stmt(self, return_stmt):
        self.output('return ')
        return_stmt.expr.accept(self)
    
    def visit_var_rvalue(self, var_rvalue):
        p = var_rvalue.path
        for var in range(len(p)):
            self.output(p[var].var_name.lexeme)
            if type(p[var].array_expr) == Expr:
                self.output('[')
                p[var].array_expr.accept(self)
                self.output(']')
            if var < len(p) - 1:
                self.output('.')

    def visit_if_stmt(self, if_stmt):
        # basic if
        self.output("if (")
        if_stmt.if_part.condition.accept(self)
        self.output(") {\n")
        self.indent += 1
        for stmt in if_stmt.if_part.stmts:
            self.output_indent()
            stmt.accept(self)
            self.output_semicolon(stmt)
            self.output('\n')
        self.indent -= 1
        self.output_indent()
        self.output('}')

        # else ifs
        if len(if_stmt.else_ifs) > 0:
            else_ifs = if_stmt.else_ifs
            for e in else_ifs:
                self.output('\n')
                self.output_indent()
                self.output("elseif (")
                e.condition.accept(self)
                self.output(") {\n")
                self.indent += 1
                for stmt in e.stmts:
                    self.output_indent()
                    stmt.accept(self)
                    self.output_semicolon(stmt)
                    self.output('\n')
                self.indent -= 1
                self.output_indent()
                self.output('}')
        # else
        if len(if_stmt.else_stmts) > 0:
            self.output('\n')
            self.output_indent()
            el = if_stmt.else_stmts
            self.output("else {\n")
            self.indent += 1
            for stmt in el:
                self.output_indent()
                stmt.accept(self)
                self.output_semicolon(stmt)
                self.output('\n')
            self.indent -= 1
            self.output_indent()
            self.output('}')
    
    def visit_assign_stmt(self, assign_stmt):
        # lvals
        lvals = assign_stmt.lvalue
        for ref in range(len(lvals)):
            self.output(lvals[ref].var_name.lexeme)
            if type(lvals[ref].array_expr) == Expr:
                self.output("[")
                lvals[ref].array_expr.accept(self)
                self.output("]")
            if ref < len(lvals) - 1:
                self.output('.')
        #  = 
        self.output(' = ')

        # expression
        assign_stmt.expr.accept(self)
    
    def visit_for_stmt(self, for_stmt):
        self.output("for (")
        # declaration
        for_stmt.var_decl.accept(self)
        self.output_semicolon(for_stmt.var_decl)
        self.output(" ")
        # condition
        for_stmt.condition.accept(self)
        self.output("; ")
        # assign
        for_stmt.assign_stmt.accept(self)
        self.output(') {\n')

        self.indent += 1
        for_stmts = for_stmt.stmts
        for stmt in range(len(for_stmts)):
            self.output_indent()  
            for_stmts[stmt].accept(self)    
            self.output_semicolon(for_stmts[stmt])
            self.output('\n')
        self.indent -= 1
        self.output_indent()
        self.output('}')  
    
    def visit_while_stmt(self, while_stmt):
        self.output('while (')
        while_stmt.condition.accept(self)
        self.output(') {\n')
        self.indent += 1
        # stmts
        for i in range(len(while_stmt.stmts)):
            self.output_indent()
            while_stmt.stmts[i].accept(self)
            self.output_semicolon(while_stmt.stmts[i])
            self.output('\n')
        self.indent -= 1
        self.output_indent()
        self.output('}')

    def visit_new_rvalue(self, new_rvalue):
        self.output(new_rvalue.type_name.lexeme)
        if type(new_rvalue.array_expr) == Expr:
            self.output('[')
            new_rvalue.array_expr.accept(self)
            self.output(']')
        self.output("(")
        if len(new_rvalue.struct_params) > 0:
            for i in range(len(new_rvalue.struct_params)):
                new_rvalue.struct_params[i].accept(self)
                if i < len(new_rvalue.struct_params) - 1:
                    self.output(', ')
        self.output(')')


                        




        
            

        





    
