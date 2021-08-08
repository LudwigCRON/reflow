% for include_dir in include_dirs:
+incdir+${include_dir}
% endfor
+timescale+${timescale}

% for file in files:
${file}
% endfor

% for flag in flags:
${flag}
% endfor