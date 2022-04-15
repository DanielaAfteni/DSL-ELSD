####################################### IMPORTS #######################################
# function for the display arrows pointing at where the error came from 
from strings_with_arrows import *

import string
import os
import math



####################################### CONSTANTS #######################################

# the digit and letters constants that are going to be introduced
DIGITS = '0123456789'
LETTERS = string.ascii_letters
LETTERS_DIGITS = LETTERS + DIGITS



####################################### ERRORS #######################################

# our own custom error class
class Error:

  # function to take in the error name, start and end position, and some details (by assigning that to the parameters)
  def __init__(self, pos_start, pos_end, error_name, details):
    self.pos_start = pos_start
    self.pos_end = pos_end
    self.error_name = error_name
    self.details = details
  

  # function to create a string that shows the error's name 
  # and other details as: file name, line number (+1, because there is no line 0) start and end position
  def as_string(self):
    result  = f'{self.error_name}: {self.details}\n'
    result += f'File {self.pos_start.fn}, line {self.pos_start.ln + 1}'
    result += '\n\n' + string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
    return result


# class for illegal characters
class IllegalCharError(Error):
  # take in the error and call the super method, 
  # and we will pass in an error name of illegal character and the rest of the information
  def __init__(self, pos_start, pos_end, details):
    super().__init__(pos_start, pos_end, 'Illegal Character', details)


# class for expected char error
class ExpectedCharError(Error):
  # take in the error and call the super method, 
  # and we will pass in an error name of expected char error and the rest of the information
  def __init__(self, pos_start, pos_end, details):
    super().__init__(pos_start, pos_end, 'Expected Character', details)


# class for invalid syntax error (in the parsing process)
class InvalidSyntaxError(Error):
  # take in the error and call the super method, 
  # and we will pass in an error name of invalid syntax error and the rest of the information
  def __init__(self, pos_start, pos_end, details=''):
    super().__init__(pos_start, pos_end, 'Invalid Syntax', details)


# class for run time error
class RTError(Error):
    # take in the error and call the super method, 
    # and we will pass in an error name of invalid syntax error and the rest of the information
  def __init__(self, pos_start, pos_end, details, context):
    super().__init__(pos_start, pos_end, 'Runtime Error', details)
    self.context = context


  # function that creates a string that shows the genereated traceback
  def as_string(self):
    result  = self.generate_traceback()
    result += f'{self.error_name}: {self.details}'
    result += '\n\n' + string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
    return result


  # method to show the most recent call last, traceback
  def generate_traceback(self):
    result = ''
    pos = self.pos_start
    ctx = self.context

    while ctx:
      result = f'  File {pos.fn}, line {str(pos.ln + 1)}, in {ctx.display_name}\n' + result
      pos = ctx.parent_entry_pos
      ctx = ctx.parent

    return 'Traceback (most recent call last):\n' + result



####################################### POSITION #######################################

# class to keep in track of the line and column numbers, current index, file name and file content while the lexer is running
# thus, when we show error, we can point exactly where the error came from, which: file name, error, line (from the file text property). 
# this is for the not in one line text 
class Position:
  # function to take in the index, line, column, file name and file content
  def __init__(self, idx, ln, col, fn, ftxt):
    self.idx = idx
    self.ln = ln
    self.col = col
    self.fn = fn
    self.ftxt = ftxt


  # function for the advance: just move on to the next index and then update line and column numbers
  def advance(self, current_char=None):
    # we increment the index and the column
    self.idx += 1
    self.col += 1

    # if the current character is equal to a new line then
    if current_char == '\n':
      # we increment the line and reset the column equal to 0
      self.ln += 1
      self.col = 0

    return self


  # function that creates a copy of the position
  def copy(self):
    return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)



####################################### TOKENS #######################################


# constants for the token type
TT_INT				= 'INT'           # int
TT_FLOAT    	= 'FLOAT'         # float
TT_STRING			= 'STRING'        # string
TT_IDENTIFIER	= 'IDENTIFIER'    # identifier
TT_KEYWORD		= 'KEYWORD'       # keyword
TT_PLUS     	= 'PLUS'          # +
TT_MINUS    	= 'MINUS'         # -
TT_MUL      	= 'MUL'           # *
TT_DIV      	= 'DIV'           # /
TT_POW				= 'POW'           # ^
TT_EQ					= 'EQ'            # =
TT_LPAREN   	= 'LPAREN'        # (
TT_RPAREN   	= 'RPAREN'        # )
TT_LSQUARE    = 'LSQUARE'       # [
TT_RSQUARE    = 'RSQUARE'       # ]
TT_EE					= 'EE'            # ==
TT_NE					= 'NE'            # !=
TT_LT					= 'LT'            # >
TT_GT					= 'GT'            # <
TT_LTE				= 'LTE'           # >=
TT_GTE				= 'GTE'           # <=
TT_COMMA			= 'COMMA'         # ,
TT_ARROW			= 'ARROW'         # ->
TT_NEWLINE		= 'NEWLINE'       # /t
TT_EOF				= 'EOF'           # end


KEYWORDS = [
  'VAR',
  'AND',
  'OR',
  'NOT',
  'IF',
  'ELIF',
  'ELSE',
  'FOR',
  'TO',
  'INCREMENT',
  'WHILE',
  'FUNCTION',
  'THEN',
  'END',
  'RETURN',
  'CONTINUE',
  'BREAK',
  'START',
  'RIGHT',
  'LEFT',
  'UP',
  'DOWN',
  'WIDTH',
  'LENGHT'
]


class Token:
  # the token type and value of the current token, and othe details as start position and end position (to determine where the error is present)
  # initially set as default values None
  def __init__(self, type_, value=None, pos_start=None, pos_end=None):
    self.type = type_
    self.value = value

    # we will check if there is a position start
    if pos_start:
      # and then assign the start, end position to that position, and advance the end position (by adding 1)
      self.pos_start = pos_start.copy()
      self.pos_end = pos_start.copy()
      self.pos_end.advance()

    # we will check if there is a position end
    if pos_end:
      # and then assign end position to that position
      self.pos_end = pos_end.copy()

  def matches(self, type_, value):
    return self.type == type_ and self.value == value
  
  # the token representation, includind: token type and value
  # in case it does not have value, then return just its type
  def __repr__(self):
    if self.value: return f'{self.type}:{self.value}'
    return f'{self.type}'



####################################### LEXER #######################################

