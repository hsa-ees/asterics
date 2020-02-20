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
