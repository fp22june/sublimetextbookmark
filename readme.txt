wip 2026Sep    scope, instance, data lifespan, event
  current modded plugin still has bugs
    because bookmark data is synced to current view instance only, but not file or fileeditbuffer
    eg. when content overwritten externally, common in repo git ops
    see "<tricky" and "<<<" below 
  do not trust AIs
    wrong logic  st event, data lifespan and scope
    wrong api syntax sometimes
  st4 observations, incomplete,         < tested only with  habit at least one project longrunning, todo utest
    sublimeapistudy.py , powershell sublimeapistudy_log.txt read,  gutter   .sublime-keymap   { "keys": ["f9"], "command": "e1"},
    note
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
      del                                                  <ignore,  user can decide with bkmtoggle
        no yet known logic retain regions 
        no yet known logic retain vanilla bookmark
      undo del to ins somehow                               <ignore for now
        somehow restore regions
        somehow restore vanilla bookmark
      at st close; restart
        save, load dirty                               <not tested when file external changed,ignore for now
        discard gutterregions
        save, load vanilla bookmark
      at project close; open
        save, load dirty                               <not te..
        discard gutterregions
        save, load vanilla bookmark
      at File>Open                              <on_load
        no regions
        no vanilla bookmark
      at tab rightlick > SplitView
        inherit and sync dirty
        no regions inherit                       < on_activated{     DONE
        no vanilla bookmark inherit
      at file save                          <on_post_save etc
        consol edit
        nochange regions
        nochange vanilla bookmark
      at view close (click tab X)
        discard regions
        discard vanilla bookmark                                  < feature most wanted by sublimetexters
      at view close; deny save prompt                            <tricky,  TODO next open need to restore from another bookmark storage, filetimestamp but not view synced 
        retain dirty , if not last view of file after SplitView
        discard dirty, only if last 
      while file open; content overwritten external                 < on_reload  on_reload_async
        auto load if not dirty
        prompt discard if dirty,   undoable restore regions
        discard regions                                             <tricky  TODO
        save, load/ try sync   vanilla bookmark
      File>Revert                                                <on_revert  on_revert_async 
        discard regions                                               <tricky TODO
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
    .
      save at least two versions perfile?                              <<<
        sync per file.dirty (same file, splitview), dispensable
        sync diskfile timestamp/linecount
        optional sync per view, dispensable
      bookmark store lcoation
        programfile/package  /.json
        sublime-project      window.set_project_data( d)
        per file
          allow diff proj, same bookmark; allow rename folder
          cautious public repo data leak
      plain json 
        notplanned bookmark storage at sublime-worksp/project
        easier edit after proj and folder rename
      View(st class).custommethod= def    per session
      persist across st close; loss at last tab/view close (==.sublime-worksp/project internally)
        view.settings().get/set()
        view.custom1=
      doesn't work get/setattr(view, "CUSTOM1", 1)
    mod
      toggle = diskwrite
      disable function bookmarkkey openfile if not yet
      disable function clearall fornow
      store line snippet when bookmarked
      list proj bookmarks w/ symlist 
      :=  [] {} 0 falsy is/not None
    don't
      camel<>underscore   class NocamelyestextsearchCommand(sublime_plugin.TextCommand):  #run_command('nocamelyestextsearch'
      view.id()     int recycle;     set().add(vid)  seems not working  
      storeread once only "at st start".