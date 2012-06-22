#!/usr/bin/env python
# vim: set ts=2 sw=2:

import sqlite3

class Db:
  CURRENT_DB_VERSION = 1

  # Everything is ready to go
  STATUS_OK = "OK"
  # Old version of the db.  No more actions possible.
  # (Maybe some day we'll support upgrades)
  STATUS_OLD_VERSION = "OLD_VERSION"
  # The database is ok, but it's new.  Must call init()
  STATUS_NEW = "NEW"

  def __init__(self, filename):
    self.conn = sqlite3.connect(filename)
    self.status = Db.STATUS_OK

    c = self.conn.cursor()
    try:
      c.execute("SELECT db_version, username, password FROM Info")
      info = c.fetchall()[0]
      if info[0] != Db.CURRENT_DB_VERSION:
        self.status = Db.STATUS_OLD_VERSION
        return # bail
      self.username = info[1]
      self.password = info[2]
    except sqlite3.OperationalError:
      # Need initialization
      self.conn.execute("""CREATE TABLE Info (
            db_version INETGER,
            username TEXT,
            password TEXT
        )""")
      self.conn.execute("""CREATE TABLE CommandHistory (
            id INTEGER,
            command TEXT
        )""")
      self.conn.execute("""INSERT INTO Info(db_version) VALUES(%d)"""
          % (Db.CURRENT_DB_VERSION))
      self.conn.commit()
      self.status = Db.STATUS_NEW
    finally:
      c.close()

  def init(self, username, password):
    if self.status != Db.STATUS_OK and self.status != Db.STATUS_NEW:
      raise Exception("Database is not initialized.  Status: %s" % self.status)
    c = self.conn.cursor()
    try:
      c.execute("UPDATE Info SET username=?, password=?", (username, password))
      self.conn.commit()
      self.status = Db.STATUS_OK
      self.username = username
      self.password = password
    finally:
      c.close()

  def assert_ok(self):
    if self.status != Db.STATUS_OK:
      raise Exception("Database status is %s" % self.status)

  def close(self):
    if self.status != Db.STATUS_OK and self.status != Db.STATUS_NEW:
      raise Exception("Database status is %s" % self.status)
    self.conn.close()

  def save_history(self, history):
    self.assert_ok()
    self.conn.execute("DELETE FROM CommandHistory")
    for i in range(0,len(history)):
      self.conn.execute("INSERT INTO CommandHistory(id,command) VALUES(?,?)", (i, history[i]))
    self.conn.commit()

  def load_history(self):
    return [row[0] for row
        in self.conn.execute("SELECT command FROM CommandHistory ORDER BY id ASC")]

def test():
  db = Db("test.dg")
  print "db.status=%s" % db.status
  if db.status == Db.STATUS_NEW:
    db.init("testuser", "testpasswd")
    print "did init"
  if db.status != Db.STATUS_OK:
    print "bailing"
    return
  db.save_history(["asdf","hi","mom"])
  print db.load_history()

if __name__ == "__main__":
  test()

