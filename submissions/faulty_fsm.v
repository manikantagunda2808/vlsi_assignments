// Errors: RTL002, RTL004, RTL005, RTL009

module wrong_fsm (        // RTL009: module name != filename
    input clk,            // RTL005: missing i_ prefix
    input reset,          // RTL005: missing i_ prefix
    output reg out        // RTL005: missing o_ prefix
);

    reg [1:0] state;

    // RTL004: plain always instead of always_ff
    always @(posedge clk) begin
        if (reset)
            state <= 2'b00;
        else begin
            case (state)
                2'b00: state <= 2'b01;
                2'b01: state <= 2'b10;
                2'b10: state <= 2'b00;
                // RTL002: no default
            endcase
        end
    end

    // RTL004: plain always instead of always_comb
    always @(*) begin
        case (state)
            2'b00: out = 1'b0;
            2'b01: out = 1'b1;
            // RTL002: no default here either
        endcase
    end

endmodule
