#!/usr/bin/env python
# vim: set ts=2 sw=2:

import re

import shellparse

IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

class Error:
  def __init__(self, message):
    self.message = message
  def __str__(self):
    return self.message


class Command:
  def run(self):
    print self
  def flatten(self):
    print str(self)


class Help(Command):
  NAME = "help"
  SHORTHELP = "Shows this help message."
  LONGHELP = """
    help          Show the list of commands
    help COMMAND  Show the help for COMMAND
  """

  def __init__(self, words):
    if len(words) == 1:
      self.command = None
    elif len(words) == 2:
      self.command = words[1]
    else:
      raise Error("malformed help command")
    assert_identifier(self.command)

  def __str__(self):
    return "Help command=%s" % self.command

  def flatten(self):
    if self.command:
      return "help %s" % self.command
    else:
      return "help"

  def run(self):
    if self.command:
      cmd = choose_command(self.command)
      if cmd:
        print "    " + cmd.SHORTHELP
        print cmd.LONGHELP
      else:
        raise Error("Not a command: %s" % self.command)
    else:
      print "Commands:"
      maxlen = 0
      for cmd in COMMANDS:
        if len(cmd.NAME) > maxlen:
          maxlen = len(cmd.NAME)
      fmt = "    {0:<%d}    {1}" % (maxlen)
      for cmd in COMMANDS:
        print fmt.format(cmd.NAME, cmd.SHORTHELP)


class Print(Command):
  NAME = "print"
  SHORTHELP = "Prints the value of an expression."
  LONGHELP = """
  """

  def __init__(self, words):
    # See if it's an expression
    self.val,index = parse_value(words[1:], None)

  def __str__(self):
    return "Print %s" % (self.val)

  def flatten(self):
    return "print %s" % (self.val.flatten())


class Reload(Command):
  NAME = "reload"
  SHORTHELP = "Reloads the game data from the web."
  LONGHELP = """
  """

  def __init__(self, words):
    pass

  def __str__(self):
    return "Reload"

  def flatten(self):
    return "reload"


class Save(Command):
  NAME = "save"
  SHORTHELP = "Creates a saved query"
  LONGHELP = """
  """

  def __init__(self, words):
    # var
    try:
      self.var = words[1]
    except IndexError as ex:
      raise Error("set command malformed: missing variable name")
    # =
    if words[2] != '=':
      raise Error("set command malformed: missing '='")
    # value
    self.query,index = parse_value(words[3:], None)

  def __str__(self):
    return "Save %s = %s" % (self.var, self.query)

  def flatten(self):
    return "save %s = %s" % (self.var, self.query.flatten())


class Set(Command):
  NAME = "set"
  SHORTHELP = "Sets a variable value."
  LONGHELP = """
  """

  def __init__(self, words):
    # var
    try:
      self.var = words[1]
    except IndexError as ex:
      raise Error("set command malformed: missing variable name")
    # =
    if words[2] != '=':
      raise Error("set command malformed: missing '='")
    # value
    self.val,index = parse_value(words[3:], None)

  def __str__(self):
    return "Set %s = %s" % (self.var, self.val)

  def flatten(self):
    return "set %s = %s" % (self.var, self.val.flatten())


class Show(Command):
  NAME = "show"
  SHORTHELP = "Shows the command for a saved query."
  LONGHELP = """
  """

  def __init__(self, words):
    # var
    try:
      self.var = words[1]
    except IndexError as ex:
      raise Error("show command malformed: missing variable name")

  def __str__(self):
    return "Show %s" % (self.var)

  def flatten(self):
    return "show %s" % self.var


class FleetExpression:
  def __init__(self, types):
    self.queries = []
    self.types = set(types)

  def __str__(self):
    return "Fleets(types=%s queries=%s)" % (self.types, self.queries)

  def flatten(self):
    result = ""
    result = result + " ".join(self.types)
    for q in self.queries:
      if q[0] == "within":
        result = result + " within %s of %s" % (q[1], flatten_string(q[2]))
      else:
        result = result + " %s %s" % (q[0], flatten_string(q[1]))
    return result


