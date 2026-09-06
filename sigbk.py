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
SIGNET_REGION_NAME = 'signet_region2'
SIGNET_ICON = 'Packages/Theme - Default/common/label.png'
CMDAUTOOPENALL='findresultsmodopenall'
MATCHFINDRESULTVIEW='Find Results'
SYMLISTVIEW_NAMEID=u'𝌆'
SESSIONSIGS = {}
FSNAME = 'sigbk'
SETTINGSD = os.path.join(sublime.packages_path(), 'User')
pathlib.Path(SETTINGSD).mkdir(parents=True, exist_ok=True)
DEBUGSTARTLOADDATAJSON=None #or os.path.join(SETTINGSD, f'{FSNAME}.store.sessionstartreadonly.json')
LOADDATAJSON=os.path.join(SETTINGSD, f'{FSNAME}.store.json')
WORKJSONVER='1'
SAVEDATAJSON=os.path.join(SETTINGSD, f'{FSNAME}.store.json')
SAVEJSONVER='1'
# SAVEDATAJSON=os.path.join(SETTINGSD, f'{FSNAME}.store')
# SAVEJSONVER=0
SETTINGSF = os.path.join(f'{FSNAME}.sublime-settings')
ENUMSIGSCOPE=['DATAHOT','DATAFILETIME'] #Scope0Sig, Scope1Sig
INVALIDSIG='ARCHIVE'
S1NAMETS='TIMESTAMP'
S1NAMETSLOCAL='TIMESTAMPLOCAL'
def debugprint(view,x):view.run_command('d',{'x':x}) #sublimeapistudy.py

def sigrowlistFromViewRegions(view):
    lns = []
    for reg in view.get_regions(SIGNET_REGION_NAME):
        row, _ = view.rowcol(reg.a)
        lns.append(row)
    lns.sort()
    return lns

def newSessionsigs():                 return (SESSIONSIGS:={'ver': WORKJSONVER})
def newProject(x):                    SESSIONSIGS[x]={}; return SESSIONSIGS[x]
def getProject(x):                    return SESSIONSIGS.get(x)
def newFile(p,f):                     p[f]={}; return p[f]
def getFile(p,f):                     return p.get(f) if p is not None else None
def newScopedSigsOfFile(s,p,f):       rs=getFile(p,f) or newFile(p,f); rs[s]=[]; return rs[s]      # p=getProject(str), f=view.file_name()
def getScopedSigsOfFile(s,p,f):       return rs.get(s)                 if(rs:=getFile(p,f)) is not None else None
def setScopedSigsOfFile(s,p,f,obs):   rs=getFile(p,f) or newFile(p,f); rs[s]=obs
def getScope1TSOfFile(p,f):           return rs.get(S1NAMETS)          if(rs:=getFile(p,f)) is not None else None
def setScope1TSOfFile(p,f,t):         rs=getFile(p,f) or newFile(p,f); rs[S1NAMETS]=t; rs[S1NAMETSLOCAL]=datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d %a %H:%M:%S')
def cleanScope1OfFile(p,f):           (rs:=getFile(p, f)) and (len(rs.get('DATAFILETIME')or[])==0) and (rs.pop('DATAFILETIME',None), rs.pop(S1NAMETS,None), rs.pop(S1NAMETSLOCAL,None))
def getArchiveOfFile(p,f):            return rs.get(INVALIDSIG)        if(rs:=getFile(p,f)) is not None else None
def setArchiveOfFile(p,f,obs):        rs=getFile(p,f) or newFile(p,f); rs[INVALIDSIG]=obs
def newsig(view,r):
  return {
    "tp": time.strftime("%Y-%m-%d %a %H:%M:%S", time.localtime()),
    "ts": int(time.time()),
    "ln": r,
    "c": view.substr(view.line(view.text_point(r, 0))),
  }
def timemarkarchive(view,o):
  return {**o, # is shallow copy
    "tpa":time.strftime("%Y-%m-%d %a %H:%M:%S", time.localtime()),
    "tsa":int(time.time()),
    "ca":view.substr(view.line(view.text_point(o["ln"], 0))),
  }

