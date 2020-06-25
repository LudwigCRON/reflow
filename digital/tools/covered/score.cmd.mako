+libext+.v+.sv+
% if instance:
-t ${instance[0]}
-i ${top}.${instance[1]}
% else:
-t ${top}
% endif
-vcd ${vcd}
-g 3
% for src in files:
-v ${src}
% endfor