class Lexer:
  # take in the text that we process from the file name
  def __init__(self, fn, text):
    self.fn = fn
    self.text = text
    # keep the track of the current position
    # we set the index and column equal to -1, because then we increment both of them by advance
    self.pos = Position(-1, 0, -1, fn, text)
    # keep the track of the current character, and advance to the next one
    self.current_char = None
    self.advance()
  

  # function to advance to the next character in the text
  def advance(self):
    self.pos.advance(self.current_char)
    # by changing the position, we set the current character equal to the character at that index position inside the text
    # we do that just when the index position is less than the lenght of the text, else we do nothing
    self.current_char = self.text[self.pos.idx] if self.pos.idx < len(self.text) else None


  # function to make tokens, depending on what is written in console
  def make_tokens(self):
    # create an empty list of tokens
    tokens = []

    # while the current character is not a None
    while self.current_char != None:
      # then we ignore the character: tab
      if self.current_char in ' \t':
        self.advance()
      # and for the rest of the characters, when we meet them, we call their corresponding fuctions:
      # - # ! = > < digits letters    
      elif self.current_char == '#':
        self.skip_comment()
      elif self.current_char in ';\n':
        tokens.append(Token(TT_NEWLINE, pos_start=self.pos))
        self.advance()
      elif self.current_char in DIGITS:
        tokens.append(self.make_number())
      elif self.current_char in LETTERS:
        tokens.append(self.make_identifier())
      elif self.current_char == '"':
        tokens.append(self.make_string())
      # if current character: + * / ^ ( ) [ ] , ; EOF
      # then we append a new token of type: + * / ^ ( ) [ ] , EOF to the list of tokens
      # and advance to the next current character
      elif self.current_char == '+':
        tokens.append(Token(TT_PLUS, pos_start=self.pos))
        self.advance()
      elif self.current_char == '-':
        tokens.append(self.make_minus_or_arrow())
      elif self.current_char == '*':
        tokens.append(Token(TT_MUL, pos_start=self.pos))
        self.advance()
      elif self.current_char == '/':
        tokens.append(Token(TT_DIV, pos_start=self.pos))
        self.advance()
      elif self.current_char == '^':
        tokens.append(Token(TT_POW, pos_start=self.pos))
        self.advance()
      elif self.current_char == '(':
        tokens.append(Token(TT_LPAREN, pos_start=self.pos))
        self.advance()
      elif self.current_char == ')':
        tokens.append(Token(TT_RPAREN, pos_start=self.pos))
        self.advance()
      elif self.current_char == '[':
        tokens.append(Token(TT_LSQUARE, pos_start=self.pos))
        self.advance()
      elif self.current_char == ']':
        tokens.append(Token(TT_RSQUARE, pos_start=self.pos))
        self.advance()
      elif self.current_char == '!':
        token, error = self.make_not_equals()
        if error: return [], error
        tokens.append(token)
      elif self.current_char == '=':
        tokens.append(self.make_equals())
      elif self.current_char == '<':
        tokens.append(self.make_less_than())
      elif self.current_char == '>':
        tokens.append(self.make_greater_than())
      elif self.current_char == ',':
        tokens.append(Token(TT_COMMA, pos_start=self.pos))
        self.advance()
      else:
        # get the position start by making a copy of our current position
        # if we do not come across the character we are looking for 
        # then we are going to store that character in a variable (char), we will advance
        pos_start = self.pos.copy()
        char = self.current_char
        self.advance()
        # and then return the empty list (tokens) and Illegal Char Error, and will pass in the character as details, 
        # the position start and for the end position - just the current position
        return [], IllegalCharError(pos_start, self.pos, "'" + char + "'")

    # add the final token of end of file
    tokens.append(Token(TT_EOF, pos_start=self.pos))
    return tokens, None


  # function that creates a number: integer or float token
  def make_number(self):
    # we need to keep the track of the number in string form, and count the numbers of dots in the number (max 1) 
    num_str = ''
    dot_count = 0
    pos_start = self.pos.copy()

    # while the current character is not None, and the current character is still a digit or a dot
    while self.current_char != None and self.current_char in DIGITS + '.':
      if self.current_char == '.':
        # if the current character is a dot, we increment its counter (max 1, then break) 
        if dot_count == 1: break
        dot_count += 1
      # and add it to the number string, and advance to the next current character
      num_str += self.current_char
      self.advance()

    # if there are no dots in the number then 
    if dot_count == 0:
      # return a new token of type int to the list of tokens by converting it into an integer (integer number)
      return Token(TT_INT, int(num_str), pos_start, self.pos)
    else:
      # otherwise return a new token of type float to the list of tokens by converting it into an float (float number)
      return Token(TT_FLOAT, float(num_str), pos_start, self.pos)


  # method to create a string 
  def make_string(self):
    string = ''
    pos_start = self.pos.copy()
    escape_character = False
    self.advance()

    escape_characters = {
      'n': '\n',
      't': '\t'
    }

    while self.current_char != None and (self.current_char != '"' or escape_character):
      if escape_character:
        string += escape_characters.get(self.current_char, self.current_char)
      else:
        if self.current_char == '\\':
          escape_character = True
        else:
          string += self.current_char
      self.advance()
      escape_character = False
    
    self.advance()
    return Token(TT_STRING, string, pos_start, self.pos)


  # method to crete an identifier
  def make_identifier(self):
    id_str = ''
    pos_start = self.pos.copy()

    while self.current_char != None and self.current_char in LETTERS_DIGITS + '_':
      id_str += self.current_char
      self.advance()

    tok_type = TT_KEYWORD if id_str in KEYWORDS else TT_IDENTIFIER
    return Token(tok_type, id_str, pos_start, self.pos)


  # method to make minus arrow 
  def make_minus_or_arrow(self):
    tok_type = TT_MINUS
    pos_start = self.pos.copy()
    self.advance()

    if self.current_char == '>':
      self.advance()
      tok_type = TT_ARROW

    return Token(tok_type, pos_start=pos_start, pos_end=self.pos)


  # method to create a != sign
  def make_not_equals(self):
    pos_start = self.pos.copy()
    self.advance()

    if self.current_char == '=':
      self.advance()
      return Token(TT_NE, pos_start=pos_start, pos_end=self.pos), None

    self.advance()
    return None, ExpectedCharError(pos_start, self.pos, "'=' (after '!')")
  

  # method to create a == sign
  def make_equals(self):
    tok_type = TT_EQ
    pos_start = self.pos.copy()
    self.advance()

    if self.current_char == '=':
      self.advance()
      tok_type = TT_EE

    return Token(tok_type, pos_start=pos_start, pos_end=self.pos)


  # method to create a < sign
  def make_less_than(self):
    tok_type = TT_LT
    pos_start = self.pos.copy()
    self.advance()

    if self.current_char == '=':
      self.advance()
      tok_type = TT_LTE

    return Token(tok_type, pos_start=pos_start, pos_end=self.pos)


  # method to create a > sign
  def make_greater_than(self):
    tok_type = TT_GT
    pos_start = self.pos.copy()
    self.advance()

    if self.current_char == '=':
      self.advance()
      tok_type = TT_GTE

    return Token(tok_type, pos_start=pos_start, pos_end=self.pos)


  # method to skip a created comment, when we find a # sign 
  def skip_comment(self):
    self.advance()

    while self.current_char != '\n':
      self.advance()

    self.advance()



####################################### NODES #######################################

# Number node is going to take in the corresponding number token
# so, that could be either: integer or float token 
class NumberNode:
  def __init__(self, tok):
    self.tok = tok

    self.pos_start = self.tok.pos_start
    self.pos_end = self.tok.pos_end


  # function for custom representation, that returns the token in a string
  def __repr__(self):
    return f'{self.tok}'


# class for the string node
# String node is going to take in the corresponding string token
class StringNode:
  def __init__(self, tok):
    self.tok = tok

    self.pos_start = self.tok.pos_start
    self.pos_end = self.tok.pos_end


  # function for custom representation, that returns the token in a string
  def __repr__(self):
    return f'{self.tok}'


# class for the list node
# List node is going to take in the corresponding element nodes
class ListNode:
  def __init__(self, element_nodes, pos_start, pos_end):
    self.element_nodes = element_nodes

    self.pos_start = pos_start
    self.pos_end = pos_end


# class for the variable access node
# Variable access node is going to take in the corresponding token name
class VarAccessNode:
  def __init__(self, var_name_tok):
    self.var_name_tok = var_name_tok

    self.pos_start = self.var_name_tok.pos_start
    self.pos_end = self.var_name_tok.pos_end


# class for the variable assign node
# Variable assign node is going to take in the corresponding token name and its value
class VarAssignNode:
  def __init__(self, var_name_tok, value_node):
    self.var_name_tok = var_name_tok
    self.value_node = value_node

    self.pos_start = self.var_name_tok.pos_start
    self.pos_end = self.value_node.pos_end


# Binary operation node for + - * / 
class BinOpNode:
  # function to take in the left node, the operation taken and teh right node
  def __init__(self, left_node, op_tok, right_node):
    self.left_node = left_node
    self.op_tok = op_tok
    self.right_node = right_node

    self.pos_start = self.left_node.pos_start
    self.pos_end = self.right_node.pos_end


  # function for custom representation of the operation: _____ + - * / _____
  def __repr__(self):
    return f'({self.left_node}, {self.op_tok}, {self.right_node})'


# class for the unary operation node (for -- = +)
# Unary operation node is going to take in the corresponding token operation and the node
class UnaryOpNode:
  def __init__(self, op_tok, node):
    self.op_tok = op_tok
    self.node = node

    self.pos_start = self.op_tok.pos_start
    self.pos_end = node.pos_end

  # function for custom representation, that returns the token in a string
  def __repr__(self):
    return f'({self.op_tok}, {self.node})'


# class for the if statement node 
# If statement node is going to take in the corresponding cases and the else cases as well
class IfNode:
  def __init__(self, cases, else_case):
    self.cases = cases
    self.else_case = else_case

    self.pos_start = self.cases[0][0].pos_start
    self.pos_end = (self.else_case or self.cases[len(self.cases) - 1])[0].pos_end


# class for the for statement node 
# For statement node is going to take in the corresponding token name, its value, end value, the increment value, bbody node and the null return 
class ForNode:
  def __init__(self, var_name_tok, start_value_node, end_value_node, increment_value_node, body_node, should_return_null):
    self.var_name_tok = var_name_tok
    self.start_value_node = start_value_node
    self.end_value_node = end_value_node
    self.increment_value_node = increment_value_node
    self.body_node = body_node
    self.should_return_null = should_return_null

    self.pos_start = self.var_name_tok.pos_start
    self.pos_end = self.body_node.pos_end


# class for the while statement node 
# While statement node is going to take in the corresponding condition node, body node and the null return 
class WhileNode:
  def __init__(self, condition_node, body_node, should_return_null):
    self.condition_node = condition_node
    self.body_node = body_node
    self.should_return_null = should_return_null

    self.pos_start = self.condition_node.pos_start
    self.pos_end = self.body_node.pos_end


