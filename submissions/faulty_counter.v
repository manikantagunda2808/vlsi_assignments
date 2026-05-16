// Intentionally buggy RTL for testing review bot

module faulty_counter_wrong_name (  // RTL009: module name != filename
    input clk,                       // RTL005: missing i_ prefix
    input rst,                       // RTL005: missing i_ prefix, RTL003: should be rst_n
    input enable,                    // RTL005: missing i_ prefix
    output [3:0] count               // RTL005: missing o_ prefix
);

    reg [3:0] count;

    // RTL001: latch inferred — missing else branch
    // RTL004: using plain always instead of always_ff
    always @(posedge clk) begin
        if (enable)
            count <= count + 1;
        // no else — latch risk
    end

    // RTL002: case with no default
    reg [1:0] state;
    always @(posedge clk) begin
        case (state)
            2'b00: state <= 2'b01;
            2'b01: state <= 2'b10;
            2'b10: state <= 2'b00;
            // RTL002: no default here
        endcase
    end

    // RTL006: signal with no reset state
    reg [3:0] data;
    always @(posedge clk) begin
        data <= count + 4'd5;  // no reset condition at all
    end

endmodule
