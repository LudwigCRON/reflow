+libext+.v+.sv+.vh+.svh+
% if instance:
-t ${instance[0]}
% else:
-t ${top}
% endif
-vcd ${vcd}
-g 3
% for incdir in includes:
-I ${incdir}
% endfor
% for src in files:
-v ${src}
% endfor
