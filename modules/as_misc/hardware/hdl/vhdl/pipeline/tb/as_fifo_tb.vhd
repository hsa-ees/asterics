library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library asterics;
use asterics.as_fifo;

entity as_fifo_tb is
end entity;

architecture TB of as_fifo_tb is

    signal clk, reset, full, empty, write_en, read_en : std_logic;
    signal running : std_logic;
    signal data_in, data_out, comp : std_logic_vector(7 downto 0);

    type byte_array is array(0 to 10) of std_logic_vector(7 downto 0);
    constant test_data : byte_array := (X"DE", X"AD", X"BE", X"EF", X"13", X"37", X"29", X"FF", X"65", X"77", X"99");

begin

    dut : entity as_fifo
    generic map(
        DATA_WIDTH => 8,
        FIFO_DEPTH => 11
    )
    port map(
        clk => clk,
        reset => reset,
        data_in => data_in,
        write_en => write_en,
        data_out => data_out,
        read_en => read_en,
        full => full,
        empty => empty
    );

    p_clk : process is
    begin
        clk <= '1';
        wait for 5 ns;
        clk <= '0';
        wait for 5 ns;
        if running = '0' then
            wait;
        end if;
    end process;

    test : process is
    begin
        report "Start";
        running <= '1';
        reset <= '1';
        read_en <= '0';
        write_en <= '0';
        data_in <= (others => '0');
        wait for 15 ns;
        reset <= '0';
        wait for 10 ns;

        write_en <= '1';
        for N in 0 to 10 loop
            data_in <= test_data(N);
            wait for 10 ns;
        end loop;
        assert full = '1' report "Signal 'full' not asserted!";
        write_en <= '0';
        wait for 10 ns;
        read_en <= '1';

        for N in 0 to 10 loop
            wait for 10 ns;
            comp <= test_data(N);
            assert data_out = test_data(N) report "Test data " & integer'image(to_integer(unsigned(test_data(N)))) & " was read as " & integer'image(to_integer(unsigned(data_out))) & "!";
        end loop;
        assert empty = '1' report "Signal 'empty' not asserted!";
        write_en <= '1';
        read_en <= '0';
        -- Test auto-read functionality:
        -- Fill fifo
        for N in 0 to 10 loop
            data_in <= test_data(10 - N);
            wait for 10 ns;
        end loop;
        write_en <= '0';
        wait for 20 ns;
        write_en <= '1';
        -- fill more, "pushing" out old data
        for N in 0 to 10 loop
            data_in <= test_data(N);
            wait for 10 ns;
            comp <= test_data(10 - N);
            assert data_out = test_data(10 - N) report "Test data " & integer'image(to_integer(unsigned(test_data(10 - N)))) & " was read as " & integer'image(to_integer(unsigned(data_out))) & "!";
        end loop;
        report "Done";
        running <= '0';
        wait;


    end process;

end architecture;