def updateScope0SigFromViewRegions(view):
  if (  (f:=view.file_name())
    and (w:=view.window())
    and (pf:=w.project_file_name()) # is project
    and (p:=getProject(pf)) is not None # already has entry
    and (obs:=getScopedSigsOfFile('DATAHOT',p,f)) is not None # empty[] truthy
    and (rs:=sigrowlistFromViewRegions(view)) is not None # empty[] truthy
  ):
    if len(rs)==len(obs): # 1to1 ln switch
      for i,r in enumerate(rs):
        obs[i]["ln"]=r
      setScopedSigsOfFile('DATAHOT',p,f,obs)
    else: # overwrite
      setScopedSigsOfFile('DATAHOT',p,f,[newsig(view,r) for r in rs])
def newScope1TSAndSigFromScope0Sig(p,f,view):
  if obs:=getScopedSigsOfFile('DATAHOT',p,f):
    setScopedSigsOfFile('DATAFILETIME',p,f,obs)
    setScope1TSOfFile(p,f,os.path.getmtime(view.file_name()))
    cleanScope1OfFile(p,f)
def newScope1TSAndSigAndScope0SigFromViewRegions(p,f,view):
  if(   (rs:=sigrowlistFromViewRegions(view)) is not None # empty[] truthy
  ):
    obs=[newsig(view,r) for r in rs]
    setScopedSigsOfFile('DATAHOT',p,f,obs)
    setScopedSigsOfFile('DATAFILETIME',p,f,obs)
    setScope1TSOfFile(p,f,os.path.getmtime(view.file_name()))
    cleanScope1OfFile(p,f)
def updateScope0SigFromScope1Sig(view):
  if(   (f:=view.file_name()) 
    and (w:=view.window())
    and (pf:=w.project_file_name()) # is project
    and (p:=getProject(pf)) is not None # already has entry
    # and os.path.exists(f)
    and (tf:=os.path.getmtime(view.file_name()))
    and (ts:=getScope1TSOfFile(p,f))
    and (obs:=getScopedSigsOfFile('DATAFILETIME',p,f)) is not None # empty[] truthy
  ):
    if tf==ts:
      setScopedSigsOfFile('DATAHOT',p,f,obs)
    else: # timestamp unmatch
      # vobs=[ o for o in obs 
      #       if o["c"]==view.substr(view.line(view.text_point(o["ln"], 0))) ]
      vobs=[]
      iobs=[]
      for o in obs:
        if o["c"]==view.substr(view.line(view.text_point(o["ln"], 0))):
          vobs.append(o.copy()) # 1to1 ln switch if snippets match
        else:
          iobs.append(o.copy())
      setArchiveOfFile(p,f,[timemarkarchive(view,o) for o in iobs])
      setScopedSigsOfFile('DATAHOT',p,f,vobs)
      setScopedSigsOfFile('DATAFILETIME',p,f,vobs)
      setScope1TSOfFile(p,f,os.path.getmtime(view.file_name()))
      cleanScope1OfFile(p,f)
      if len(iobs)==0:
        sublime.status_message(u"🔖 Reverted / File modification detected, all bookmarks restored and adjusted to new line numbers.")
      else:
        sublime.status_message(u"🔖 Reverted / File modification detected, {0} / {1} invalid bookmark{2} archived.".format(len(iobs),len(obs),'s' if len(iobs)>1 else ''))
      # if 0<len(iobs):
      #   debugprint(view,'{0} archived'.format(len(iobs)))
      #   [debugprint(view,y) for y in
      #     [ ('\n ln#'+str(p['ln']).ljust(4) + str(p['tp'])                                           +':'+str(p['c'])
      #       +'\n '+      '(now)'.ljust(3+4) + time.strftime("%Y-%m-%d %a %H:%M:%S", time.localtime())+':'+view.substr(view.line(view.text_point(p["ln"], 0)))
      #       ) for p in iobs ] ]