# class for the function declaration node 
# Function declaration node is going to take in the corresponding token name, the token names of the arguments, body node and the return
class FuncDefNode:
  def __init__(self, var_name_tok, arg_name_toks, body_node, should_auto_return):
    self.var_name_tok = var_name_tok
    self.arg_name_toks = arg_name_toks
    self.body_node = body_node
    self.should_auto_return = should_auto_return

    if self.var_name_tok:
      self.pos_start = self.var_name_tok.pos_start
    elif len(self.arg_name_toks) > 0:
      self.pos_start = self.arg_name_toks[0].pos_start
    else:
      self.pos_start = self.body_node.pos_start

    self.pos_end = self.body_node.pos_end


# class for the function call node 
# Function call node is going to take in the corresponding node call and the token nodes of the arguments
class CallNode:
  def __init__(self, node_to_call, arg_nodes):
    self.node_to_call = node_to_call
    self.arg_nodes = arg_nodes

    self.pos_start = self.node_to_call.pos_start

    if len(self.arg_nodes) > 0:
      self.pos_end = self.arg_nodes[len(self.arg_nodes) - 1].pos_end
    else:
      self.pos_end = self.node_to_call.pos_end


# class for the return statement node 
# Return statement node is going to take in the corresponding node to return, the start position and end one
class ReturnNode:
  def __init__(self, node_to_return, pos_start, pos_end):
    self.node_to_return = node_to_return

    self.pos_start = pos_start
    self.pos_end = pos_end


# class for the continue statement node 
# Continue statement node is going to take in the corresponding the start position and end one
class ContinueNode:
  def __init__(self, pos_start, pos_end):
    self.pos_start = pos_start
    self.pos_end = pos_end


# class for the continue statement node 
# Continue statement node is going to take in the corresponding the start position and end one
class BreakNode:
  def __init__(self, pos_start, pos_end):
    self.pos_start = pos_start
    self.pos_end = pos_end



####################################### PARSE RESULT #######################################

# class to check if there is any error
class ParseResult:
  # function to keep track of an error 
  def __init__(self):
    # if there is going to be any error and its also going to keep track of the node, so this class will have some methods   
    self.error = None
    self.node = None
    self.last_registered_advance_count = 0
    self.advance_count = 0
    self.to_reverse_count = 0

  def register_advancement(self):
    self.last_registered_advance_count = 1
    self.advance_count += 1

  
  # function to take an either another parse result or a node
  def register(self, res):
    self.last_registered_advance_count = res.advance_count
    self.advance_count += res.advance_count
    # if that result has an error, then we will set our error to that error
    if res.error: self.error = res.error
    # and then we will extract the node and return it
    return res.node

  def try_register(self, res):
    if res.error:
      self.to_reverse_count = res.advance_count
      return None
    return self.register(res)


  # method to take in the node and assign the node to that node 
  def success(self, node):
    self.node = node
    return self


  # method to take in an error instead
  def failure(self, error):
    # if there is no error or the last registered advance count is equal with 0
    if not self.error or self.last_registered_advance_count == 0:
      # then set the self error to the error
      self.error = error
    return self

####################################### PARSER #######################################

