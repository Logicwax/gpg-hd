
class Field(object):
  def __init__(self, cmdline, gui_label, tip):
    self.cmdline = cmdline
    self.gui_label = gui_label
    self.tip = tip
    self.value = None

  def validate(self, newval):
    return True

  def generate_widget(): pass

class StringField(Field):
  def generate_widget(self):
    entry = Gtk.Entry()
    entry.set_tooltip_markup(self.tip)
    def handle(*args):
      text = entry.get_text()
      if self.validate(text):
        self.value = text
    entry.connect('changed', handle)
    return entry

#Incomplete
class ReStringField(StringField):
  def validate(self, newval):
    pass

class UIntField(Field):
  def validate(self, newval):
    return newval.isdigit()

  def generate_widget(self):
    entry = Gtk.SpinButton()
    entry.set_tooltip_markup(self.tip)
    entry.set_numeric(True)
    entry.set_adjustment(Gtk.Adjustment(0, 0, sys.maxint, 1, 100, 0))
    entry.set_update_policy(Gtk.SpinButtonUpdatePolicy.IF_VALID)
    def handle(*args):
      print entry.get_value_as_int()
      self.value = entry.get_value_as_int()
    entry.connect('value-changed', handle)
    return entry


class Return(dict):
  """ Usage: ret = Return("Descriptive string <a href="replace">link text</a>")
             # descriptive string is parsed as markup for Gtk.Label
             ret['replace'] = ...
             ret['var'] = ...
  """
  def __init__(self, string):
    dict.__init__(self)
    self.string = string

  def generate_widget(self):
    ret = Gtk.Label()
    ret.set_markup(self.string)
    ret.set_justify(Gtk.Justification.LEFT)
    ret.set_selectable(True)
    ret.props.halign = Gtk.Align.START
    ret.props.xalign = 0
    ret.set_line_wrap(True)
    ret.connect('activate-link', self.link_handler)

    return ret

  def link_handler(self, label, uri):
    try:
      self[uri].handle()
    except:
      raise
    return True # link handled

class RetExecLink(object):
  def __init__(self, command, terminal=False):
    self.command = command
    self.terminal = terminal

  def handle(self):
    import os
    if self.terminal:
      os.system('xterm -e %s' % self.command)
    else:
      os.system(self.command)

class Plugin(object):
  def __init__(self, title, description):
    self.title = title
    self.description = description
    self.fields = [StringField('so', 'Foo Var:', 'a tip')]

  def doit(self, seed): pass

  def valid(self): return True

