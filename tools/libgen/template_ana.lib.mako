library (${library}) {
    technology (cmos);
    revision        : ${xlsx_version}/${block_version};
    delay_model     : table_lookup;
    bus_naming_style: "%s[%d]";

    /* set units for the entire file */
    time_unit               : "1ps";
    voltage_unit            : "1V";
    current_unit            : "1uA";
    pulling_resistance_unit : "1kohm";
    capacitive_load_unit (1,ff);
    leakage_power_unit: 1uW;

    /* define extraction conditions */
    operating_conditions ${corner_name} {
        process     : 1.0;
        voltage     : ${corner["voltage"]};
        temperature : ${corner["temperature"]};
        tree_type	: "worst_case_tree";
    }

    input_threshold_pct_fall        : 50.0;
    output_threshold_pct_fall       : 50.0;
    slew_lower_threshold_pct_fall   : 10.0;
    slew_upper_threshold_pct_fall   : 90.0;

    input_threshold_pct_rise        : 50.0;
    output_threshold_pct_rise       : 50.0;
    slew_lower_threshold_pct_rise   : 10.0;
    slew_upper_threshold_pct_rise   : 90.0;

    /* define different bus type needed */
    % for type in types:
    ${create_type(type)}
    % endfor

    /* define the characterized cell */
    cell (${block_name}) {
        area            : ${area};
        dont_touch      : true;
        dont_use        : true;
        interface_timing: true;

        % for pin in pins:
        ${create_pin_bus(pin)}
        % endfor
    }
}
<%def name="create_type(t)">
    type (bus_${t.width}) {
        base_type: array;
        data_type: bit;
        bit_width: ${t.width};
        bit_from: 0;
        bit_to: ${t.width-1};
        downto: true;
    }
</%def>
<%def name="create_pin_bus(p)">
        ${'bus' if p.width > 1 else 'pin'} (${p.dig_name}) {
            % if p.width > 1:
            bus_type    : bus_${p.width};
            % endif
            % if p.type == "CLOCK":
            clock       : true;
            % elif p.type in ["SEQUENTIAL", "RESET"]:
            direction   : ${p.direction};
            % endif
            % if p.direction == "input":
            capacitance : ${p.capacitance * 1e15};
            /* ${'RECOVERY' if p.type == 'RESET' else 'SETUP'}_TIME */
            timing() {
                related_pin		: "";
                timing_type		: ${'recovery' if p.type == 'RESET' else 'setup'}_(rising|falling);
                rise_constraint(scalar) {
                    values("${"%.3f" % (
                        p.setup[corner_name]*1e12 if corner_name in p.setup \
                        else p.setup['typ']*1e12
                    )}");
                }
                fall_constraint(scalar) {
                    values("${"%.3f" % (
                        p.setup[corner_name]*1e12 if corner_name in p.setup \
                        else p.setup['typ']*1e12
                    )}");
                }
            }
            /* ${'REMOVAL' if p.type == 'RESET' else 'HOLD'}_TIME */
            timing() {
                related_pin		: "";
                timing_type		: ${'removal' if p.type=='RESET' else 'hold'}_(rising|falling);
                rise_constraint(scalar) {
                    values("${"%.3f" % (
                        p.hold[corner_name]*1e12 if corner_name in p.hold \
                        else p.hold['typ']*1e12
                    )}");
                }
                fall_constraint(scalar) {
                    values("${"%.3f" % (
                        p.hold[corner_name]*1e12 if corner_name in p.hold \
                        else p.hold['typ']*1e12
                    )}");
                }
            }
            % else:
            max_fanout		: 2;
            max_capacitance	: ${p.capacitance};
            /* ACCESS_TIME */
            timing () {
                related_pin		: "";
                timing_type		: (rising|falling)_edge;
                cell_rise(scalar) {
                    values("${"%.3f" % (
                        p.setup[corner_name]*1e12 if corner_name in p.setup \
                        else p.setup['typ']*1e12
                    )}");
                }
                cell_fall(scalar) {
                    values("${"%.3f" % (
                        p.setup[corner_name]*1e12 if corner_name in p.setup \
                        else p.setup['typ']*1e12
                    )}");
                }
                rise_transition(scalar) {
                    values("${'%.3f' % (p.transition * 1e12)}");
                }
                fall_transition(scalar) {
                    values("${'%.3f' % (p.transition * 1e12)}");
                }
            }
            % endif

        }
</%def>