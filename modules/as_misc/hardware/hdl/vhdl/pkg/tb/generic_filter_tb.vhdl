library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;
use work.as_generic_filter.all;

entity GENERIC_FILTER_TB is
end GENERIC_FILTER_TB;


architecture SET_GET_WINDOW_TEST of GENERIC_FILTER_TB is
    signal window : t_generic_window(0 to 1, 0 to 1, 1 downto 0) := ((('0', '0'), ('0', '1')), (('1', '0'), ('1', '1')));
    signal slice : std_logic_vector(1 downto 0);
begin
    process
    begin
        slice <= f_get_vector_of_generic_window(window, 0, 0);
        wait for 3 ns;
        report integer'image(to_integer(unsigned(slice)));
        assert slice = "00";
        slice <= f_get_vector_of_generic_window(window, 0, 1);
        wait for 3 ns;
        report integer'image(to_integer(unsigned(slice)));
        assert slice = "01";
        slice <= f_get_vector_of_generic_window(window, 1, 0);
        wait for 3 ns;
        report integer'image(to_integer(unsigned(slice)));
        assert slice = "10";
        slice <= f_get_vector_of_generic_window(window, 1, 1);
        wait for 3 ns;
        report integer'image(to_integer(unsigned(slice)));
        assert slice = "11";
        
        
        slice <= "01";
        wait for 3 ns;
        f_set_vector_of_generic_window(window, 0, 0, slice);
        wait for 3 ns;
        slice <= f_get_vector_of_generic_window(window, 0, 0);
        wait for 3 ns;
        report integer'image(to_integer(unsigned(slice)));
        assert slice = "01";
        
        slice <= "00";
        wait for 3 ns;
        f_set_vector_of_generic_window(window, 0, 1, slice);
        wait for 3 ns;
        slice <= f_get_vector_of_generic_window(window, 0, 1);
        wait for 3 ns;
        report integer'image(to_integer(unsigned(slice)));
        assert slice = "00";
        
        slice <= "11";
        wait for 3 ns;
        f_set_vector_of_generic_window(window, 1, 0, slice);
        wait for 3 ns;
        slice <= f_get_vector_of_generic_window(window, 1, 0);
        wait for 3 ns;
        report integer'image(to_integer(unsigned(slice)));
        assert slice = "11";
        
        
        slice <= "10";
        wait for 3 ns;
        f_set_vector_of_generic_window(window, 1, 1, slice);
        wait for 3 ns;
        slice <= f_get_vector_of_generic_window(window, 1, 1);
        wait for 3 ns;
        report integer'image(to_integer(unsigned(slice)));
        assert slice = "10";
        wait;
    end process;

end architecture;

architecture SET_GET_LINE_TEST of GENERIC_FILTER_TB is
    signal gline : t_generic_line(0 to 3, 1 downto 0) :=
        (('0', '0'), ('0', '1'), ('1', '0'), ('1', '1'));
    signal word : std_logic_vector(1 downto 0);
begin
    testbench : process is
    begin
        word <= f_get_vector_of_generic_line(gline, 0);
        wait for 3 ns;
        assert word = "00" report "Line(0) got wrong result!";
        wait for 3 ns;
        word <= f_get_vector_of_generic_line(gline, 1);
        wait for 3 ns;
        assert word = "01" report "Line(1) got wrong result!";
        wait for 3 ns;
        word <= f_get_vector_of_generic_line(gline, 2);
        wait for 3 ns;
        assert word = "10" report "Line(2) got wrong result!";
        wait for 3 ns;
        word <= f_get_vector_of_generic_line(gline, 3);
        wait for 3 ns;
        assert word = "11" report "Line(3) got wrong result!";
        wait for 3 ns;

        f_set_vector_of_generic_line(gline, 0, "01");
        wait for 3 ns;
        word <= f_get_vector_of_generic_line(gline, 0);
        wait for 3 ns;
        assert word = "10" report "Line(0) got wrong result after set!";
        wait for 3 ns;
        f_set_vector_of_generic_line(gline, 3, "00");
        wait for 3 ns;
        word <= f_get_vector_of_generic_line(gline, 3);
        wait for 3 ns;
        assert word = "00" report "Line(3) got wrong result after set!";
        wait for 3 ns;
        
        report "Test complete!";
        wait;
    end process;
