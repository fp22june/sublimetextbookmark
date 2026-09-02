import sys
import os
import traceback
import collections
import datetime
import pathlib
import shutil
import subprocess
import sublime
import sublime_plugin
import json
import bisect
import time

SIGNETVIEW_NAMEID = 'Find Results'#'🔖'
SIGNET_REGION_NAME = 'signet_region'
SIGNET_ICON = 'Packages/Theme - Default/common/label.png'
CMDAUTOOPENALL='findresultsmodopenall'
MATCHFINDRESULTVIEW='Find Results'
SESSIONSIGS = {}
FSNAME = 'sigbk'

SETTINGSD = os.path.join(sublime.packages_path(), 'User')
pathlib.Path(SETTINGSD).mkdir(parents=True, exist_ok=True)

DATAJSON=os.path.join(SETTINGSD, f'{FSNAME}.store.json')

SETTINGSF = os.path.join(f'{FSNAME}.sublime-settings')

def updateSessionsigFromViewRegions(view):
  if (  (fn:=view.file_name())
    and (w:=view.window())
    and (pf:=w.project_file_name()) # is project
    and (ps:=SESSIONSIGS.get(pf)) is not None # already has entry
    and (obs:=ps.get(fn)) is not None # already has entries
    and (rs:=sigrowlistFromViewRegions(view)) is not None # empty[] truthy
  ):
    if len(rs)==len(ps[fn]): # 1to1 ln switch
      for i,r in enumerate(rs):
        obs[i]["ln"]=r
      ps[fn]=obs
    else: # overwrite
      ps[fn]=[newsig(view,r) for r in rs]
def newsig(view,r):
  return {
    "tp": time.strftime("%Y-%m-%d %a %H:%M:%S", time.localtime()),
    'ts': int(time.time()),
    "ln": r,
    "c": view.substr(view.line(view.text_point(r, 0))),
  }
def updateViewRegionsFromSessionsig(view):
  if ( (not view.is_scratch())
    and (fn:=view.file_name())
    and (w:=view.window())
    and (pf:=w.project_file_name()) # is project
    and (ps:=SESSIONSIGS.get(pf)) is not None # already has entry
    and (obs:=ps.get(fn)) is not None # already has entries
  ):
    regions=[
        sublime.Region(pt, pt)
        for o in obs
        if (ln:=o.get("ln")) is not None
        for pt in [view.text_point(ln, 0)]  # line start
    ]
    view.erase_regions(SIGNET_REGION_NAME)
    view.add_regions(SIGNET_REGION_NAME, regions, str(sublime.load_settings(SETTINGSF).get('scope') or "region.redish"), SIGNET_ICON)

def sigrowlistFromViewRegions(view):
    lns = []
    for reg in view.get_regions(SIGNET_REGION_NAME):
        row, _ = view.rowcol(reg.a)
        lns.append(row)
    lns.sort()
    return lns

def newSessionsig(x): SESSIONSIGS[x]={}; return SESSIONSIGS[x]
def sessionsig(x): return SESSIONSIGS[x]

def updateSessionsigsFromDiskreadJson():
  global SESSIONSIGS
  if os.path.isfile(DATAJSON):
    try:
      with open(DATAJSON, 'r') as j:
        jd=json.load(j)
        SESSIONSIGS = {}
        for pf, fs in jd.items(): # if os.path.exists(pf):     #mod retain invalid
          SESSIONSIGS[pf]={}
          for fn, obs in fs.items():  # if os.path.exists(fn) and len(lines) > 0:     #mod retain invalid
            SESSIONSIGS[pf][fn]=[]
            for o in obs:
              if isinstance(o, int): # backward compatible
                SESSIONSIGS[pf][fn].append({
                  "ln": o,
                })
              elif o.get("ln") is not None:
                ao={
                  "ln": o.get("ln")
                }
                if "tp" in o: ao["tp"]=o.get("tp")
                if 'ts' in o: ao['ts']=o.get('ts')
                if "c" in o:  ao["c" ]=o.get("c")
                SESSIONSIGS[pf][fn].append(ao)
    except Exception:
      raise
    #   error(f'Error reading {DATAJSON}: {e}', e.__traceback__)
  else:
    sublime.status_message('Creating new signets file')
    SESSIONSIGS = {}
