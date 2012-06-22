#!/usr/bin/env python

class Tokenizer:
  def __init__(self, string):
    self.string = string
    self.pos = 0
  def set(self, pos):
    self.pos = pos
  def get(self):
    s = self.string
    pos = self.pos
    l = len(s)
    while pos < l and s[pos].isspace():
      pos = pos + 1
    startpos = pos
    if pos >= l:
      return None
    start = s[pos]
    pos = pos + 1
    if start == ';':
      endpos = pos
    elif start == '"' or start == "'":
      startpos = pos
      while pos < l and s[pos] != start:
        pos = pos + 1
      endpos = pos
      pos = pos + 1
    else:
      while pos < l and not s[pos].isspace() and s[pos] != ';':
        pos = pos + 1
      endpos = pos
    self.pos = pos
    return s[startpos:endpos]

def split(string):
  tokenizer = Tokenizer(string)
  result = []
  while True:
    t = tokenizer.get()
    if t is None:
      return result
    else:
      result.append(t)

def test():
  def check_tokens(string, expected):
    actual = split(string)
    if expected != actual:
      print "FAILED: %s" % string
      print "   expected: %s" % expected
      print "   actual:   %s" % actual

  check_tokens(" 'asdf' "" \" 1234 ' jkl;\" xy;z jkl",
      ["asdf", " 1234 ' jkl;", "xy", ";", "z", "jkl"])

if __name__ == "__main__":
  test()