end architecture;



architecture FILTER_MAX_TEST of GENERIC_FILTER_TB is
    signal filter : t_generic_filter(0 to 1, 0 to 1) := ((1, 2), (3, -4));
    signal max : natural;
begin
    process
    begin
	max <= f_get_filter_max(filter);
	wait for 3 ns;
	assert max = 4;
	wait;
    end process;
end architecture;

architecture FILTER_SUM_ABS_TEST of GENERIC_FILTER_TB is
    signal filter : t_generic_filter(0 to 1, 0 to 1) := ((1, 2), (3, -4));
    signal sum : natural;
begin
    process
    begin
	sum <= f_get_filter_sum_abs(filter);
	wait for 3 ns;
	assert sum = 10;
	wait;
    end process;
end architecture;

architecture WINDOW_AND_LINE_TEST of GENERIC_FILTER_TB is

    signal gwindow : t_generic_window(0 to 2, 0 to 2, 7 downto 0);
    signal gline_8 : t_generic_line(0 to 2, 7 downto 0);
    signal gline_4 : t_generic_line(0 to 2, 3 downto 0);
    signal gline_8_short : t_generic_line(0 to 1, 7 downto 0);
    signal test_data : t_generic_line(0 to 2, 7 downto 0);

begin
    testbench : process is
    begin
        -- Window setup
        f_set_vector_of_generic_window(gwindow, 0, 0, "11001111"); -- "11110011"); -- 243
        f_set_vector_of_generic_window(gwindow, 1, 0, "11111100"); -- "00111111"); --  63
        f_set_vector_of_generic_window(gwindow, 2, 0, "11110011"); -- "11001111"); -- 207

        f_set_vector_of_generic_window(gwindow, 0, 1, "01001111"); -- "11110010"); -- 242
        f_set_vector_of_generic_window(gwindow, 1, 1, "01111100"); -- "00111110"); --  62
        f_set_vector_of_generic_window(gwindow, 2, 1, "01110011"); -- "11001110"); -- 206

        f_set_vector_of_generic_window(gwindow, 0, 2, "00110011"); -- "11001100"); -- 204
        f_set_vector_of_generic_window(gwindow, 1, 2, "00111111"); -- "11111100"); -- 252
        f_set_vector_of_generic_window(gwindow, 2, 2, "00001111"); -- "11110000"); -- 240

        -- Test data line setup
        f_set_vector_of_generic_line(test_data, 0,    "10101010"); -- "01010101"); --  85
        f_set_vector_of_generic_line(test_data, 1,    "01010101"); -- "10101010"); -- 170
        f_set_vector_of_generic_line(test_data, 2,    "11100110"); -- "01100111"); -- 103
        wait for 3 ns;

        -- Test if window lines get correctly assigned to generic line signals
        -- Test Y 0
        gline_8 <= f_get_line_of_generic_window(gwindow, 0);
        wait for 3 ns;
        assert f_get_vector_of_generic_line(gline_8, 0) = "11110011" report "WINDOW(0,0) failed to assign to line!";
        report integer'image(to_integer(unsigned(f_get_vector_of_generic_line(gline_8, 0))));
        assert f_get_vector_of_generic_line(gline_8, 1) = "00111111" report "WINDOW(1,0) failed to assign to line!";
        report integer'image(to_integer(unsigned(f_get_vector_of_generic_line(gline_8, 1))));
        assert f_get_vector_of_generic_line(gline_8, 2) = "11001111" report "WINDOW(2,0) failed to assign to line!";
        report integer'image(to_integer(unsigned(f_get_vector_of_generic_line(gline_8, 2))));
        -- Test Y 1
        gline_8 <= f_get_line_of_generic_window(gwindow, 1);
        wait for 3 ns;
        assert f_get_vector_of_generic_line(gline_8, 0) = "11110010" report "WINDOW(0,1) failed to assign to line!";
        report integer'image(to_integer(unsigned(f_get_vector_of_generic_line(gline_8, 0))));
        assert f_get_vector_of_generic_line(gline_8, 1) = "00111110" report "WINDOW(1,1) failed to assign to line!";
        report integer'image(to_integer(unsigned(f_get_vector_of_generic_line(gline_8, 1))));
        assert f_get_vector_of_generic_line(gline_8, 2) = "11001110" report "WINDOW(2,1) failed to assign to line!";
        report integer'image(to_integer(unsigned(f_get_vector_of_generic_line(gline_8, 2))));
        -- Test Y 2
        gline_8 <= f_get_line_of_generic_window(gwindow, 2);
        wait for 3 ns;
        assert f_get_vector_of_generic_line(gline_8, 0) = "11001100" report "WINDOW(0,2) failed to assign to line!";
        report integer'image(to_integer(unsigned(f_get_vector_of_generic_line(gline_8, 0))));
        assert f_get_vector_of_generic_line(gline_8, 1) = "11111100" report "WINDOW(1,2) failed to assign to line!";
        report integer'image(to_integer(unsigned(f_get_vector_of_generic_line(gline_8, 1))));
        assert f_get_vector_of_generic_line(gline_8, 2) = "11110000" report "WINDOW(2,2) failed to assign to line!";
        report integer'image(to_integer(unsigned(f_get_vector_of_generic_line(gline_8, 2))));

        
        -- Same test for partial assignment of window lines
        -- to generic line signals shorter than the window width
        -- Test Y 1 X 0 to 1
        gline_8_short <= f_get_part_line_of_generic_window(gwindow, 1, 0, 2);
        wait for 3 ns;
        assert f_get_vector_of_generic_line(gline_8_short, 0) = "11110010" report "WINDOW(0,0) failed to assign to line!";
        report integer'image(to_integer(unsigned(f_get_vector_of_generic_line(gline_8_short, 0))));
        assert f_get_vector_of_generic_line(gline_8_short, 1) = "00111110" report "WINDOW(1,0) failed to assign to line!";
        report integer'image(to_integer(unsigned(f_get_vector_of_generic_line(gline_8_short, 1))));
        -- Test Y 1 X 1 to 2
        gline_8_short <= f_get_part_line_of_generic_window(gwindow, 1, 1, 2);
        wait for 3 ns;
        assert f_get_vector_of_generic_line(gline_8_short, 0) = "00111110" report "WINDOW(0,0) failed to assign to line!";
        report integer'image(to_integer(unsigned(f_get_vector_of_generic_line(gline_8_short, 0))));
        assert f_get_vector_of_generic_line(gline_8_short, 1) = "11001110" report "WINDOW(1,0) failed to assign to line!";
        report integer'image(to_integer(unsigned(f_get_vector_of_generic_line(gline_8_short, 1))));

        -- Test if vectors in generic lines are correctly cut 
        -- Test X 2 to 5; Same as: 
        -- short_word <= long_word(5 downto 2); -- for every word in the line
        gline_4 <= f_cut_vectors_of_generic_line(gline_8, 2, 4);
        wait for 3 ns;
        assert f_get_vector_of_generic_line(gline_4, 0) = "0011" report "Line_8(0) failed partial assignment to line_4";
        report integer'image(to_integer(unsigned(f_get_vector_of_generic_line(gline_4, 0))));
        assert f_get_vector_of_generic_line(gline_4, 1) = "1111" report "Line_8(1) failed partial assignment to line_4";
        report integer'image(to_integer(unsigned(f_get_vector_of_generic_line(gline_4, 1))));
        assert f_get_vector_of_generic_line(gline_4, 2) = "1100" report "Line_8(2) failed partial assignment to line_4";
        report integer'image(to_integer(unsigned(f_get_vector_of_generic_line(gline_4, 2))));
        -- Test X 4 to 7
        gline_4 <= f_cut_vectors_of_generic_line(gline_8, 4, 4);
        wait for 3 ns;
        assert f_get_vector_of_generic_line(gline_4, 0) = "1100" report "Line_8(0) failed partial assignment to line_4";
        report integer'image(to_integer(unsigned(f_get_vector_of_generic_line(gline_4, 0))));
        assert f_get_vector_of_generic_line(gline_4, 1) = "1111" report "Line_8(1) failed partial assignment to line_4";
        report integer'image(to_integer(unsigned(f_get_vector_of_generic_line(gline_4, 1))));
        assert f_get_vector_of_generic_line(gline_4, 2) = "1111" report "Line_8(2) failed partial assignment to line_4";
        report integer'image(to_integer(unsigned(f_get_vector_of_generic_line(gline_4, 2))));

        -- Test if a line of the window can be overwritten by a generic line signal
        -- Test Y 0
        f_set_line_of_generic_window(gwindow, 0, test_data);
        wait for 3 ns;
        gline_8 <= f_get_line_of_generic_window(gwindow, 0);
        wait for 3 ns;
        assert f_get_vector_of_generic_line(gline_8, 0) = "01010101" report "Failed to set and read back WINDOW(0,0)!";
        report integer'image(to_integer(unsigned(f_get_vector_of_generic_line(gline_8, 0))));
        assert f_get_vector_of_generic_line(gline_8, 1) = "10101010" report "Failed to set and read back WINDOW(1,0)!";
        report integer'image(to_integer(unsigned(f_get_vector_of_generic_line(gline_8, 1))));
        assert f_get_vector_of_generic_line(gline_8, 2) = "01100111" report "Failed to set and read back WINDOW(2,0)!";
        report integer'image(to_integer(unsigned(f_get_vector_of_generic_line(gline_8, 2))));
        -- Test Y 2
        f_set_line_of_generic_window(gwindow, 2, test_data);
        wait for 3 ns;
        gline_8 <= f_get_line_of_generic_window(gwindow, 2);
        wait for 3 ns;
        assert f_get_vector_of_generic_line(gline_8, 0) = "01010101" report "Failed to set and read back WINDOW(0,2)!";
        report integer'image(to_integer(unsigned(f_get_vector_of_generic_line(gline_8, 0))));
        assert f_get_vector_of_generic_line(gline_8, 1) = "10101010" report "Failed to set and read back WINDOW(1,2)!";
        report integer'image(to_integer(unsigned(f_get_vector_of_generic_line(gline_8, 1))));
        assert f_get_vector_of_generic_line(gline_8, 2) = "01100111" report "Failed to set and read back WINDOW(2,2)!";
        report integer'image(to_integer(unsigned(f_get_vector_of_generic_line(gline_8, 2))));

        report "Test complete!";
        wait;
    end process;
