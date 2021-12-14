"""The token kinds currently recognized."""


from musicode.tokens import TokenKind

keyword_kinds = []
symbol_kinds = []

note_kw = TokenKind("note", keyword_kinds)
chord_kw = TokenKind("chord", keyword_kinds)
piece_kw = TokenKind("piece", keyword_kinds)
setting_kw = TokenKind("setting", keyword_kinds)


play_kw = TokenKind("play", keyword_kinds)
print_kw = TokenKind("print", keyword_kinds)
score_kw = TokenKind("score", keyword_kinds)
while_kw = TokenKind("while", keyword_kinds)
case_kw = TokenKind("case", keyword_kinds)
if_kw = TokenKind("if", keyword_kinds)
else_kw = TokenKind("else", keyword_kinds)
break_kw = TokenKind("break", keyword_kinds)
continue_kw = TokenKind("continue", keyword_kinds)

plus = TokenKind("+", symbol_kinds)
minus = TokenKind("-", symbol_kinds)
star = TokenKind("*", symbol_kinds)
slash = TokenKind("/", symbol_kinds)
mod = TokenKind("%", symbol_kinds)
at = TokenKind("@", symbol_kinds)

incr = TokenKind("++", symbol_kinds)
decr = TokenKind("--", symbol_kinds)
equals = TokenKind("=", symbol_kinds)
plusequals = TokenKind("+=", symbol_kinds)
minusequals = TokenKind("-=", symbol_kinds)
starequals = TokenKind("*=", symbol_kinds)
divequals = TokenKind("/=", symbol_kinds)
modequals = TokenKind("%=", symbol_kinds)
twoequals = TokenKind("==", symbol_kinds)
notequal = TokenKind("!=", symbol_kinds)
bool_and = TokenKind("&&", symbol_kinds)
bool_or = TokenKind("||", symbol_kinds)
bool_not = TokenKind("!", symbol_kinds)
lt = TokenKind("<", symbol_kinds)
gt = TokenKind(">", symbol_kinds)
ltoe = TokenKind("<=", symbol_kinds)
gtoe = TokenKind(">=", symbol_kinds)
amp = TokenKind("&", symbol_kinds)
pound = TokenKind("#", symbol_kinds)
bar = TokenKind("|", symbol_kinds)

lbitshift = TokenKind("<<", symbol_kinds)
rbitshift = TokenKind(">>", symbol_kinds)
compl = TokenKind("~", symbol_kinds)

dquote = TokenKind('"', symbol_kinds)
squote = TokenKind("'", symbol_kinds)

open_paren = TokenKind("(", symbol_kinds)
close_paren = TokenKind(")", symbol_kinds)
open_brack = TokenKind("{", symbol_kinds)
close_brack = TokenKind("}", symbol_kinds)
open_sq_brack = TokenKind("[", symbol_kinds)
close_sq_brack = TokenKind("]", symbol_kinds)

comma = TokenKind(",", symbol_kinds)
semicolon = TokenKind(";", symbol_kinds)
dot = TokenKind(".", symbol_kinds)
arrow = TokenKind("->", symbol_kinds)

identifier = TokenKind('identifier')
number = TokenKind('number')
string = TokenKind('string')
char_string = TokenKind('char_string')