class Parser:
  # function to take in a list of tokens 
  def __init__(self, tokens):
    self.tokens = tokens
    # the parser will have to keep track of the current token index (as in the lexer), and will need an advance method
    self.tok_idx = -1
    self.advance()


  # function for the advance to the next current token
  def advance(self):
    # we will increase the token index by 1, we update the current token and return it
    self.tok_idx += 1
    self.update_current_tok()
    return self.current_tok

  def reverse(self, amount=1):
    self.tok_idx -= amount
    self.update_current_tok()
    return self.current_tok


  # function for the update of the current token
  def update_current_tok(self):
    # if that token index is in range of the tokens, 
    # then we can grab the current token as the token at that token index 
    if self.tok_idx >= 0 and self.tok_idx < len(self.tokens):
      self.current_tok = self.tokens[self.tok_idx]


  # function 
  def parse(self):
    res = self.statements()
    # if there was no error, but the current token type is not equal to the end of the file 
    if not res.error and self.current_tok.type != TT_EOF:
      # we can return response failure and we can pass in an error
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        "Token cannot appear after previous tokens"
      ))
    return res

  ################################### 
  # RULES #

  # function responsible for: NEWLINE* statement (NEWLINE+ statement)* NEWLINE*
  def statements(self):
    res = ParseResult()
    statements = []
    pos_start = self.current_tok.pos_start.copy()

    # while the current token type is a newline, we register an advancement and advance
    while self.current_tok.type == TT_NEWLINE:
      res.register_advancement()
      self.advance()

    statement = res.register(self.statement())
    if res.error: return res
    statements.append(statement)

    more_statements = True

    while True:
      newline_count = 0
      while self.current_tok.type == TT_NEWLINE:
        res.register_advancement()
        self.advance()
        newline_count += 1
      if newline_count == 0:
        more_statements = False
      
      if not more_statements: break
      statement = res.try_register(self.statement())
      if not statement:
        self.reverse(res.to_reverse_count)
        more_statements = False
        continue
      statements.append(statement)

    return res.success(ListNode(
      statements,
      pos_start,
      self.current_tok.pos_end.copy()
    ))


  # function responsible for: KEYWORD:RETURN expr?, KEYWORD:CONTINUE, KEYWORD:BREAK, expr
  def statement(self):
    res = ParseResult()
    # we copy the start position of the current token
    pos_start = self.current_tok.pos_start.copy()

    # if the current token type is a return statement, we register an advancement and advance
    if self.current_tok.matches(TT_KEYWORD, 'RETURN'):
      res.register_advancement()
      self.advance()

      expr = res.try_register(self.expr())
      if not expr:
        self.reverse(res.to_reverse_count)
      return res.success(ReturnNode(expr, pos_start, self.current_tok.pos_start.copy()))
    
    # if the current token type is a continue statement, we register an advancement and advance
    if self.current_tok.matches(TT_KEYWORD, 'CONTINUE'):
      res.register_advancement()
      self.advance()
      return res.success(ContinueNode(pos_start, self.current_tok.pos_start.copy()))

    # if the current token type is a break statement, we register an advancement and advance  
    if self.current_tok.matches(TT_KEYWORD, 'BREAK'):
      res.register_advancement()
      self.advance()
      return res.success(BreakNode(pos_start, self.current_tok.pos_start.copy()))

    expr = res.register(self.expr())
    if res.error:
      return res.failure(InvalidSyntaxError(
        # we can return response failure and we can pass in an error
        self.current_tok.pos_start, self.current_tok.pos_end,
        "Expected 'RETURN', 'CONTINUE', 'BREAK', 'VAR', 'IF', 'FOR', 'WHILE', 'FUNCTION', int, float, identifier, '+', '-', '(', '[' or 'NOT'"
      ))
    return res.success(expr)


  # function responsible for: KEYWORD:VAR IDENTIFIER EQ expr, comp-expr ((KEYWORD:AND|KEYWORD:OR) comp-expr)*
  def expr(self):
    res = ParseResult()

    # if the current token type is a var statement, we register an advancement and advance
    if self.current_tok.matches(TT_KEYWORD, 'VAR'):
      res.register_advancement()
      self.advance()

      # if the current token type is not an identifier
      if self.current_tok.type != TT_IDENTIFIER:
        # we can return response failure and we can pass in an error
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          "Expected identifier"
        ))

      var_name = self.current_tok
      res.register_advancement()
      self.advance()

      # if the current token type is not an equal sign
      if self.current_tok.type != TT_EQ:
        # we can return response failure and we can pass in an error
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          "Expected '='"
        ))

      res.register_advancement()
      self.advance()
      expr = res.register(self.expr())
      if res.error: return res
      return res.success(VarAssignNode(var_name, expr))

    node = res.register(self.bin_op(self.comp_expr, ((TT_KEYWORD, 'AND'), (TT_KEYWORD, 'OR'))))

    if res.error:
      return res.failure(InvalidSyntaxError(
        # we can return response failure and we can pass in an error
        self.current_tok.pos_start, self.current_tok.pos_end,
        "Expected 'VAR', 'IF', 'FOR', 'WHILE', 'FUNCTION', int, float, identifier, '+', '-', '(', '[' or 'NOT'"
      ))

    return res.success(node)


  # function responsible for: NOT comp-expr, arith-expr ((EE|LT|GT|LTE|GTE) arith-expr)*
  def comp_expr(self):
    res = ParseResult()

    # if the current token type is a break statement, we register an advancement and advance
    if self.current_tok.matches(TT_KEYWORD, 'NOT'):
      op_tok = self.current_tok
      res.register_advancement()
      self.advance()

      node = res.register(self.comp_expr())
      if res.error: return res
      return res.success(UnaryOpNode(op_tok, node))
    
    node = res.register(self.bin_op(self.arith_expr, (TT_EE, TT_NE, TT_LT, TT_GT, TT_LTE, TT_GTE)))
    
    if res.error:
      return res.failure(InvalidSyntaxError(
        # we can return response failure and we can pass in an error
        self.current_tok.pos_start, self.current_tok.pos_end,
        "Expected int, float, identifier, '+', '-', '(', '[', 'IF', 'FOR', 'WHILE', 'FUNCTION' or 'NOT'"
      ))

    return res.success(node)


  # function for: term ((PLUS|MINUS) term)*
  # and returns the binary operation + - , similar to the term function
  def arith_expr(self):
    return self.bin_op(self.term, (TT_PLUS, TT_MINUS))


  # function for: factor ((MUL|DIV) factor)*
  # it returns the binary operation * / 
  def term(self):
    return self.bin_op(self.factor, (TT_MUL, TT_DIV))


  # function for: (PLUS|MINUS) factor, power
  # and returns a number node of that token
  def factor(self):
    # we will create a parse result instance at each start of each method 
    # every time we call advance or another method we are going to wrap it in response register
    # so, we are wrapping this advance call inside register 
    res = ParseResult()
    tok = self.current_tok

    if tok.type in (TT_PLUS, TT_MINUS):
      res.register_advancement()
      self.advance()
      factor = res.register(self.factor())
      if res.error: return res
      return res.success(UnaryOpNode(tok, factor))

    return self.power()


  # function responsible for: call (POW factor)*
  def power(self):
    return self.bin_op(self.call, (TT_POW, ), self.factor)


  # function responsible for: atom (LPAREN (expr (COMMA expr)*)? RPAREN)?
  def call(self):
    res = ParseResult()
    atom = res.register(self.atom())
    if res.error: return res

    if self.current_tok.type == TT_LPAREN:
      res.register_advancement()
      self.advance()
      arg_nodes = []

      if self.current_tok.type == TT_RPAREN:
        res.register_advancement()
        self.advance()
      else:
        arg_nodes.append(res.register(self.expr()))
        if res.error:
          return res.failure(InvalidSyntaxError(
            # we can return response failure and we can pass in an error
            self.current_tok.pos_start, self.current_tok.pos_end,
            "Expected ')', 'VAR', 'IF', 'FOR', 'WHILE', 'FUNCTION', int, float, identifier, '+', '-', '(', '[' or 'NOT'"
          ))

        while self.current_tok.type == TT_COMMA:
          res.register_advancement()
          self.advance()

          arg_nodes.append(res.register(self.expr()))
          if res.error: return res

        if self.current_tok.type != TT_RPAREN:
          return res.failure(InvalidSyntaxError(
            # we can return response failure and we can pass in an error
            self.current_tok.pos_start, self.current_tok.pos_end,
            f"Expected ',' or ')'"
          ))

        res.register_advancement()
        self.advance()
      return res.success(CallNode(atom, arg_nodes))
    return res.success(atom)


  # function for: INT|FLOAT|STRING|IDENTIFIER, LPAREN expr RPAREN, list, if, for and while expresions, function declaration
  # and returns a number, string, identifier etc node of that token 
  def atom(self):
    # we will create a parse result instance at each start of each method 
    # every time we call advance or another method we are going to wrap it in response register
    # so, we are wrapping this advance call inside register 
    # we will get the current token, and check if that token is a: 
    res = ParseResult()
    tok = self.current_tok

    # integer or float 
    if tok.type in (TT_INT, TT_FLOAT):
      res.register_advancement()
      # if yes, then we can advance and return a number token of tha token
      self.advance()
      return res.success(NumberNode(tok))

    # string
    elif tok.type == TT_STRING:
      res.register_advancement()
      # if yes, then we can advance and return a string token of tha token
      self.advance()
      return res.success(StringNode(tok))

    # identifier
    elif tok.type == TT_IDENTIFIER:
      res.register_advancement()
      # if yes, then we can advance and return a var access node token of tha token
      self.advance()
      return res.success(VarAccessNode(tok))

    # left parenthesis
    elif tok.type == TT_LPAREN:
      res.register_advancement()
      self.advance()
      expr = res.register(self.expr())
      if res.error: return res
      # right parenthesis
      if self.current_tok.type == TT_RPAREN:
        res.register_advancement()
        self.advance()
        return res.success(expr)
      else:
        # if we don't come across an entry ), we can return response failure
        # and we can pass in an error 
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          "Expected ')'"
        ))

    # left sqaure
    elif tok.type == TT_LSQUARE:
      list_expr = res.register(self.list_expr())
      if res.error: return res
      return res.success(list_expr)
    
    # if the token matches the if statement
    elif tok.matches(TT_KEYWORD, 'IF'):
      if_expr = res.register(self.if_expr())
      if res.error: return res
      return res.success(if_expr)

    # if the token matches the for statement
    elif tok.matches(TT_KEYWORD, 'FOR'):
      for_expr = res.register(self.for_expr())
      if res.error: return res
      return res.success(for_expr)

    # if the token matches the while statement
    elif tok.matches(TT_KEYWORD, 'WHILE'):
      while_expr = res.register(self.while_expr())
      if res.error: return res
      return res.success(while_expr)

    # if the token matches the function statement
    elif tok.matches(TT_KEYWORD, 'FUNCTION'):
      func_def = res.register(self.func_def())
      if res.error: return res
      return res.success(func_def)

    return res.failure(InvalidSyntaxError(
      # we can return response failure and we can pass in an error
      tok.pos_start, tok.pos_end,
      "Expected int, float, identifier, '+', '-', '(', '[', IF', 'FOR', 'WHILE', 'FUNCTION'"
    ))

  # function responsible for: LSQUARE (expr (COMMA expr)*)? RSQUARE
  def list_expr(self):
    res = ParseResult()
    element_nodes = []
    pos_start = self.current_tok.pos_start.copy()

    if self.current_tok.type != TT_LSQUARE:
      # we can return response failure and we can pass in an error
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Expected '['"
      ))

    res.register_advancement()
    self.advance()

    if self.current_tok.type == TT_RSQUARE:
      res.register_advancement()
      self.advance()
    else:
      element_nodes.append(res.register(self.expr()))
      if res.error:
        # we can return response failure and we can pass in an error
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          "Expected ']', 'VAR', 'IF', 'FOR', 'WHILE', 'FUNCTION', int, float, identifier, '+', '-', '(', '[' or 'NOT'"
        ))

      while self.current_tok.type == TT_COMMA:
        res.register_advancement()
        self.advance()

        element_nodes.append(res.register(self.expr()))
        if res.error: return res

      if self.current_tok.type != TT_RSQUARE:
        # we can return response failure and we can pass in an error
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          f"Expected ',' or ']'"
        ))

      res.register_advancement()
      self.advance()

    return res.success(ListNode(
      element_nodes,
      pos_start,
      self.current_tok.pos_end.copy()
    ))


  # function responsible for: KEYWORD:IF expr KEYWORD:THEN, (statement if-expr-b|if-expr-c?), (NEWLINE statements KEYWORD:END|if-expr-b|if-expr-c)
  def if_expr(self):
    res = ParseResult()
    all_cases = res.register(self.if_expr_cases('IF'))
    if res.error: return res
    cases, else_case = all_cases
    return res.success(IfNode(cases, else_case))

  # function responsible for: KEYWORD:ELIF expr KEYWORD:THEN, (statement if-expr-b|if-expr-c?), (NEWLINE statements KEYWORD:END|if-expr-b|if-expr-c)
  def if_expr_b(self):
    return self.if_expr_cases('ELIF')
    
  # function responsible for: KEYWORD:ELSE, statement, (NEWLINE statements KEYWORD:END)
  def if_expr_c(self):
    res = ParseResult()
    else_case = None

    if self.current_tok.matches(TT_KEYWORD, 'ELSE'):
      res.register_advancement()
      self.advance()

      if self.current_tok.type == TT_NEWLINE:
        res.register_advancement()
        self.advance()

        statements = res.register(self.statements())
        if res.error: return res
        else_case = (statements, True)

        if self.current_tok.matches(TT_KEYWORD, 'END'):
          res.register_advancement()
          self.advance()
        else:
          # we can return response failure and we can pass in an error
          return res.failure(InvalidSyntaxError(
            self.current_tok.pos_start, self.current_tok.pos_end,
            "Expected 'END'"
          ))
      else:
        expr = res.register(self.statement())
        if res.error: return res
        else_case = (expr, False)

    return res.success(else_case)


  # function responsible for: if-expr-b or if-expr-c
  def if_expr_b_or_c(self):
    res = ParseResult()
    cases, else_case = [], None

    if self.current_tok.matches(TT_KEYWORD, 'ELIF'):
      all_cases = res.register(self.if_expr_b())
      if res.error: return res
      cases, else_case = all_cases
    else:
      else_case = res.register(self.if_expr_c())
      if res.error: return res
    
    return res.success((cases, else_case))


  # function responsible for the presense of cases
  def if_expr_cases(self, case_keyword):
    res = ParseResult()
    cases = []
    else_case = None

    if not self.current_tok.matches(TT_KEYWORD, case_keyword):
      # we can return response failure and we can pass in an error
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Expected '{case_keyword}'"
      ))

    res.register_advancement()
    self.advance()

    condition = res.register(self.expr())
    if res.error: return res

    if not self.current_tok.matches(TT_KEYWORD, 'THEN'):
      # we can return response failure and we can pass in an error
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Expected 'THEN'"
      ))

    res.register_advancement()
    self.advance()

    if self.current_tok.type == TT_NEWLINE:
      res.register_advancement()
      self.advance()

      statements = res.register(self.statements())
      if res.error: return res
      cases.append((condition, statements, True))

      if self.current_tok.matches(TT_KEYWORD, 'END'):
        res.register_advancement()
        self.advance()
      else:
        all_cases = res.register(self.if_expr_b_or_c())
        if res.error: return res
        new_cases, else_case = all_cases
        cases.extend(new_cases)
    else:
      expr = res.register(self.statement())
      if res.error: return res
      cases.append((condition, expr, False))

      all_cases = res.register(self.if_expr_b_or_c())
      if res.error: return res
      new_cases, else_case = all_cases
      cases.extend(new_cases)

    return res.success((cases, else_case))


  # function responsible for: KEYWORD:FOR IDENTIFIER EQ expr KEYWORD:TO expr, (KEYWORD:INCREMENT expr)? KEYWORD:THEN, statement, (NEWLINE statements KEYWORD:END)
  def for_expr(self):
    res = ParseResult()

    if not self.current_tok.matches(TT_KEYWORD, 'FOR'):
      # we can return response failure and we can pass in an error
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Expected 'FOR'"
      ))

    res.register_advancement()
    self.advance()

    if self.current_tok.type != TT_IDENTIFIER:
      # we can return response failure and we can pass in an error
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Expected identifier"
      ))

    var_name = self.current_tok
    res.register_advancement()
    self.advance()

    if self.current_tok.type != TT_EQ:
      # we can return response failure and we can pass in an error
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Expected '='"
      ))
    
    res.register_advancement()
    self.advance()

    start_value = res.register(self.expr())
    if res.error: return res

    if not self.current_tok.matches(TT_KEYWORD, 'TO'):
      # we can return response failure and we can pass in an error
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Expected 'TO'"
      ))
    
    res.register_advancement()
    self.advance()

    end_value = res.register(self.expr())
    if res.error: return res

    if self.current_tok.matches(TT_KEYWORD, 'INCREMENT'):
      res.register_advancement()
      self.advance()

      step_value = res.register(self.expr())
      if res.error: return res
    else:
      step_value = None

    if not self.current_tok.matches(TT_KEYWORD, 'THEN'):
      # we can return response failure and we can pass in an error
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Expected 'THEN'"
      ))

    res.register_advancement()
    self.advance()

    if self.current_tok.type == TT_NEWLINE:
      res.register_advancement()
      self.advance()

      body = res.register(self.statements())
      if res.error: return res

      if not self.current_tok.matches(TT_KEYWORD, 'END'):
        # we can return response failure and we can pass in an error
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          f"Expected 'END'"
        ))

      res.register_advancement()
      self.advance()

      return res.success(ForNode(var_name, start_value, end_value, step_value, body, True))
    
    body = res.register(self.statement())
    if res.error: return res

    return res.success(ForNode(var_name, start_value, end_value, step_value, body, False))


  # function responsible for: KEYWORD:WHILE expr KEYWORD:THEN, statement, (NEWLINE statements KEYWORD:END)
  def while_expr(self):
    res = ParseResult()

    if not self.current_tok.matches(TT_KEYWORD, 'WHILE'):
      # we can return response failure and we can pass in an error
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Expected 'WHILE'"
      ))

    res.register_advancement()
    self.advance()

    condition = res.register(self.expr())
    if res.error: return res

    if not self.current_tok.matches(TT_KEYWORD, 'THEN'):
      # we can return response failure and we can pass in an error
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Expected 'THEN'"
      ))

    res.register_advancement()
    self.advance()

    if self.current_tok.type == TT_NEWLINE:
      res.register_advancement()
      self.advance()

      body = res.register(self.statements())
      if res.error: return res

      if not self.current_tok.matches(TT_KEYWORD, 'END'):
        # we can return response failure and we can pass in an error
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          f"Expected 'END'"
        ))

      res.register_advancement()
      self.advance()

      return res.success(WhileNode(condition, body, True))
    
    body = res.register(self.statement())
    if res.error: return res

    return res.success(WhileNode(condition, body, False))


  # function responsible for: KEYWORD:FUNCTION IDENTIFIER?, LPAREN (IDENTIFIER (COMMA IDENTIFIER)*)? RPAREN, (ARROW expr), (NEWLINE statements KEYWORD:END)
  def func_def(self):
    res = ParseResult()

    if not self.current_tok.matches(TT_KEYWORD, 'FUNCTION'):
      # we can return response failure and we can pass in an error
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Expected 'FUNCTION'"
      ))

    res.register_advancement()
    self.advance()

    if self.current_tok.type == TT_IDENTIFIER:
      var_name_tok = self.current_tok
      res.register_advancement()
      self.advance()
      if self.current_tok.type != TT_LPAREN:
        # we can return response failure and we can pass in an error
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          f"Expected '('"
        ))
    else:
      var_name_tok = None
      if self.current_tok.type != TT_LPAREN:
        # we can return response failure and we can pass in an error
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          f"Expected identifier or '('"
        ))
    
    res.register_advancement()
    self.advance()
    arg_name_toks = []

    if self.current_tok.type == TT_IDENTIFIER:
      arg_name_toks.append(self.current_tok)
      res.register_advancement()
      self.advance()
      
      while self.current_tok.type == TT_COMMA:
        res.register_advancement()
        self.advance()

        if self.current_tok.type != TT_IDENTIFIER:
          # we can return response failure and we can pass in an error
          return res.failure(InvalidSyntaxError(
            self.current_tok.pos_start, self.current_tok.pos_end,
            f"Expected identifier"
          ))

        arg_name_toks.append(self.current_tok)
        res.register_advancement()
        self.advance()
      
      if self.current_tok.type != TT_RPAREN:
        # we can return response failure and we can pass in an error
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          f"Expected ',' or ')'"
        ))
    else:
      if self.current_tok.type != TT_RPAREN:
        # we can return response failure and we can pass in an error
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_start, self.current_tok.pos_end,
          f"Expected identifier or ')'"
        ))

    res.register_advancement()
    self.advance()

    if self.current_tok.type == TT_ARROW:
      res.register_advancement()
      self.advance()

      body = res.register(self.expr())
      if res.error: return res

      return res.success(FuncDefNode(
        var_name_tok,
        arg_name_toks,
        body,
        True
      ))
    
    if self.current_tok.type != TT_NEWLINE:
      # we can return response failure and we can pass in an error
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Expected '->' or NEWLINE"
      ))

    res.register_advancement()
    self.advance()

    body = res.register(self.statements())
    if res.error: return res

    if not self.current_tok.matches(TT_KEYWORD, 'END'):
      # we can return response failure and we can pass in an error
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_start, self.current_tok.pos_end,
        f"Expected 'END'"
      ))

    res.register_advancement()
    self.advance()
    
    return res.success(FuncDefNode(
      var_name_tok,
      arg_name_toks,
      body,
      False
    ))

  ###################################


  # function for the binary operation * / (for term), + - (for arith_expr)
  def bin_op(self, func_a, ops, func_b=None):
    if func_b == None:
      func_b = func_a
    
    # we are going to create a result, that is a new parse result 
    # and we are going to wrap its call inside register
    res = ParseResult()
    # we will get the left factor
    # the register will take in the parse result the call to function func_a
    # and its going to take out the node from that andreturn it
    # that means that left is getting assigned to only the node and not the entire parse result
    left = res.register(func_a())
    # if there is an error, then we can just return out of the function
    if res.error: return res

    # while the current token type is the operation (MUL or DIV for term) (PLUS or MINUS for arith_expr) 
    while self.current_tok.type in ops or (self.current_tok.type, self.current_tok.value) in ops:
      # then we grab the token
      op_tok = self.current_tok
      res.register_advancement()
      self.advance()
      # and then grab another factor
      right = res.register(func_b())
      if res.error: return res
      # we will create a binary operation node, where we pass in the left factor, the operation token and the right factor
      # _____ * / _____ (for term)
      # _____ + - _____ (for arith_expr)
      left = BinOpNode(left, op_tok, right)

    # then we return the left factor, which is now the binary operation node, because we reassigned this
    return res.success(left)

