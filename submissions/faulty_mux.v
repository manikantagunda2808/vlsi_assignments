// Errors: RTL004, RTL007, RTL010

module faulty_mux (
    input i_clk,
    input i_rst_n,
    input [3:0] i_a,
    input [3:0] i_b,
    input i_sel,
    output reg [3:0] o_out
);

    // RTL007: o_out driven by two always blocks
    always_ff @(posedge i_clk or negedge i_rst_n) begin
        if (!i_rst_n)
            o_out <= 4'd0;
        else
            o_out <= i_a;
    end

    // RTL007: same signal o_out driven again
    always @(*) begin
        if (i_sel)
            o_out = i_b;   // multi-driven net
    end

    // RTL004: plain always instead of always_comb
    reg [3:0] unused_wire;  // RTL010: unused signal
    always @(*) begin
        unused_wire = i_a & i_b;
    end

endmodule