def updateViewRegionsFromScopedSig(s,view):
  if ( (not view.is_scratch())
    and (f:=view.file_name())
    and (w:=view.window())
    and (pf:=w.project_file_name()) # is project
    and (p:=getProject(pf)) is not None # already has entry
    and (obs:=getScopedSigsOfFile(s,p,f)) is not None # empty[] truthy
  ):
    regions=[
        sublime.Region(pt, pt)
        for o in obs
        if (ln:=o.get("ln")) is not None
        for pt in [view.text_point(ln, 0)]  # line start
    ]
    view.erase_regions(SIGNET_REGION_NAME)
    view.add_regions(SIGNET_REGION_NAME, regions, str(sublime.load_settings(SETTINGSF).get('scope') or "region.redish"), SIGNET_ICON)
def addViewRegionsFromScopedSig(s,pf,f,view): # partial dup of updateViewRegionsFromScopedSig(), lesser conditional for performance
  if (  (p:=getProject(pf)) is not None # already has entry
    and (obs:=getScopedSigsOfFile(s,p,f)) is not None # empty[] truthy
  ):
    regions=[
        sublime.Region(pt, pt)
        for o in obs
        if (ln:=o.get("ln")) is not None
        for pt in [view.text_point(ln, 0)]  # line start
    ]
    view.add_regions(SIGNET_REGION_NAME, regions, str(sublime.load_settings(SETTINGSF).get('scope') or "region.redish"), SIGNET_ICON)

def toggleScopedSig(s,p,f,r,view):
  obs=getScopedSigsOfFile(s,p,f) or newScopedSigsOfFile(s,p,f)
  if any(o.get("ln") == r for o in obs):
    obs = [o for o in obs if o.get("ln") != r]
  else:
    obs.append(newsig(view,r))
  obs=sorted(obs, key=lambda x: x["ln"])
  setScopedSigsOfFile(s,p,f,obs)

def updateSessionsigsFromDiskreadJson():
  global SESSIONSIGS
  SESSIONSIGS=newSessionsigs()
  if os.path.isfile(DEBUGSTARTLOADDATAJSON or LOADDATAJSON):
    try:
      with open(DEBUGSTARTLOADDATAJSON or LOADDATAJSON, 'r') as j:
        jd=json.load(j)
        loadedver=jd.get('ver')
        for pf, fs in jd.items(): # if os.path.exists(pf):     #mod retain invalid
          if pf=='ver':
            continue
          SESSIONSIGS[pf]={}
          for fn, ds in fs.items():  # if os.path.exists(fn) and len(lines) > 0:     #mod retain invalid
            SESSIONSIGS[pf][fn]={}
            if WORKJSONVER=='1':
              if loadedver=='1':
                for k, v in ds.items():
                  if k in [*ENUMSIGSCOPE, INVALIDSIG]:
                    t=[]
                    for o in v:
                      if o.get("ln") is not None:
                        ao={
                          "ln": o.get("ln")
                        }
                        if "tp"  in o:  ao["tp"]=o.get("tp")
                        if "ts"  in o:  ao["ts"]=o.get("ts")
                        if "c"   in o:   ao["c"]=o.get("c")
                        if "tpa" in o: ao["tpa"]=o.get("tpa")
                        if "tsa" in o: ao["tsa"]=o.get("tsa")
                        if "ca"  in o:  ao["ca"]=o.get("ca")
                        t.append(ao)
                    SESSIONSIGS[pf][fn][k]=t
                  elif k in [S1NAMETS, S1NAMETSLOCAL]:
                    SESSIONSIGS[pf][fn][k]=v
              else: # cepthomas/SbotSignet 1567db9
                SESSIONSIGS[pf][fn]['DATAHOT'] = [{"ln": o} for o in ds]
      # print('sigbk json diskread')
      # print(SESSIONSIGS)
    except Exception:
      raise
    #   error(f'Error reading {LOADDATAJSON}: {e}', e.__traceback__)
def writeJsonWithSessionsigs():
  timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
  temp_file = f"{SAVEDATAJSON}.{timestamp}.tmp"
  try:
      with open(temp_file, 'w') as fp:
        if WORKJSONVER=='1':
          if SAVEJSONVER=='1':
            json.dump(SESSIONSIGS, fp, indent=2)
          else: # cepthomas/SbotSignet 1567db9
            json.dump({
                pf: {fn: [v['ln'] for v in ds['DATAHOT']] 
                    for fn, ds in fs.items()}
                for pf, fs in SESSIONSIGS.items() if pf != 'ver'
              }, fp, indent=2)
      os.replace(temp_file, SAVEDATAJSON)
  except Exception:
      if os.path.exists(temp_file):
          pass#os.remove(temp_file)
      raise