#######################################
# RUNTIME RESULT
#######################################

class RTResult:
  # reset everything related
  def __init__(self):
    self.reset()

  def reset(self):
    self.value = None
    self.error = None
    self.func_return_value = None
    self.loop_should_continue = False
    self.loop_should_break = False

  def register(self, res):
    self.error = res.error
    self.func_return_value = res.func_return_value
    self.loop_should_continue = res.loop_should_continue
    self.loop_should_break = res.loop_should_break
    return res.value

  def success(self, value):
    self.reset()
    self.value = value
    return self

  def success_return(self, value):
    self.reset()
    self.func_return_value = value
    return self
  
  def success_continue(self):
    self.reset()
    self.loop_should_continue = True
    return self

  def success_break(self):
    self.reset()
    self.loop_should_break = True
    return self

  def failure(self, error):
    self.reset()
    self.error = error
    return self

  def should_return(self):
    # this will allow us to continue and break outside the current function
    return (
      self.error or
      self.func_return_value or
      self.loop_should_continue or
      self.loop_should_break
    )

####################################### VALUES #######################################

class Value:
  def __init__(self):
    self.set_pos()
    self.set_context()

  def set_pos(self, pos_start=None, pos_end=None):
    self.pos_start = pos_start
    self.pos_end = pos_end
    return self

  def set_context(self, context=None):
    self.context = context
    return self

  def added_to(self, other):
    return None, self.illegal_operation(other)

  def subbed_by(self, other):
    return None, self.illegal_operation(other)

  def multed_by(self, other):
    return None, self.illegal_operation(other)

  def dived_by(self, other):
    return None, self.illegal_operation(other)

  def powed_by(self, other):
    return None, self.illegal_operation(other)

  def get_comparison_eq(self, other):
    return None, self.illegal_operation(other)

  def get_comparison_ne(self, other):
    return None, self.illegal_operation(other)

  def get_comparison_lt(self, other):
    return None, self.illegal_operation(other)

  def get_comparison_gt(self, other):
    return None, self.illegal_operation(other)

  def get_comparison_lte(self, other):
    return None, self.illegal_operation(other)

  def get_comparison_gte(self, other):
    return None, self.illegal_operation(other)

  def anded_by(self, other):
    return None, self.illegal_operation(other)

  def ored_by(self, other):
    return None, self.illegal_operation(other)

  def notted(self, other):
    return None, self.illegal_operation(other)

  def execute(self, args):
    return RTResult().failure(self.illegal_operation())

  def copy(self):
    raise Exception('No copy method defined')

  def is_true(self):
    return False

  def illegal_operation(self, other=None):
    if not other: other = self
    return RTError(
      self.pos_start, other.pos_end,
      'Illegal operation',
      self.context
    )


