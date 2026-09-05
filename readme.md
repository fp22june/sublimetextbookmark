demo video ![webm(2M)](https://raw.githubusercontent.com/fp22june/sublimetextbookmark/main/demo1.webm)

```
2026Sep
  modded
    disable function cmd nextbookmark openfileneeded part
    disable function cmd clearall    for now
    store line snippet when bookmarked
    list proj bookmarks w/ symlist 
    :=  [] {} 0 falsy is/not None
    edited file, File>Revert
    add signet, close st, file content overwritten externally (repo git ops), open
    don't edit, add signet only, st stay open, file content overwritten externally (repo git ops) (st auto reload)
  current issues
    add text, add signet, close st, open, undo to del added text
    at view close; deny save prompt
    backup option or ui show deleted for        unmatched sigs del at revert/extmod, .  

  test  commented commits should run, never get forcepsuhed
  dev   numbered commits may not run, often get forcepushed

  todo,notes
    save at least two versions perfile?                              see also "<tricky" 
      DONE SCOPE0HOT        per (buffer)[https://www.sublimetext.com/docs/api_reference.html#sublime.Buffer] (same file, splitview)
      DONE SCOPE1FILETIME   per actual file, eg. timestamp/linecount
      not for now           optionally per view
    signets store lcoation options
      programfile/package  /.json
      sublime-project      window.set_project_data( d)
      per file
        allow diff proj, same signets; allow rename folder
        cautious public repo data leak
    plain json 
      notplanned signets storage at sublime-worksp/project
      easier edit after proj and folder rename
    View(st class).custommethod= def    per session
    these persist across st close; but cleared at buffer end == last tab/view close (==.sublime-worksp/project internally)
      view.settings().get/set()
      view.custom1=
    doesn't work get/setattr(view, "CUSTOM1", 1)
  don't
    camel<>underscore   class NocamelyestextsearchCommand(sublime_plugin.TextCommand):  #run_command('nocamelyestextsearch'
    view.id()     int recycle;     set().add(vid)  seems not working  
    storeread once only "at st start".
    do not trust AIs
      wrong logic  st event, lifecycle, data lifespan and scope
      wrong api syntax sometimes
  st4 observations, incomplete,         < tested only with  habit at least one project longrunning;  todo utest (notplanned)
    summary
      file content sync w         buffer
        when content externally changed/user revert, if prompt buffer discard confirmed, retains vanilla bookmark(view), but removes gutterregions (view)
      gutterregions sync w        view            <signet
      vanilla bookmark  sync w    view
      plugin.py init with         session
      events
    sublimeapistudy.py
      powershell sublimeapistudy_log.txt read
      testgutterregions   .sublime-keymap   { "keys": ["f9"], "command": "e1"},
    observe
      text edit /view.dirty
      gutterregions         < view.add_regions(   < sync view, not shared by SplitView views
      vanilla bookmark                            < sync view,  ..
    behavior
      insert
        auto adjust regions
        auto adjust vanilla bookmark
      undo insert to del somehow (dirty, exit st, open, undo)    < TODO  , diy detct , no api on_undo
        somehow del regions
        somehow del vanilla bookmark
      del                                                  <ignore,  user can decide with togglecmd
        no yet known logic retain regions 
        no yet known logic retain vanilla bookmark
      undo del to ins somehow                               <ignore for now
        somehow restore regions
        somehow restore vanilla bookmark
      at st close; restart
        save, load dirty                               <not tested when file external changed,ignore for now
        discard regions
        save, load vanilla bookmark
      at project close; open
        save, load dirty                               <not te..
        discard regions
        save, load vanilla bookmark
      at File>Open                              <on_load
        no regions
        no vanilla bookmark
      at tab rightlick > SplitView
        inherit and sync dirty
        no regions inherit                       < on_activated{     DONE
        no vanilla bookmark inherit
      at file save                          <on_post_save     <diskwrite 
        consol edit
        nochange regions
        nochange vanilla bookmark
      at view close (click tab X)
        discard regions
        discard vanilla bookmark                                  < feature most wanted by sublimetexters
      at view close; deny save prompt                            <tricky, TODO
        retain dirty , if not last view of file after SplitView
        discard dirty, only if last 
      while file open; content overwritten external                 < on_reload  on_reload_async
        auto load if not dirty
        prompt discard if dirty,   undoable restore regions
        discard regions                                             <tricky  DONE
        save, load/ try sync   vanilla bookmark
      File>Revert                                                <on_revert  on_revert_async 
        discard regions                                               <tricky DONE
        save, load/ try sync   vanilla bookmark
    api
      at st start; hot reload   plugin.py edit/save               <avoid only readstore once here. togglebookmark, st/proj close/oprn  changes store and need readstore
        exec plugin.py root
        plugin_load()     view/window may not init yet
        plugin.py class on_init
      at st start
        opens last project(s) (to test multi projects   File>Exit)
        NO load_project   even if multi
        NO on_load
        on_activated  x1
      at ins,del                                      <nochange
      lostfocus                      on_deactivated   <diskwrite
      gainfocus                      on_activated
      at st close; and at project close
        on_pre_close_project        views[]           <diskwrite
        on_pre_close(view) etc       cautious  redundnat exec
      at tab rightlick > SplitView
        on_deactivated    curent
        on_activated      newsplitview  same file_name()
        NO on_load
      ONLY triggered by
        load_project
          File>Project>Open project
        on_load
          File>Project>Open project
          File>Open
    cmd
      toggle                                            <diskwrite
      gensymlist                                            <diskwrite
```