class PlanetExpression:
  def __init__(self):
    self.queries = []

  def __str__(self):
    return "Planets(queries=%s)" % (self.queries)

  def flatten(self):
    result = "planets"
    for q in self.queries:
      if q[0] == "within":
        result = result + " within %s of %s" % (q[1], flatten_string(q[2]))
      else:
        result = result + " %s %s" % (q[0], flatten_string(q[1]))
    return result



def flatten_string(text):
  if IDENTIFIER_RE.match(text):
    return text
  else:
    return "\"" + text + "\""


# Parses out a fleet, planet or route expression.  If termiator is provided,
# parsing will stop if that word is encountered.
# Returns a tuple of
#   0: FleetExpression or PlanetExpression expressed in words
#   1: The next position in words at which parsing should continue
# Raises Error if there is an error
def parse_value(words, terminator):
  try:
    types,index = parse_fleet_names(words)
    if len(types) > 0:
      return parse_fleets(words, terminator)
    if words[0] == "planets":
      return parse_planets(words[1:], terminator)
    if len(words) == 1:
      return (words[0],1)
    raise Error("Expected fleets, planets or routes")
  except IndexError as ex:
    raise Error("IndexError")

def assert_identifier(text):
  if not IDENTIFIER_RE.match(text):
    raise Error("Expecting identifier. Found: %s" % text)

FLEET_NAMES = {
  "arc": "arc",
  "arcs": "arc",
  "merchantman": "merchantmen",
  "merchantmen": "merchantmen",
}

def normalize_fleet_name(word):
  if FLEET_NAMES.has_key(word):
    return FLEET_NAMES[word]
  else:
    return None

def parse_fleet_names(words):
  if words[0] == "fleets":
    return (["fleets"],1)
  index = 0
  result = []
  while index < len(words):
    name = normalize_fleet_name(words[index])
    if name:
      result.append(name)
    else:
      break
    index = index + 1
  return result,index

def parse_fleets(words, terminator):
  types,index = parse_fleet_names(words)
  fleets = FleetExpression(types)
  while index < len(words):
    if words[index] == "within":
      distance = words[index+1]
      if words[index+2] != "of":
        raise Error("Expected 'of'")
      planet = words[index+3]
      fleets.queries.append(("within", distance, planet))
      index = index + 4
    elif words[index] == "inside":
      fleets.queries.append(("inside", words[index+1]))
      index = index + 2
    elif words[index] == "on":
      fleets.queries.append(("on", words[index+1]))
      index = index + 2
    elif words[index] == "id":
      fleets.queries.append(("id", words[index+1]))
      index = index + 2
    else:
      fleets.queries.append(("id", words[index]))
      index = index + 1
  return (fleets, index)

def parse_planets(words, terminator):
  index = 0
  fleets = PlanetExpression()
  while index < len(words):
    if words[index] == "within":
      distance = words[index+1]
      if words[index+2] != "of":
        raise Error("Expected 'of'")
      planet = words[index+3]
      fleets.queries.append(("within", distance, planet))
      index = index + 4
    elif words[index] == "inside":
      fleets.queries.append(("inside", words[index+1]))
      index = index + 2
    elif words[index] == "id":
      fleets.queries.append(("id", words[index+1]))
      index = index + 2
    else:
      fleets.queries.append(("id", words[index]))
      index = index + 1
  return (fleets, index)

COMMANDS = (
    Help,
    Print,
    Reload,
    Save,
    Set,
    Show,
  )

def choose_command(word):
  for cmd in COMMANDS:
    if cmd.NAME == word:
      return cmd
  return None

def parse_text(text):
  return parse_list(shellparse.split(text))

def parse_list(words):
  cmd = choose_command(words[0])
  if cmd:
    return cmd(words)
  else:
    raise Error("Not a command: %s" % words[0])

def test():
  def check(text):
    cmd = parse_text(text)
    print cmd

  check("reload")
  check("set x = fleets inside 'routename' within 4.2 of mom on routey")
  check("set x = fleets")
  check("set x = arc arcs")
  check("set x = arcs merchantmen inside 'routename' within 4.2 of mom on routey")
  check("set x = asdf")
  check("save x = arcs merchantmen inside 'routename' more within 4.2 of mom on routey 1234 'a b'")
  check("save x = planets inside 'routename' more within 4.2 of mom 1234 'a b'")
  check("show x")
  check("help")
  check("help show")

if __name__ == "__main__":
  test()