# class for the acctual calaculations
class Number(Value):
  def __init__(self, value):
    super().__init__()
    self.value = value


  # function for the + operation
  def added_to(self, other):
    if isinstance(other, Number):
      return Number(self.value + other.value).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)


  # function for the - operation
  def subbed_by(self, other):
    if isinstance(other, Number):
      return Number(self.value - other.value).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)


  # function for the * operation
  def multed_by(self, other):
    if isinstance(other, Number):
      return Number(self.value * other.value).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  # function for the / operation, but not by 0 
  def dived_by(self, other):
    if isinstance(other, Number):
      if other.value == 0:
        return None, RTError(
          other.pos_start, other.pos_end,
          'Division by zero',
          self.context
        )

      return Number(self.value / other.value).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  
  # function for the ^ operation
  def powed_by(self, other):
    if isinstance(other, Number):
      return Number(self.value ** other.value).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)


  # function for the == operation
  def get_comparison_eq(self, other):
    if isinstance(other, Number):
      return Number(int(self.value == other.value)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)


  # function for the != operation
  def get_comparison_ne(self, other):
    if isinstance(other, Number):
      return Number(int(self.value != other.value)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)


  # function for the < operation
  def get_comparison_lt(self, other):
    if isinstance(other, Number):
      return Number(int(self.value < other.value)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)


  # function for the > operation
  def get_comparison_gt(self, other):
    if isinstance(other, Number):
      return Number(int(self.value > other.value)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)


  # function for the <= operation
  def get_comparison_lte(self, other):
    if isinstance(other, Number):
      return Number(int(self.value <= other.value)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)


  # function for the >= operation
  def get_comparison_gte(self, other):
    if isinstance(other, Number):
      return Number(int(self.value >= other.value)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)


  # function for the and operation
  def anded_by(self, other):
    if isinstance(other, Number):
      return Number(int(self.value and other.value)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)


  # function for the or operation
  def ored_by(self, other):
    if isinstance(other, Number):
      return Number(int(self.value or other.value)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)


  # function for the 0 or 1 operation
  def notted(self):
    return Number(1 if self.value == 0 else 0).set_context(self.context), None


  # function for the copy of the value, start and end position, and context
  def copy(self):
    copy = Number(self.value)
    copy.set_pos(self.pos_start, self.pos_end)
    copy.set_context(self.context)
    return copy


  # function for the true determination operation
  def is_true(self):
    return self.value != 0

  def __str__(self):
    return str(self.value)
  
  def __repr__(self):
    return str(self.value)


# value establishment for the null, false as 0, true as 1, and pi number as it is in math
Number.null = Number(0)
Number.false = Number(0)
Number.true = Number(1)
Number.math_PI = Number(math.pi)


# class string for the string representation of the operations
class String(Value):
  def __init__(self, value):
    super().__init__()
    self.value = value


  # function for the + operation
  def added_to(self, other):
    if isinstance(other, String):
      return String(self.value + other.value).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)


  # function for the * operation
  def multed_by(self, other):
    if isinstance(other, Number):
      return String(self.value * other.value).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  # function for the leght greater than 0 operation (value is present)
  def is_true(self):
    return len(self.value) > 0


  # function for the copy of the string value, start and end position, and context
  def copy(self):
    copy = String(self.value)
    copy.set_pos(self.pos_start, self.pos_end)
    copy.set_context(self.context)
    return copy

  def __str__(self):
    return self.value


  # function for custome representation of the value
  def __repr__(self):
    return f'"{self.value}"'


# class for the list creation
class List(Value):
  def __init__(self, elements):
    super().__init__()
    self.elements = elements


  # method to add elements in a list
  def added_to(self, other):
    new_list = self.copy()
    new_list.elements.append(other)
    return new_list, None

  # method to remove elements in a list
  def subbed_by(self, other):
    if isinstance(other, Number):
      new_list = self.copy()
      try:
        new_list.elements.pop(other.value)
        return new_list, None
      except:
        return None, RTError(
          other.pos_start, other.pos_end,
          'Element at this index could not be removed from list because index is out of bounds',
          self.context
        )
    else:
      return None, Value.illegal_operation(self, other)

  def multed_by(self, other):
    if isinstance(other, List):
      new_list = self.copy()
      new_list.elements.extend(other.elements)
      return new_list, None
    else:
      return None, Value.illegal_operation(self, other)

  def dived_by(self, other):
    if isinstance(other, Number):
      try:
        return self.elements[other.value], None
      except:
        return None, RTError(
          other.pos_start, other.pos_end,
          'Element at this index could not be retrieved from list because index is out of bounds',
          self.context
        )
    else:
      return None, Value.illegal_operation(self, other)
  

  # function for the copy of the list elemnets, start and end position, and context
  def copy(self):
    copy = List(self.elements)
    copy.set_pos(self.pos_start, self.pos_end)
    copy.set_context(self.context)
    return copy

  def __str__(self):
    return ", ".join([str(x) for x in self.elements])


  # function for custome representation of the list elements
  def __repr__(self):
    return f'[{", ".join([repr(x) for x in self.elements])}]'

class BaseFunction(Value):
  def __init__(self, name):
    super().__init__()
    # FUNCTION (f) -> 8 * f
    self.name = name or "<anonymous>"

  def generate_new_context(self):
    new_context = Context(self.name, self.context, self.pos_start)
    new_context.symbol_table = SymbolTable(new_context.parent.symbol_table)
    return new_context

  def check_args(self, arg_names, args):
    res = RTResult()

    if len(args) > len(arg_names):
      return res.failure(RTError(
        self.pos_start, self.pos_end,
        f"{len(args) - len(arg_names)} too many args passed into {self}",
        self.context
      ))
    
    if len(args) < len(arg_names):
      return res.failure(RTError(
        self.pos_start, self.pos_end,
        f"{len(arg_names) - len(args)} too few args passed into {self}",
        self.context
      ))

    return res.success(None)

  def populate_args(self, arg_names, args, exec_ctx):
    for i in range(len(args)):
      arg_name = arg_names[i]
      arg_value = args[i]
      arg_value.set_context(exec_ctx)
      exec_ctx.symbol_table.set(arg_name, arg_value)

  def check_and_populate_args(self, arg_names, args, exec_ctx):
    res = RTResult()
    res.register(self.check_args(arg_names, args))
    if res.should_return(): return res
    self.populate_args(arg_names, args, exec_ctx)
    return res.success(None)