end architecture WINDOW_AND_LINE_TEST;

architecture MAKE_WINDOW_TEST of GENERIC_FILTER_TB is
    signal gwindow : t_generic_window(0 to 2, 0 to 2, 7 downto 0);
    type test_data is array(0 to 2) of t_integer_array(0 to 2);
    signal word : std_logic_vector(7 downto 0);
begin
    testbench : process is
    begin
        gwindow <= f_make_generic_window(3, 3, select_kernel(3, "sobel_y"), 8);
        wait for 3 ns;
        word <= f_get_vector_of_generic_window(gwindow, 0, 0);
        wait for 3 ns;
        assert to_integer(signed(word)) = 1 report "Sobel Y (0, 0) read incorrectly!";
        report integer'image(to_integer(signed(word)));
        word <= f_get_vector_of_generic_window(gwindow, 1, 0);
        wait for 3 ns;
        assert to_integer(signed(word)) = 2 report "Sobel Y (1, 0) read incorrectly!";
        report integer'image(to_integer(signed(word)));
        word <= f_get_vector_of_generic_window(gwindow, 2, 0);
        wait for 3 ns;
        assert to_integer(signed(word)) = 1 report "Sobel Y (2, 0) read incorrectly!";
        report integer'image(to_integer(signed(word)));
        word <= f_get_vector_of_generic_window(gwindow, 0, 1);
        wait for 3 ns;
        assert to_integer(signed(word)) = 0 report "Sobel Y (0, 1) read incorrectly!";
        report integer'image(to_integer(signed(word)));
        word <= f_get_vector_of_generic_window(gwindow, 1, 1);
        wait for 3 ns;
        assert to_integer(signed(word)) = 0 report "Sobel Y (1, 1) read incorrectly!";
        report integer'image(to_integer(signed(word)));
        word <= f_get_vector_of_generic_window(gwindow, 2, 1);
        wait for 3 ns;
        assert to_integer(signed(word)) = 0 report "Sobel Y (2, 1) read incorrectly!";
        report integer'image(to_integer(signed(word)));
        word <= f_get_vector_of_generic_window(gwindow, 0, 2);
        wait for 3 ns;
        assert to_integer(signed(word)) = -1 report "Sobel Y (0, 2) read incorrectly!";
        report integer'image(to_integer(signed(word)));
        word <= f_get_vector_of_generic_window(gwindow, 1, 2);
        wait for 3 ns;
        assert to_integer(signed(word)) = -2 report "Sobel Y (1, 2) read incorrectly!";
        report integer'image(to_integer(signed(word)));
        word <= f_get_vector_of_generic_window(gwindow, 2, 2);
        wait for 3 ns;
        assert to_integer(signed(word)) = -1 report "Sobel Y (2, 2) read incorrectly!";
        report integer'image(to_integer(signed(word)));


        gwindow <= f_make_generic_window(3, 3, select_kernel(3, "sobel_x"), 8);
        wait for 3 ns;
        word <= f_get_vector_of_generic_window(gwindow, 0, 0);
        wait for 3 ns;
        assert to_integer(signed(word)) = 1 report "Sobel X (0, 0) read incorrectly!";
        report integer'image(to_integer(signed(word)));
        word <= f_get_vector_of_generic_window(gwindow, 1, 0);
        wait for 3 ns;
        assert to_integer(signed(word)) = 0 report "Sobel X (1, 0) read incorrectly!";
        report integer'image(to_integer(signed(word)));
        word <= f_get_vector_of_generic_window(gwindow, 2, 0);
        wait for 3 ns;
        assert to_integer(signed(word)) = -1 report "Sobel X (2, 0) read incorrectly!";
        report integer'image(to_integer(signed(word)));
        word <= f_get_vector_of_generic_window(gwindow, 0, 1);
        wait for 3 ns;
        assert to_integer(signed(word)) = 2 report "Sobel X (0, 1) read incorrectly!";
        report integer'image(to_integer(signed(word)));
        word <= f_get_vector_of_generic_window(gwindow, 1, 1);
        wait for 3 ns;
        assert to_integer(signed(word)) = 0 report "Sobel X (1, 1) read incorrectly!";
        report integer'image(to_integer(signed(word)));
        word <= f_get_vector_of_generic_window(gwindow, 2, 1);
        wait for 3 ns;
        assert to_integer(signed(word)) = -2 report "Sobel X (2, 1) read incorrectly!";
        report integer'image(to_integer(signed(word)));
        word <= f_get_vector_of_generic_window(gwindow, 0, 2);
        wait for 3 ns;
        assert to_integer(signed(word)) = 1 report "Sobel X (0, 2) read incorrectly!";
        report integer'image(to_integer(signed(word)));
        word <= f_get_vector_of_generic_window(gwindow, 1, 2);
        wait for 3 ns;
        assert to_integer(signed(word)) = 0 report "Sobel X (1, 2) read incorrectly!";
        report integer'image(to_integer(signed(word)));
        word <= f_get_vector_of_generic_window(gwindow, 2, 2);
        wait for 3 ns;
        assert to_integer(signed(word)) = -1 report "Sobel X (2, 2) read incorrectly!";
        report integer'image(to_integer(signed(word)));
        
        wait;
    end process;

