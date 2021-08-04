# GTKWave
http://gtkwave.sourceforge.net/

**Tested versions:**
 - gtkwave 3.3.104-108

**New:**

**Change:**

**Obsolete:**

## Strategy

## Supported
`gtkwave` can be opened on Linux/Windows if gtkwave is in the PATH.
On Mac, it is supposed the packaged application is installed.

`gtkwave` support to save the view in a *.gtkw file. If a gtkw view is
found in the current directory, it will be loaded. Otherwise, the VCD
file is loaded.

## List of flags to be specified
-n, --nocli=[DIRPATH]: use file requester for dumpfile name

-f, --dump=[FILE]: specify dumpfile name

-F, --fastload: use VCD recoder fastload files

-o, --optimize: optimize VCD to FST

-a, --save=[FILE]: specify savefile name

-A, --autosavename

-r, --rcfile=[FILE]: specify override .rcfile name. to be investigated

-d, defaultskip: skip defaults if missing .rcfile

-D, --dualid=[WHICH]: specify multissesion identifier

-l, --logfile=[FILE]: specify simulation logfile name for time values

-s, --start=[TIME]: specify start time for LXT2/VZT block skip

-e, --end=[TIME]: specify end time for LXT2/VZT block skip

-t, --stems=[FILE]: specify stems file for source code annotation
                    to be investigated

-c, --cpu=[NUMCPUS]: specify number of CPUs for parallelizeable ops

-N, --nowm: disable window manager. `gtkwave` is almost unusable.

-M, --nomenus: do not render menubar. user has to know all shortcuts `gtkwave`. Prefered to not opt-in this option.

-S, --script=[FILE]: specify Tcl command script

-T, --tcl_init=[FILE]: specify Tcl command script for startup

-W, --wish: enable Tcl command line on stdio

-R, --repscript=[FILE]: specify timer-driven Tcl command script file

-P, --repperiod=[VALUE]: specify repscript period in msec

-g, --giga: use gigabyte mempacking when recoding

-z, --slider-zoom: enable horizontal slider stretch zoom
no noticeable change in User Experience on touchpad or mouse