class Function(BaseFunction):
  def __init__(self, name, body_node, arg_names, should_auto_return):
    super().__init__(name)
    self.body_node = body_node
    self.arg_names = arg_names
    self.should_auto_return = should_auto_return

  def execute(self, args):
    res = RTResult()
    interpreter = Interpreter()
    exec_ctx = self.generate_new_context()

    res.register(self.check_and_populate_args(self.arg_names, args, exec_ctx))
    if res.should_return(): return res

    value = res.register(interpreter.visit(self.body_node, exec_ctx))
    if res.should_return() and res.func_return_value == None: return res

    ret_value = (value if self.should_auto_return else None) or res.func_return_value or Number.null
    return res.success(ret_value)

  def copy(self):
    copy = Function(self.name, self.body_node, self.arg_names, self.should_auto_return)
    copy.set_context(self.context)
    copy.set_pos(self.pos_start, self.pos_end)
    return copy

  def __repr__(self):
    return f"<function {self.name}>"

class BuiltInFunction(BaseFunction):
  def __init__(self, name):
    super().__init__(name)

  def execute(self, args):
    res = RTResult()
    exec_ctx = self.generate_new_context()

    method_name = f'execute_{self.name}'
    method = getattr(self, method_name, self.no_visit_method)

    res.register(self.check_and_populate_args(method.arg_names, args, exec_ctx))
    if res.should_return(): return res

    return_value = res.register(method(exec_ctx))
    if res.should_return(): return res
    return res.success(return_value)
  
  def no_visit_method(self, node, context):
    raise Exception(f'No execute_{self.name} method defined')

  def copy(self):
    copy = BuiltInFunction(self.name)
    copy.set_context(self.context)
    copy.set_pos(self.pos_start, self.pos_end)
    return copy

  def __repr__(self):
    return f"<built-in function {self.name}>"

  #####################################

  def execute_print(self, exec_ctx):
    print(str(exec_ctx.symbol_table.get('value')))
    return RTResult().success(Number.null)
  execute_print.arg_names = ['value']
  
  def execute_print_ret(self, exec_ctx):
    return RTResult().success(String(str(exec_ctx.symbol_table.get('value'))))
  execute_print_ret.arg_names = ['value']
  
  def execute_input(self, exec_ctx):
    text = input()
    return RTResult().success(String(text))
  execute_input.arg_names = []

  def execute_input_int(self, exec_ctx):
    while True:
      text = input()
      try:
        number = int(text)
        break
      except ValueError:
        print(f"'{text}' must be an integer. Try again!")
    return RTResult().success(Number(number))
  execute_input_int.arg_names = []

  def execute_clear(self, exec_ctx):
    os.system('cls' if os.name == 'nt' else 'cls') 
    return RTResult().success(Number.null)
  execute_clear.arg_names = []

  def execute_is_number(self, exec_ctx):
    is_number = isinstance(exec_ctx.symbol_table.get("value"), Number)
    return RTResult().success(Number.true if is_number else Number.false)
  execute_is_number.arg_names = ["value"]

  def execute_is_string(self, exec_ctx):
    is_number = isinstance(exec_ctx.symbol_table.get("value"), String)
    return RTResult().success(Number.true if is_number else Number.false)
  execute_is_string.arg_names = ["value"]

  def execute_is_list(self, exec_ctx):
    is_number = isinstance(exec_ctx.symbol_table.get("value"), List)
    return RTResult().success(Number.true if is_number else Number.false)
  execute_is_list.arg_names = ["value"]

  def execute_is_function(self, exec_ctx):
    is_number = isinstance(exec_ctx.symbol_table.get("value"), BaseFunction)
    return RTResult().success(Number.true if is_number else Number.false)
  execute_is_function.arg_names = ["value"]

  def execute_append(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")
    value = exec_ctx.symbol_table.get("value")

    if not isinstance(list_, List):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "First argument must be list",
        exec_ctx
      ))

    list_.elements.append(value)
    return RTResult().success(Number.null)
  execute_append.arg_names = ["list", "value"]

  def execute_pop(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")
    index = exec_ctx.symbol_table.get("index")

    if not isinstance(list_, List):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "First argument must be list",
        exec_ctx
      ))

    if not isinstance(index, Number):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Second argument must be number",
        exec_ctx
      ))

    try:
      element = list_.elements.pop(index.value)
    except:
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        'Element at this index could not be removed from list because index is out of bounds',
        exec_ctx
      ))
    return RTResult().success(element)
  execute_pop.arg_names = ["list", "index"]

  def execute_extend(self, exec_ctx):
    listA = exec_ctx.symbol_table.get("listA")
    listB = exec_ctx.symbol_table.get("listB")

    if not isinstance(listA, List):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "First argument must be list",
        exec_ctx
      ))

    if not isinstance(listB, List):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Second argument must be list",
        exec_ctx
      ))

    listA.elements.extend(listB.elements)
    return RTResult().success(Number.null)
  execute_extend.arg_names = ["listA", "listB"]

  def execute_len(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")

    if not isinstance(list_, List):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Argument must be list",
        exec_ctx
      ))

    return RTResult().success(Number(len(list_.elements)))
  execute_len.arg_names = ["list"]

  def execute_run(self, exec_ctx):
    fn = exec_ctx.symbol_table.get("fn")

    if not isinstance(fn, String):
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        "Second argument must be string",
        exec_ctx
      ))

    fn = fn.value

    try:
      with open(fn, "r") as f:
        script = f.read()
    except Exception as e:
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        f"Failed to load script \"{fn}\"\n" + str(e),
        exec_ctx
      ))

    _, error = run(fn, script)
    
    if error:
      return RTResult().failure(RTError(
        self.pos_start, self.pos_end,
        f"Failed to finish executing script \"{fn}\"\n" +
        error.as_string(),
        exec_ctx
      ))

    return RTResult().success(Number.null)
  execute_run.arg_names = ["fn"]

BuiltInFunction.print       = BuiltInFunction("print")
BuiltInFunction.print_ret   = BuiltInFunction("print_ret")
BuiltInFunction.input       = BuiltInFunction("input")
BuiltInFunction.input_int   = BuiltInFunction("input_int")
BuiltInFunction.clear       = BuiltInFunction("clear")
BuiltInFunction.is_number   = BuiltInFunction("is_number")
BuiltInFunction.is_string   = BuiltInFunction("is_string")
BuiltInFunction.is_list     = BuiltInFunction("is_list")
BuiltInFunction.is_function = BuiltInFunction("is_function")
BuiltInFunction.append      = BuiltInFunction("append")
BuiltInFunction.pop         = BuiltInFunction("pop")
BuiltInFunction.extend      = BuiltInFunction("extend")
BuiltInFunction.len					= BuiltInFunction("len")
BuiltInFunction.run					= BuiltInFunction("run")

####################################### CONTEXT #######################################

class Context:
  # class to understand the name, parent and its entry position of the self
  def __init__(self, display_name, parent=None, parent_entry_pos=None):
    self.display_name = display_name
    self.parent = parent
    self.parent_entry_pos = parent_entry_pos
    self.symbol_table = None

####################################### SYMBOL TABLE #######################################

class SymbolTable:
  def __init__(self, parent=None):
    self.symbols = {}
    self.parent = parent

  def get(self, name):
    value = self.symbols.get(name, None)
    if value == None and self.parent:
      return self.parent.get(name)
    return value

  def set(self, name, value):
    self.symbols[name] = value

  def remove(self, name):
    del self.symbols[name]

####################################### INTERPRETER #######################################