class E20260901(sublime_plugin.EventListener):
  def on_init(self, views):
    updateSessionsigsFromDiskreadJson()
    if len(views) > 0 and views[0].window() is not None:
      for view in views:
        if not view.is_dirty():
          updateScope0SigFromScope1Sig(view)
        updateViewRegionsFromScopedSig('DATAHOT',view)
  def on_load_project(self, window): #  Project > Open; ! Not triggered at program start even if project restored  
    for view in window.views():
        if not view.is_dirty():
          updateScope0SigFromScope1Sig(view)
        updateViewRegionsFromScopedSig('DATAHOT',view)
  def on_load(self, view):
    updateSessionsigsFromDiskreadJson() #TODO reduce diskread
    if not view.is_dirty(): # needed?
      updateScope0SigFromScope1Sig(view)
    updateViewRegionsFromScopedSig('DATAHOT',view)
  def on_pre_close_project(self, window):
    for view in window.views():
      updateScope0SigFromViewRegions(view)
    writeJsonWithSessionsigs()
  # def on_pre_close(self, view): pass # children of on_pre_close_project()
  def on_deactivated(self, view): # lost focus
    if((fn:=view.file_name())
      and os.path.exists(fn)
    ):
      updateScope0SigFromViewRegions(view)
      writeJsonWithSessionsigs()
  def on_activated(self, view):
    if(  view.name()==MATCHFINDRESULTVIEW 
      or MATCHFINDRESULTVIEW in (view.file_name() or '') ):
      # sublime.status_message(u".") # visually replace previous 
      pass # findresultsmod plugin
    elif SYMLISTVIEW_NAMEID in view.name() or SYMLISTVIEW_NAMEID in (view.file_name() or ''):
      # sublime.status_message(u".") # visually replace previous
      pass # symlist plugin
    else:
      rs=sigrowlistFromViewRegions(view)
      if len(rs)==0: # tab right click > Split View
        if not view.is_dirty():
          updateScope0SigFromScope1Sig(view)
        updateViewRegionsFromScopedSig('DATAHOT',view)
        rs=sigrowlistFromViewRegions(view)
      if len(rs)>1:
        sublime.status_message(u"🔖 {0} bookmark{1}".format(len(rs),'s' if len(rs)>1 else ''))
    #
    if(   not view.is_dirty()
      and (f:=view.file_name()) 
      and (w:=view.window())
      and (pf:=w.project_file_name()) # is project
      and (p:=getProject(pf)) is not None # already has entry
      and os.path.exists(f)
    ):
      if not (ts:=getScope1TSOfFile(p,f)):
        if getScopedSigsOfFile('DATAHOT',p,f):
          newScope1TSAndSigFromScope0Sig(p,f,view)
        else:
          if len(sigrowlistFromViewRegions(view))>0:
            newScope1TSAndSigAndScope0SigFromViewRegions(p,f,view)
      elif ts!=os.path.getmtime(view.file_name()):
        # vanilla prompt
        pass
  def on_post_save(self, view):
    if(   not view.is_dirty()
      and (f:=view.file_name()) 
      and (w:=view.window())
      and (pf:=w.project_file_name()) # is project
      and (p:=getProject(pf)) is not None # already has entry
      and (_:=getScopedSigsOfFile('DATAHOT',p,f)) is not None # empty[] truthy
      and os.path.exists(f)
    ):
      newScope1TSAndSigAndScope0SigFromViewRegions(p,f,view)
      writeJsonWithSessionsigs()
  def on_reload(self, view):
      updateScope0SigFromScope1Sig(view)
      updateViewRegionsFromScopedSig('DATAHOT',view)
  # def on_reload_async(self, view): seems always after on_sync
  def on_revert(self, view):
      updateScope0SigFromScope1Sig(view)
      updateViewRegionsFromScopedSig('DATAHOT',view)
  # def on_revert_async(self, view): seems always after on_sync