def writeJsonWithSessionsigs():
  # try:
  #   with open(DATAJSON, 'w') as fp:
  #     json.dump(SESSIONSIGS, fp, indent=4)
  # except Exception as e:
  #   error(f'Error writing {DATAJSON}: {e}', e.__traceback__)
  timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
  temp_file = f"{DATAJSON}.{timestamp}.tmp"
  try:
      with open(temp_file, 'w') as fp:
          json.dump(SESSIONSIGS, fp, indent=4)
      os.replace(temp_file, DATAJSON)
  except Exception:
      if os.path.exists(temp_file):
          pass#os.remove(temp_file)
      raise

class E20260901(sublime_plugin.EventListener):
  def on_init(self, views):
    updateSessionsigsFromDiskreadJson()
    if len(views) > 0 and views[0].window() is not None:
      for view in views:
        updateViewRegionsFromSessionsig(view)
  def on_load_project(self, window): #  Project > Open; ! Not triggered at program start even if project restored  
    for view in window.views():
      updateViewRegionsFromSessionsig(view)
  def on_load(self, view):
    updateSessionsigsFromDiskreadJson() #TODO reduce diskread
    updateViewRegionsFromSessionsig(view)
  def on_pre_close_project(self, window):
    for view in window.views():
      updateSessionsigFromViewRegions(view)
    writeJsonWithSessionsigs()
  # def on_pre_close(self, view): pass # children of on_pre_close_project()
  def on_deactivated(self, view): # lost focus
    if((fn:=view.file_name())
      and os.path.exists(fn)
    ):
      updateSessionsigFromViewRegions(view)
      writeJsonWithSessionsigs()
  def on_activated(self, view):
    if(  view.name()==MATCHFINDRESULTVIEW 
      or MATCHFINDRESULTVIEW in (view.file_name() or []) ):
      # sublime.status_message(u".") # visually replace previous 
      pass # findresultsmod plugin
    elif u'𝌆' in view.name() or u'𝌆' in (view.file_name() or []):
      # sublime.status_message(u".") # visually replace previous
      pass # symlist plugin
    else:
      rs=sigrowlistFromViewRegions(view)
      if len(rs)==0:
        updateViewRegionsFromSessionsig(view) # tab right click > Split View
        rs=sigrowlistFromViewRegions(view)
      sublime.status_message(u"🔖 {0} bookmark{1}".format(len(rs),'s' if len(rs)>1 else ''))
  #TODO
  # def on_reload(self, view):
  #     updateViewRegionsFromSessionsig(view)
  # def on_reload_async(self, view):
  #     updateViewRegionsFromSessionsig(view)
  # def on_revert(self, view):
  #     updateViewRegionsFromSessionsig(view)
  # def on_revert_async(self, view):
  #     updateViewRegionsFromSessionsig(view) 
