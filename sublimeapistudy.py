import sublime
import sublime_plugin
import sys
import os
import traceback
import datetime
LOGF = os.path.join(sublime.packages_path(), 'sublimeapistudy_log.txt')
if not os.path.exists(LOGF): open(LOGF, 'w').close()
viewhint=0

# Get-Content -Path .\sublimeapistudy_log.txt -Tail 10 -Wait

def log(message, tb=None):
    # if LOGF == INVALID_FN:
    #     raise RuntimeError('Logger has not been initialized.')
    if len(message) == 0:
        return
    if len(message) == 1 and message[0] == '\n':
        return
    frame = sys._getframe(2)
    fn = os.path.basename(frame.f_code.co_filename)
    line = frame.f_lineno
    # f'func = {frame.f_code.co_name}'
    # f'mod_name = {frame.f_globals["__name__"]}'
    # f'class_name = {frame.f_locals["self"].__class__.__name__}'
    time_str = str(datetime.datetime.now())[:-3]
    # Write the record. No need to be synchronized across multiple sbot plugins
    # as ST docs say that API runs on a single thread.
    with open(LOGF, 'a') as log:
        out_line = "{0} {1}:{2} {3}".format(time_str, fn, str(line).ljust(4), message)
        log.write(out_line + '\n')
        if tb is not None:
            # The traceback formatter is a bit ugly - clean it up.
            tblines = []
            for s in traceback.format_tb(tb):
                if len(s) > 0:
                    tblines.append(s[:-1])
            stb = '\n'.join(tblines)
            log.write(stb + '\n')
        log.flush()
def debugprint(x=None):
  global viewhint
  x=sys._getframe().f_back.f_code.co_name.ljust(15)+' '+(x or '')
  sys.stdout.write(x+"\n")
  m=['-',' '][viewhint%2]
  log(m*viewhint+str(viewhint%10)+m*(20-viewhint)+' ' + x); 
  viewhint+=1
  if viewhint>=20: viewhint=0 
  pass
class DCommand(sublime_plugin.TextCommand): #run_command('d',{'x':
  def run(self, edit, x=''):
    debugprint(x)

class E20260831(sublime_plugin.EventListener):
  def on_text_command(self, view, command_name, args):
    if command_name == "undo":
      debugprint("undo")
      return None
#   def on_init(self, views):
#     print(str(self))
#     file_path = self.views[0].file_name() # cannot get py folder
#     folder_path = os.path.dirname(file_path)
#     folder_name = os.path.basename(folder_path)
#     print("SIGSTUDY Folder Path:"+folder_path)
class E1Command(sublime_plugin.TextCommand): #run_command('e1')
  def run(self, edit):
    self.view.add_regions('R', [self.view.sel()[0]], "region.orangish", 'Packages/Theme - Default/common/label.png')
class StudyEvent(sublime_plugin.EventListener):
    def on_init(self, views):
      debugprint()
    #     for view in views:
    #         debugprint(view.file_name())
    def on_load_project(self, window):
        debugprint()
        debugprint(self.view.window().project_file_name())
        # for view in window.views():
    def on_pre_close_project(self, window):
        debugprint()
        debugprint(self.view.window().project_file_name())
    def on_load(self, view):
        debugprint(view.file_name())
    def on_pre_close(self, view):
        debugprint(view.file_name())
    def on_deactivated(self, view):
        debugprint(view.file_name())
    def on_activated(self, view):
        debugprint(view.file_name())
        # debugprint('attrtest '+str(getattr(view, "_my_plugin_initialized", False)))
        # if not getattr(view, "_my_plugin_initialized", False):
        #     view._my_plugin_initialized = True
        # debugprint('attrtest '+str(getattr(view, "_my_plugin_initialized", False)))

        # debugprint('attrtest '+str(view.settings().get("_my_plugin_initialized",False)))
        # view.settings().set("_my_plugin_initialized",True)
        # debugprint('attrtest '+str(view.settings().get("_my_plugin_initialized",False)))
    def on_reload(self, view):
        debugprint(view.file_name())
    def on_reload_async(self, view):
        debugprint(view.file_name())
    def on_revert(self, view):
        debugprint(view.file_name())
    def on_revert_async(self, view):
        debugprint(view.file_name())
    def on_post_save(self, view):
        debugprint(view.file_name())