class Interpreter:
  # function visit for the visit of each node in a context
  def visit(self, node, context):
    method_name = f'visit_{type(node).__name__}'
    method = getattr(self, method_name, self.no_visit_method)
    return method(node, context)

  def no_visit_method(self, node, context):
    raise Exception(f'No visit_{type(node).__name__} method defined')

  ###################################

  # function to visit and return the number value of the token
  def visit_NumberNode(self, node, context):
    return RTResult().success(
      Number(node.tok.value).set_context(context).set_pos(node.pos_start, node.pos_end)
    )


  # function to visit and return the string value of the token
  def visit_StringNode(self, node, context):
    return RTResult().success(
      String(node.tok.value).set_context(context).set_pos(node.pos_start, node.pos_end)
    )


  # function to visit and return the list nodes 
  def visit_ListNode(self, node, context):
    res = RTResult()
    elements = []

    for element_node in node.element_nodes:
      elements.append(res.register(self.visit(element_node, context)))
      if res.should_return(): return res

    return res.success(
      List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
    )


  # function to visit and return the value of the variable access node
  def visit_VarAccessNode(self, node, context):
    res = RTResult()
    var_name = node.var_name_tok.value
    value = context.symbol_table.get(var_name)

    if not value:
      return res.failure(RTError(
        node.pos_start, node.pos_end,
        f"'{var_name}' is not defined",
        context
      ))

    value = value.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
    return res.success(value)


  # function to visit and return the value of the variable assigned node
  def visit_VarAssignNode(self, node, context):
    res = RTResult()
    var_name = node.var_name_tok.value
    value = res.register(self.visit(node.value_node, context))
    if res.should_return(): return res

    context.symbol_table.set(var_name, value)
    return res.success(value)


  # function to visit and return the value of the binary operation node
  def visit_BinOpNode(self, node, context):
    res = RTResult()
    left = res.register(self.visit(node.left_node, context))
    if res.should_return(): return res
    right = res.register(self.visit(node.right_node, context))
    if res.should_return(): return res

    if node.op_tok.type == TT_PLUS:
      result, error = left.added_to(right)
    elif node.op_tok.type == TT_MINUS:
      result, error = left.subbed_by(right)
    elif node.op_tok.type == TT_MUL:
      result, error = left.multed_by(right)
    elif node.op_tok.type == TT_DIV:
      result, error = left.dived_by(right)
    elif node.op_tok.type == TT_POW:
      result, error = left.powed_by(right)
    elif node.op_tok.type == TT_EE:
      result, error = left.get_comparison_eq(right)
    elif node.op_tok.type == TT_NE:
      result, error = left.get_comparison_ne(right)
    elif node.op_tok.type == TT_LT:
      result, error = left.get_comparison_lt(right)
    elif node.op_tok.type == TT_GT:
      result, error = left.get_comparison_gt(right)
    elif node.op_tok.type == TT_LTE:
      result, error = left.get_comparison_lte(right)
    elif node.op_tok.type == TT_GTE:
      result, error = left.get_comparison_gte(right)
    elif node.op_tok.matches(TT_KEYWORD, 'AND'):
      result, error = left.anded_by(right)
    elif node.op_tok.matches(TT_KEYWORD, 'OR'):
      result, error = left.ored_by(right)

    if error:
      return res.failure(error)
    else:
      return res.success(result.set_pos(node.pos_start, node.pos_end))


  # function to visit and return the value of the unary operation node
  def visit_UnaryOpNode(self, node, context):
    res = RTResult()
    number = res.register(self.visit(node.node, context))
    if res.should_return(): return res

    error = None

    if node.op_tok.type == TT_MINUS:
      number, error = number.multed_by(Number(-1))
    elif node.op_tok.matches(TT_KEYWORD, 'NOT'):
      number, error = number.notted()

    if error:
      return res.failure(error)
    else:
      return res.success(number.set_pos(node.pos_start, node.pos_end))


  # function to visit and return the value of the if statement node
  def visit_IfNode(self, node, context):
    res = RTResult()

    for condition, expr, should_return_null in node.cases:
      condition_value = res.register(self.visit(condition, context))
      if res.should_return(): return res

      if condition_value.is_true():
        expr_value = res.register(self.visit(expr, context))
        if res.should_return(): return res
        return res.success(Number.null if should_return_null else expr_value)

    if node.else_case:
      expr, should_return_null = node.else_case
      expr_value = res.register(self.visit(expr, context))
      if res.should_return(): return res
      return res.success(Number.null if should_return_null else expr_value)

    return res.success(Number.null)


  # function to visit and return the value of the for statement node
  def visit_ForNode(self, node, context):
    res = RTResult()
    elements = []

    start_value = res.register(self.visit(node.start_value_node, context))
    if res.should_return(): return res

    end_value = res.register(self.visit(node.end_value_node, context))
    if res.should_return(): return res

    if node.increment_value_node:
      step_value = res.register(self.visit(node.increment_value_node, context))
      if res.should_return(): return res
    else:
      step_value = Number(1)

    i = start_value.value

    if step_value.value >= 0:
      condition = lambda: i < end_value.value
    else:
      condition = lambda: i > end_value.value
    
    while condition():
      context.symbol_table.set(node.var_name_tok.value, Number(i))
      i += step_value.value

      value = res.register(self.visit(node.body_node, context))
      if res.should_return() and res.loop_should_continue == False and res.loop_should_break == False: return res
      
      if res.loop_should_continue:
        continue
      
      if res.loop_should_break:
        break

      elements.append(value)

    return res.success(
      Number.null if node.should_return_null else
      List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
    )


  # function to visit and return the value of the while statement node
  def visit_WhileNode(self, node, context):
    res = RTResult()
    elements = []

    while True:
      condition = res.register(self.visit(node.condition_node, context))
      if res.should_return(): return res

      if not condition.is_true():
        break

      value = res.register(self.visit(node.body_node, context))
      if res.should_return() and res.loop_should_continue == False and res.loop_should_break == False: return res

      if res.loop_should_continue:
        continue
      
      if res.loop_should_break:
        break

      elements.append(value)

    return res.success(
      Number.null if node.should_return_null else
      List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
    )


  # function to visit and return the value of the function declaration statement node
  def visit_FuncDefNode(self, node, context):
    res = RTResult()

    func_name = node.var_name_tok.value if node.var_name_tok else None
    body_node = node.body_node
    arg_names = [arg_name.value for arg_name in node.arg_name_toks]
    func_value = Function(func_name, body_node, arg_names, node.should_auto_return).set_context(context).set_pos(node.pos_start, node.pos_end)
    
    if node.var_name_tok:
      context.symbol_table.set(func_name, func_value)

    return res.success(func_value)


  # function to visit and return the value of the function call statement node
  def visit_CallNode(self, node, context):
    res = RTResult()
    args = []

    value_to_call = res.register(self.visit(node.node_to_call, context))
    if res.should_return(): return res
    value_to_call = value_to_call.copy().set_pos(node.pos_start, node.pos_end)

    for arg_node in node.arg_nodes:
      args.append(res.register(self.visit(arg_node, context)))
      if res.should_return(): return res

    return_value = res.register(value_to_call.execute(args))
    if res.should_return(): return res
    return_value = return_value.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
    return res.success(return_value)


  # function to visit and return the value of the return statement node
  def visit_ReturnNode(self, node, context):
    res = RTResult()

    if node.node_to_return:
      value = res.register(self.visit(node.node_to_return, context))
      if res.should_return(): return res
    else:
      value = Number.null
    
    return res.success_return(value)


  # function to visit and return the value of the continue statement node
  def visit_ContinueNode(self, node, context):
    return RTResult().success_continue()


  # function to visit and return the value of the break statement node
  def visit_BreakNode(self, node, context):
    return RTResult().success_break()

####################################### RUN #######################################

global_symbol_table = SymbolTable()
global_symbol_table.set("NIL", Number.null)
global_symbol_table.set("FALSE", Number.false)
global_symbol_table.set("TRUE", Number.true)
global_symbol_table.set("MATH_PI", Number.math_PI)
global_symbol_table.set("PRINT", BuiltInFunction.print)
global_symbol_table.set("PRINT_RET", BuiltInFunction.print_ret)
global_symbol_table.set("INPUT", BuiltInFunction.input)
global_symbol_table.set("INPUT_INT", BuiltInFunction.input_int)
global_symbol_table.set("CLEAR", BuiltInFunction.clear)
global_symbol_table.set("CLS", BuiltInFunction.clear)
global_symbol_table.set("IS_NUM", BuiltInFunction.is_number)
global_symbol_table.set("IS_STR", BuiltInFunction.is_string)
global_symbol_table.set("IS_LIST", BuiltInFunction.is_list)
global_symbol_table.set("IS_FUN", BuiltInFunction.is_function)
global_symbol_table.set("APPEND", BuiltInFunction.append)
global_symbol_table.set("POP", BuiltInFunction.pop)
global_symbol_table.set("EXTEND", BuiltInFunction.extend)
global_symbol_table.set("LEN", BuiltInFunction.len)
global_symbol_table.set("RUN", BuiltInFunction.run)


# function that takes some text and runs it 
def run(fn, text):
  # Generate tokens
  # create a new lexer, where we take in a file name and pass in that text
  lexer = Lexer(fn, text)
  # take the tokens and error out of it, by making them
  tokens, error = lexer.make_tokens()
  # if there is no error then we return nothing, othrwise we return the error
  if error: return None, error
  # for instance: we will get from 1 + 2.5, something like: [INT:1, PLUS, FLOAT:2.5] 
  # for instance error: from 1 * a, something like: Illegal Character: 'a' File filename, line 1 
  
  # Generate Abstractc Syntax Tree
  # create a new parser, where we pass in the tokens
  parser = Parser(tokens)
  ast = parser.parse()
  # if there is no error then we return nothing, othrwise we return the error
  if ast.error: return None, ast.error
  # for instance: we will get from 6 + 5 * 2, something like: (INT:6, PLUS, (INT:5, MUL, INT:2))

  # Run program
  interpreter = Interpreter()
  # create a new parser
  context = Context('<program>')
  context.symbol_table = global_symbol_table
  # result is going to be the visited Abstractc Syntax Tree from the context
  result = interpreter.visit(ast.node, context)

  # just return the value of the result, and the errors as well
  return result.value, result.error