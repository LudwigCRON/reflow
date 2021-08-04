module $_DLATCH_P_(input E, input D, output Q);
    wire [1023:0] _TECHMAP_DO_ = "simplemap; opt";
	DLATCH _TECHMAP_REPLACE_ (
		.D(D),
		.G(E),
		.Q(Q)
	);
endmodule

module $_DLATCH_N_(input E, input D, output Q);
    wire [1023:0] _TECHMAP_DO_ = "simplemap; opt";
	DLATCH _TECHMAP_REPLACE_ (
		.D(D),
		.G(!E),
		.Q(Q)
	);
endmodule
