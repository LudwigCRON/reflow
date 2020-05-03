<% input_pins = [p for p in libs["template"].pins if p.direction == "input"] %>\
<% output_pins = [p for p in libs["template"].pins if p.direction == "output"] %>\
module basic_wrapper (
    input  wire      mcu_clk,
    input  wire      mcu_warm_rstb,

    % for p in input_pins:
    input  wire      ${p.ana_name},
    % endfor

    % for p in output_pins:
    output wire      ${p.ana_name}${',' if loop.index < len(output_pins)-1 else ''}
    % endfor
);

% for module in modules:
/*======== ${module.name} ========
    ${module}
    % for pin in module.pins:
        % if pin.width > 1 or pin.msb != 0 or pin.lsb != 0:
    ${pin.direction.lower()} ${pin.type.lower()}    [${pin.msb}:${pin.lsb}] ${pin.name}
        % else:
    ${pin.direction.lower()} ${pin.type.lower()}            ${pin.name}
        % endif
    % endfor
*/
% endfor

endmodule