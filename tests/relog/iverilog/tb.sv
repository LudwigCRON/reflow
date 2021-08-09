`timescale 1ns/100ps
`resetall

module tb;

    real VDD;
    real VREF;
    real VMAX;
    real VBRK;

    initial
    begin: reset
        VDD = 0.0;
        VREF = 0.05;
        VMAX = 0.07;
        VBRK = 0.09;
        $info("This testbench provide stimuli for `relog iverilog`");
        $info("VREF = %.3f V", VREF);
        $info("VMAX = %.3f V", VMAX);
        $info("VBRK = %.3f V", VBRK);
        #(100us);
        $fatal(1, "Unexpected timeout");
    end

    always forever
    begin: ramp_up
        #(1ns);
        VDD += 0.01;
        $display("VDD=%.3f V", VDD);
    end

    // ==== checks thresholds ====
    always forever
    begin: warnings
        #(1ns);
        if (VDD >= VREF && VDD < VMAX)
            $warning("VDD exceed nominal voltage Expected [%.3f V] Get [%.3f V]", VREF, VDD);
    end

    always forever
    begin: errors
        #(1ns);
        if (VDD >= VMAX)
            $error("VDD exceed maximal voltage Expected [<%.3f V] Get [%.3f V]", VMAX, VDD);
    end

    always forever
    begin: breakdown
        #(1ns);
        if (VDD > VBRK)
            $fatal(2, "VDD exceed breakdown voltage");
    end


endmodule