class SbotToggleSignetCommand(sublime_plugin.TextCommand):
  def is_visible(self):
    return self.view.is_scratch() is False and self.view.file_name() is not None
  def run(self, __):
    view=self.view
    if ( (not view.is_scratch())
      and (fn:=view.file_name())
      and (w:=view.window())
      and (pf:=w.project_file_name()) # is project
      # and (ps:=SESSIONSIGS.get(pf)) is not None # already has entry
      # and (obs:=ps.get(fn)) is not None # already has entries
      and (rs:=sigrowlistFromViewRegions(view)) is not None # empty[] truthy
      and (caret:=view.sel()[0].b if len(view.sel()) == 1 else None) is not None # 0 truthy
      and (r_:=view.rowcol(caret)) # invalid input outputs (0,0), is truthy         CAUTION invalid
    ):
      updateSessionsigFromViewRegions(view)
      r,_=r_
      if r is not None:
        if r in rs: rs.remove(r)
        else:       rs.append(r)
      ps = SESSIONSIGS.get(pf) or newSessionsig(pf)
      obs=ps.get(fn) or []
      if any(o.get("ln") == r for o in obs):
        obs = [o for o in obs if o.get("ln") != r]
      else:
        obs.append(newsig(view,r))
      obs=sorted(obs, key=lambda x: x["ln"])
      ps[fn]=obs
      #
      regions=[
          sublime.Region(pt, pt)
          for o in obs
          if (ln:=o.get("ln")) is not None
          for pt in [view.text_point(ln, 0)]  # line start
      ]
      view.erase_regions(SIGNET_REGION_NAME)
      view.add_regions(SIGNET_REGION_NAME, regions, str(sublime.load_settings(SETTINGSF).get('scope') or "region.redish"), SIGNET_ICON)
      writeJsonWithSessionsigs()
class SbotGotoSignetCommand(sublime_plugin.TextCommand):
    def is_enabled(self):
        return len(sigrowlistFromViewRegions(self.view))>0
    # def is_visible(self):
    #     return len(sigrowlistFromViewRegions(self.view))>0

    def run(self, __, where):
      dnext=where=='next'
      nav_all_files=sublime.load_settings(SETTINGSF).get('nav_all_files') or False
      print(nav_all_files)
      view=self.view
      if ( (not view.is_scratch())
        and (fn:=view.file_name())
        and (w:=view.window())
        and (pf:=w.project_file_name()) # is project
        and (ps:=SESSIONSIGS.get(pf)) is not None # already has entry
        # and (obs:=ps.get(fn)) is not None # already has entries
        # and (rs:=sigrowlistFromViewRegions(view)) is not None # empty[] truthy
        and (caret:=view.sel()[0].b if len(view.sel()) == 1 else None) is not None # 0 truthy
        and (r_:=view.rowcol(caret)) # invalid input outputs (0,0), is truthy         CAUTION invalid
      ):
        sel_row,_=r_  # current selected row
        incr = +1 if dnext else -1
        array_end = 0 if dnext else -1

        done = False

        # 1) dnext: If there's another bookmark below -> goto it
        # 1) prev: If there's another bookmark above -> goto it
        if not done:
            rs=sigrowlistFromViewRegions(view)
            if not dnext:
                rs.reverse()
            for si,sr in enumerate(rs):
                if (dnext and sr > sel_row) or (not dnext and sr < sel_row):
                    view.run_command("goto_line", {"line": sr + 1})
                    done = True
                    break

            sublime.status_message(u"🔖 {0} / {1} bookmark{2}".format(si+1 if done else '1',len(rs),'s' if len(rs)>1 else ''))

            # At begin or end. Check for single file operation.
            if not done and not nav_all_files and len(rs) > 0:
                view.run_command("goto_line", {"line": rs[0] + 1})
                done = True

        # 2) dnext: Else if there's an open signet file to the right of this tab -> focus tab, goto first signet
        # 2) prev: Else if there's an open signet file to the left of this tab -> focus tab, goto last signet
        if nav_all_files and not done:
            view_index = w.get_view_index(view)[1] + incr
            while not done and ((dnext and view_index < len(w.views()) or (not dnext and view_index >= 0))):
                vv = w.views()[view_index]
                rs=sigrowlistFromViewRegions(vv)
                if len(rs) > 0:
                    w.focus_view(vv)
                    vv.run_command("goto_line", {"line": rs[array_end] + 1})
                    done = True
                else:
                    view_index += incr

        
        # def wait_load_file(window, fpath, line):
        #     '''Open file asynchronously then position at line. Returns the new View or None if failed.'''
        #     vnew = None
        #     def _load(view):
        #         if view.is_loading():
        #             sublime.set_timeout(lambda: _load(view), 10)  # maybe not forever?
        #         else:
        #             view.run_command("goto_line", {"line": line})
        #     # Open the file in a new view.
        #     try:
        #         vnew = window.open_file(fpath)
        #         _load(vnew)
        #     except Exception as e:
        #         error(f'Failed to open {fpath}: {e}', e.__traceback__)
        #         vnew = None
        #     return vnew
        # 3) dnext: Else if there is a signet file in the project that is not open -> open it, focus tab, goto first signet
        # 3) prev: Else if there is a signet file in the project that is not open -> open it, focus tab, goto last signet
        # if nav_all_files and not done:
        #     for fn, rows in ps.items():
        #         if fn is not None:
        #             if w.find_open_file(fn) is None and os.path.exists(fn) and len(rows) > 0:
        #                 vv = wait_load_file(w, fn, rows[array_end])
        #                 done = True
        #                 break

        # 4) dnext: Else -> find first tab/file with signets, focus tab, goto first signet
        # 4) prev: Else -> find last tab/file with signets, focus tab, goto last signet
        if nav_all_files and not done:
            view_index = 0 if dnext else len(w.views()) - 1
            while not done and ((dnext and view_index < len(w.views()) or (not dnext and view_index >= 0))):
                vv = w.views()[view_index]
                rs=sigrowlistFromViewRegions(vv)
                if len(rs) > 0:
                    w.focus_view(vv)
                    vv.run_command("goto_line", {"line": rs[array_end] + 1})
                    done = True
                else:
                    view_index += incr