class SbotToggleSignetCommand(sublime_plugin.TextCommand):
  def is_visible(self):
    return self.view.is_scratch() is False and self.view.file_name() is not None
  def run(self, __):
    view=self.view
    if ( (not view.is_scratch())
      and (f:=view.file_name())
      and (w:=view.window())
      and (pf:=w.project_file_name()) # is project
      # and (p:=getProject(pf)) is not None # already has entry
      # and (obs:=getScopedSigsOfFile('DATAHOT',p,f)) is not None # empty[] truthy
      and (rs:=sigrowlistFromViewRegions(view)) is not None # empty[] truthy
      and (caret:=view.sel()[0].b if len(view.sel()) == 1 else None) is not None # 0 truthy
      and (r_:=view.rowcol(caret)) # invalid input outputs (0,0), is truthy         CAUTION invalid
    ):
      updateScope0SigFromViewRegions(view)
      r,_=r_
      if r is not None:
        if r in rs: rs.remove(r)
        else:       rs.append(r)
        p=getProject(pf) or newProject(pf)
        toggleScopedSig('DATAHOT',p,f,r,view)
        if not view.is_dirty(): toggleScopedSig('DATAFILETIME',p,f,r,view)
        cleanScope1OfFile(p,f)
      view.erase_regions(SIGNET_REGION_NAME)
      addViewRegionsFromScopedSig('DATAHOT',pf,f,view)
      writeJsonWithSessionsigs()
class SbotGotoSignetCommand(sublime_plugin.TextCommand):
    def is_enabled(self):
        return len(sigrowlistFromViewRegions(self.view))>0
    # def is_visible(self):
    #     return len(sigrowlistFromViewRegions(self.view))>0

    def run(self, __, where):
      dnext=where=='next'
      nav_all_files=sublime.load_settings(SETTINGSF).get('nav_all_files') or False
      view=self.view
      if ( (not view.is_scratch())
        and (fn:=view.file_name())
        and (w:=view.window())
        and (pf:=w.project_file_name()) # is project
        and (ps:=getProject(pf)) is not None # already has entry
        # and (obs:=getScopedSigsOfFile('DATAHOT',ps,fn)) is not None # empty[] truthy
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
    if((fn:=view.file_name())
      and os.path.exists(fn)
    ):
      updateScope0SigFromViewRegions(view)
      writeJsonWithSessionsigs()
    if (   (w:=view.window())
      and (pf:=w.project_file_name()) # is project
      and (ps:=getProject(pf)) is not None # already has entry
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
        obs=getScopedSigsOfFile('DATAHOT',ps,fn)
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
      self.view.insert(edit, self.view.size(), "{1}Listing bookmarks in {0}\n".format(s,"\n\n"if self.view.size()>0 else''))
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
class SbotlistarchivedCommand(sublime_plugin.TextCommand): #run_command('sbotlistarchived'
  def run(self, __):
    view=self.view
    if(   (f:=view.file_name())
      and (w:=view.window())
      and (pf:=w.project_file_name()) # is project
      and (p:=getProject(pf)) is not None # already has entry
      and (iobs:=getArchiveOfFile(p,f)) # empty[] falsy
    ):
      v=w.new_file()
      v.set_name('Archived bookmarks of {0}'.format(f))
      v.set_scratch(True)
      v.run_command('sbotappendarchiveview',{'x':f,'y':"\n".join(
        [ ('\n ln#'+str(p['ln']).ljust(4) + str(p['tp'])                                           +':'+str(p['c'])
          +'\n '+           ''.ljust(3+4) + str(p['tpa'])                                          +':'+str(p['ca'])
          +'\n '+      '(now)'.ljust(3+4) + time.strftime("%Y-%m-%d %a %H:%M:%S", time.localtime())+':'+view.substr(view.line(view.text_point(p["ln"], 0)))
          ) for p in iobs ] ) })
class SbotappendarchiveviewCommand(sublime_plugin.TextCommand): #run_command('sbotappendarchiveview',{'x':
  def run(self, edit, x='', y=''):
    view=self.view
    self.view.insert(edit,0, "Listing archived bookmarks of {0}\n".format(x))
    self.view.insert(edit, self.view.size(), y)