end architecture;

architecture OTHER_TESTS of GENERIC_FILTER_TB is
    signal gwindow : t_generic_window(0 to 2, 0 to 2, 7 downto 0);
    signal gline   : t_generic_line(0 to 2, 7 downto 0);
    constant test_data : t_integer_array(0 to 8) := (7, 15, 23, 7, 23, 31, 8, 7, 9);
    signal word : std_logic_vector(7 downto 0);
    signal temp_to0, temp_to1, temp_to2 : std_logic_vector(7 downto 0);
begin
    testbench : process is
    begin
        -- Test consecutive read/writes to/from generic window
        for D in test_data'range loop
            for Y in gwindow'length(2) - 1 downto 0 loop
                if Y < 2 then
                    f_set_vector_of_generic_window(gwindow, 0, Y + 1, f_get_vector_of_generic_window(gwindow, 2, Y));
                end if;
                f_set_vector_of_generic_window(gwindow, 2, Y, f_get_vector_of_generic_window(gwindow, 1, Y));
                f_set_vector_of_generic_window(gwindow, 1, Y, f_get_vector_of_generic_window(gwindow, 0, Y));
            end loop;
            f_set_vector_of_generic_window(gwindow, 0, 0, std_logic_vector(to_unsigned(test_data(D), gwindow'length(3))));
            wait for 2 ns;
        end loop;
        for Y in gwindow'range(2) loop
            for X in gwindow'range(1) loop
                word <= f_get_vector_of_generic_window(gwindow, X, Y);
                wait for 2 ns;
                assert to_integer(unsigned(word)) = test_data(8 - (X + Y * 3)) 
                    report "Data incorrect @(" & integer'image(X) & ", " & integer'image(Y) & ")! Is: " 
                            & integer'image(to_integer(unsigned(word))) & " Should: " & integer'image(test_data(8 - (X + Y * 3)));
            end loop;
        end loop;
        
        for D in test_data'range loop
            temp_to2 <= f_get_vector_of_generic_line(gline, 1);
            temp_to1 <= f_get_vector_of_generic_line(gline, 0);
            temp_to0 <= std_logic_vector(to_unsigned(test_data(D), gline'length(2)));
            wait for 2 ns;
            f_set_vector_of_generic_line(gline, 2, temp_to2);
            f_set_vector_of_generic_line(gline, 1, temp_to1);
            f_set_vector_of_generic_line(gline, 0, temp_to0);
            wait for 2 ns;
        end loop;
        for X in 0 to 2 loop
            word <= f_get_vector_of_generic_line(gline, X);
            wait for 2 ns;
            assert to_integer(unsigned(word)) = test_data(8 - X) 
                report "Data incorrect @(" & integer'image(X) & ")! Is: " & integer'image(to_integer(unsigned(word))) 
                    & " Should: " & integer'image(test_data(8 - X));
        end loop;

        gline(0, 0) <= '1';
        gline(0, 1) <= '0';
        gline(0, 2) <= '1';
        gline(0, 3) <= '0';
        gline(0, 4) <= '1';
        gline(0, 5) <= '0';
        gline(0, 6) <= '1';
        gline(0, 7) <= '0';
        wait for 2 ns;
        f_set_line_of_generic_window(gwindow, 0, gline);
        wait for 2 ns;
        word <= f_get_vector_of_generic_window(gwindow, 0, 0);
        wait for 2 ns;
        assert word = "01010101" report "Failed to read back Window(0, 0)!";
        report integer'image(to_integer(unsigned(word)));
        f_set_line_of_generic_window(gwindow, 0, f_get_line_of_generic_window(gwindow, 0));
        wait for 2 ns;
        word <= f_get_vector_of_generic_window(gwindow, 0, 0);
        wait for 2 ns;
        assert word = "01010101" report "Failed to read back Window(0, 0) after write back!";
        report integer'image(to_integer(unsigned(word)));

        report "Test complete!";
        wait;
    end process;
end architecture;