# class SbotClearAllSignetsCommand(sublime_plugin.TextCommand):
class SbotgenlistCommand(sublime_plugin.TextCommand):
  def run(self, __):
    view=self.view
    if (   (w:=view.window())
      and (pf:=w.project_file_name()) # is project
      and (ps:=SESSIONSIGS.get(pf)) is not None # already has entry
    ):
      s=['']
      for fn in [ps for _, ps 
                  in sorted(enumerate(ps)
                            , key=lambda ef: 0 if ef[1] == view.file_name() else (999-ef[0]))]: #current view at the top, followed by lastest edits 
        fv=None
        for ov in w.views():
          ovf=ov.file_name()
          if ovf and ovf==fn:
            #sys.stdout.write(">>>> ok " +str(fn)+'\n')
            fv=ov
            # ov.substr(view.line(view.text_point(rr, 0)))
        obs=ps[fn]
        if not len(obs)>0:
          continue
        obs=sorted(obs, key=lambda x: x["ln"])
        if fv:
          s.append('{0}\n{1}:'.format(os.path.basename(fv.file_name()),fv.file_name()))
          for o in obs:
            r=o.get("ln")
            symbol_name=None
            point=fv.text_point(r,0)
            symbols=fv.symbols()
            closest_region=None
            for _, (region, name) in enumerate(symbols):
              if region.a < point:
                closest_region=region
              else:
                break
            if closest_region:
              sym_region=sublime.Region(closest_region.a, closest_region.b)
              symbol_name=fv.substr(fv.line(sym_region))
            if symbol_name:
              s.append(str(fv.rowcol(closest_region.a)[0] + 1).rjust(5)+':@'+symbol_name)

            for a in -2,-1,0,1,2:
              rr=r+a
              if 0<=rr and rr<=(fv.rowcol(fv.size())[0] + 1):
                s.append(
                  (
                    "{5}{3}\n{6}{4}\n{0}{1}{2}"
                      if a==0 and (o.get("tp") or o.get("c")) else
                    "{0}{1}{2}"
                  ).format(
                    str(rr+1).rjust(5)
                    ,':'if a==0 else ' '
                    ,fv.substr(fv.line(fv.text_point(rr, 0)))
                    ,o.get("tp") or ' '*23
                    ,o.get("c") or ''
                    ,'    ┌ '
                    ,'    │ '
                  )
                )
            s.append(' ')
        else:
          s.append('{0}\n{1}:'.format(os.path.basename(fn),fn))
          fe=os.path.exists(fn)
          for o in obs:
            s.append(
              ( (u"{4}{2}\n{5}{3}\n{0}: "
                if (o.get("tp") or o.get("c")) else 
                u"{0}: ")
                +
                (u"⚠ File not opened yet. Either "
                  "1. Double click filename to open, if this tab was created by 'Find' ; or "
                  "2. Run '{1}' to open ALL❗files. Then regen this list again."
                if fe else
                u"❗ File no longer exist."
                )
              ).format(
                str(o.get("ln")+1).rjust(5)
                ,CMDAUTOOPENALL
                ,o.get("tp") or ' '*23
                ,o.get("c") or ''
                ,'    ┌ '
                ,'    │ '
              )
            )
        s.append(' ')

      view_open=False
      for vs in w.views():
          if SIGNETVIEW_NAMEID in vs.name():
            view_open=True
            v=vs
      if not view_open:
        v=w.new_file()
        v.set_name(SIGNETVIEW_NAMEID)
      v.set_scratch(True)
      v.settings().set('line_numbers', False)
      v.settings().set('word_wrap', False)
      # v.settings().set('fold_buttons', False)
      # v.settings().set('highlight_line', False)
      v.settings().set('margin', 0)
      #https://forum.sublimetext.com/t/set-layout-reference/5713
      # w.set_layout({
      #   "cols"  : [0.0, 0.7, 1.0],
      #   "rows"  : [0.0, 1.0],
      #   "cells" : [[0, 0, 1, 1], [1, 0, 2, 1]]
      # })
      w.set_view_index(v, 1, 0)
      v.run_command('sbotshowlist', {'x': s})
    else:
      sublime.status_message(u"🔖 no project bookmarks yet.")
class SbotshowlistCommand(sublime_plugin.TextCommand): #run_command('sbotshowlist', {'x':
  def run(self, edit, x=None):
    if(   (w:=self.view.window())
      and (f:=w.project_file_name())
      and (p:=os.path.split(f))
      and (s:=p[1].replace('.sublime-project', ''))
    ):
      #self.view.erase(edit, sublime.Region(0, self.view.size()))
      self.view.insert(edit, self.view.size(), "{1}Listing bookmarks for {0}\n".format(s,"\n\n"if self.view.size()>0 else''))
      self.view.insert(edit, self.view.size(), "\n".join(x))
class SbotrequestsymlistbookmarkrowsCommand(sublime_plugin.TextCommand): #expose symlist
  def run(self, edit, x=[]):
    if len(x)>0:
      v=sigrowlistFromViewRegions(self.view)
      # sys.stdout.write('x '+str(x)+'\n')
      # sys.stdout.write('v '+str(v)+'\n')
      if v:
        indices = []
        for val in v:
            idx = bisect.bisect_right(x, val) - 1
            indices.append(idx)
        r=list(dict.fromkeys(indices))
        #sys.stdout.write('r '+str(r)+'\n')
        if len(r)>0: self.view.run_command('symlistrequestlisthighlightcallback', {'x': r})
class SbothighlightsymlistrowsCommand(sublime_plugin.TextCommand): #expose symlist
  def run(self, edit, x=[]):
    if len(x)>0:
      # sys.stdout.write('x '+str(x)+'\n')
      regions=[]
      for r in x:
          pt = self.view.text_point(r, 0)  # line start
          regions.append(sublime.Region(pt, pt))
      self.view.add_regions('symlistrowsig', regions, 'region.redish', 'Packages/Theme - Default/common/label.png')



class SbotopenjsonCommand(sublime_plugin.TextCommand):  #run_command('sbotopenjson', 
  def run(self, edit):
    if os.path.isfile(DATAJSON):
      self.view.window().open_file(DATAJSON)