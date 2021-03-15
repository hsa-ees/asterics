------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2017 Hochschule Augsburg, University of Applied Sciences
------------------------ LICENSE ----------------------------------------
-- This program is free software; you can redistribute it and/or
-- modify it under the terms of the GNU Lesser General Public
-- License as published by the Free Software Foundation; either
-- version 3 of the License, or (at your option) any later version.
-- 
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
-- Lesser General Public License for more details.
-- 
-- You should have received a copy of the GNU Lesser General Public License
-- along with this program; if not, see <http://www.gnu.org/licenses/>
-- or write to the Free Software Foundation, Inc.,
-- 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
------------------------------------------------------------------------
-- Entity:         AS_CORDIC_ATAN_PIPE
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--                 Efficient Embedded Systems Group
--                 http://ees.hs-augsburg.de
--
-- Author:         Markus Bihler
--
-- Modified:       2017-06-07
--
-- Description:    Pipeline for calculating angles using the cordic 
--                 algorithm.
--
------------------------------------------------------------------------
--! @file  as_cordic_atan_pipe.vhd
--! @brief This entity implements an atan pipeline for the CORDIC algorithm.
----------------------------------------------------------------------------------

--! @addtogroup as_cordic_direction_internals
--! @{

library IEEE;
use IEEE.std_logic_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

use work.as_cordic_pkg.all;

entity AS_CORDIC_ATAN_PIPE is
  generic(
    gen_step_count : natural;
    gen_input_width : natural
  );
  port(
    clk           : in std_logic;
    reset         : in std_logic;
    
    strobe_in     : in  std_logic;
    x_in          : in  signed(gen_input_width-1 downto 0);
    y_in          : in  signed(gen_input_width-1 downto 0);
    
    z_out         : out signed(c_angle_width-1 downto 0)
    
  );
end AS_CORDIC_ATAN_PIPE;

--! @}

architecture RTL of AS_CORDIC_ATAN_PIPE is
  constant c_last_step : natural := gen_step_count-1;
  constant c_data_width : natural := gen_input_width+addBits(c_last_step)+1; -- +1 due to first addition (x_in+y_in); +addBits(steps) due to slr every step
  
  signal s_d : std_logic_vector(0 to c_last_step);
  
  type t_data_array is array(natural range <>) of signed(c_data_width-1 downto 0);
  type t_z_array is array(natural range <>) of signed(c_angle_width-1 downto 0);
  
  signal r_x : t_data_array(1 to c_last_step-1);
  signal r_y : t_data_array(1 to c_last_step);
  signal r_z : t_z_array(1 to c_last_step);
  signal s_d_mul_x : t_data_array(0 to c_last_step-1);
  signal s_d_mul_x2 : t_data_array(0 to c_last_step-1);
  signal s_d_mul_y : t_data_array(0 to c_last_step);
  signal s_d_mul_atan : t_z_array(0 to c_last_step);
  
--  signal r_x : t_data_array(1 to gen_step_count+1);
--  signal r_y : t_data_array(1 to gen_step_count+1);
--  signal r_z : t_z_array(1 to gen_step_count+1);
--  signal s_d_mul_x : t_data_array(0 to gen_step_count+1);
--  signal s_d_mul_y : t_data_array(0 to gen_step_count+1);
--  signal s_d_mul_atan : t_z_array(0 to gen_step_count+1);
  
begin
  assert gen_step_count <= c_max_steps
    report "gen_step_count may not be bigger than c_max_steps in as_feature_cordic_pkg"
    severity failure;
    
  s_d(0) <= y_in(y_in'left);
  D_I : for i in 1 to c_last_step generate
    s_d(i) <= r_y(i)(r_y(i)'left);
  end generate;
  
  CORDIC_STEPS : for i in 0 to c_last_step generate
     
    STEP_0  : if i = 0 generate
      -- calculate d_i * y_i/x_i/atan(1/2^i):
      s_d_mul_y(i)(c_data_width-1 downto addBits(c_last_step)-addBits(i)) <= 
                            -resize(y_in,gen_input_width+1)
                            when s_d(i) = '0'
                            else resize(y_in,gen_input_width+1);
                            
      s_d_mul_x(i)(c_data_width-1 downto addBits(c_last_step)-addBits(i)) <=
                            -resize(x_in,gen_input_width+1)
                            when s_d(i) = '0'
                            else resize(x_in,gen_input_width+1);
                            
      s_d_mul_atan(i) <=    -c_atan_list(i)
                            when s_d(i) = '0'
                            else c_atan_list(i);
                            
      p_step_i : process(clk)
        -- x(i+1) = x(i) - d(i) * y(i) * 1/2^i
        -- y(i+1) = y(i) + d(i) * y(i) * 1/2^i
        -- z(i+1) = z(i) - d(i) * atan(1/2^i)
        -- the bit width grows with each step. the unused bits of lower steps are left unasigned
        constant c_this_data_width : natural := gen_input_width+1+addBits(i); -- bitwidth required for step i
        constant c_next_data_width : natural := gen_input_width+1+addBits(i+1); -- bitwidth required for step i+1
        constant c_left       : natural := c_data_width-1;
        constant c_right      : natural := addBits(c_last_step)-addBits(i);
        --constant c_right_next : natural := addBits(c_last_step)-addBits(i+1);
      begin
        if rising_edge(clk) then
          if reset = '1' then
            r_x(i+1)(c_left downto c_right-(i+1)) <= (others => '0');
            r_y(i+1)(c_left downto c_right-(i+1)) <= (others => '0');
            r_z(i+1) <= (others => '0');
          else
              if strobe_in = '1' then
                r_x(i+1)(c_left downto c_right-(i+1)) <= resize(x_in,c_next_data_width) - resize(s_d_mul_y(i)(c_left downto c_right),c_next_data_width); -- step 0: 1/2^i = 1 => no shift operation required
                r_y(i+1)(c_left downto c_right-(i+1)) <= resize(y_in,c_next_data_width) + resize(s_d_mul_x(i)(c_left downto c_right),c_next_data_width);
                r_z(i+1) <= -s_d_mul_atan(i);
              end if;
          end if;
        end if;
      end process;
    end generate;
    
    STEP_i : if i > 0 and i < c_last_step generate
      -- calculate d_i * y_i/x_i/atan(1/2^i):
      s_d_mul_y(i)(c_data_width-1 downto addBits(c_last_step)-addBits(i)) <=
                            -r_y(i)(c_data_width-1 downto addBits(c_last_step)-addBits(i))
                            when s_d(i) = '0'
                            else r_y(i)(c_data_width-1 downto addBits(c_last_step)-addBits(i));
                            
      s_d_mul_x(i)(c_data_width-1 downto addBits(c_last_step)-addBits(i)) <=
                            -r_x(i)(c_data_width-1 downto addBits(c_last_step)-addBits(i))
                            when s_d(i) = '0'
                            else r_x(i)(c_data_width-1 downto addBits(c_last_step)-addBits(i));
                            
      s_d_mul_atan(i) <=    -c_atan_list(i) 
                            when s_d(i) = '0'
                            else c_atan_list(i);
    end generate;
    STEP_i_process : if i > 0 and i < c_last_step-1 generate
      p_step_i : process(clk)
        -- x(i+1) = x(i) - d(i) * y(i) * 1/2^i
        -- y(i+1) = y(i) + d(i) * y(i) * 1/2^i
        -- z(i+1) = z(i) - d(i) * atan(1/2^i)
        -- the bit width grows with each step. the unused bits of lower steps are left unasigned
        constant c_this_data_width : natural := gen_input_width+1+addBits(i); -- bitwidth required for step i
        constant c_next_data_width : natural := gen_input_width+1+addBits(i+1); -- bitwidth required for step i+1
        constant c_left       : natural := c_data_width-1;
        constant c_right      : natural := addBits(c_last_step)-addBits(i);
        --constant c_right_next : natural := addBits(c_last_step)-addBits(i+1);
      begin
        if rising_edge(clk) then
          if reset = '1' then
              r_x(i+1)(c_left downto c_right-(i+1)) <= (others => '0');
              r_y(i+1)(c_left downto c_right-(i+1)) <= (others => '0');
              r_z(i+1) <= (others => '0');
          else
              if strobe_in = '1' then
                  r_x(i+1)(c_left downto c_right-(i+1)) <= 
                                  shift_left(resize(r_x(i)(c_left downto c_right),c_next_data_width),i) -- this appends i zeros to the end of the valid bits of r_x(i) 
                                  -- example: i = 3: xxxx xxxx.xxx => resize => xxx xxxx xxxx.xxx => left shift => xxx xxxx x.xxx 000
                                  - shift_right(s_d_mul_y(i)(c_left downto c_right-i),i); -- this divides by 2^i
                                  -- example: i = 3: xxxx xxxx.xxxU UU => shift right => 111or000 xxxx xxxx.xxxx xx
                r_y(i+1)(c_left downto c_right-(i+1)) <= 
                                  shift_left(resize(r_y(i)(c_left downto c_right),c_next_data_width),i) -- this appends i zeros to the end of the valid bits of r_x(i) 
                                  + shift_right(s_d_mul_x(i)(c_left downto c_right-i),i); -- this divides by 2^i
                r_z(i+1) <= r_z(i)-s_d_mul_atan(i);
              end if;
          end if;
        end if;
      end process;
    end generate;
    
    STEP_i_pre_last : if i = c_last_step-1 generate
      p_step_i : process(clk)
        -- x(i+1) = x(i) - d(i) * y(i) * 1/2^i
        -- y(i+1) = y(i) + d(i) * y(i) * 1/2^i
        -- z(i+1) = z(i) - d(i) * atan(1/2^i)
        -- the bit width grows with each step. the unused bits of lower steps are left unasigned
        constant c_this_data_width : natural := gen_input_width+1+addBits(i); -- bitwidth required for step i
        constant c_next_data_width : natural := gen_input_width+1+addBits(i+1); -- bitwidth required for step i+1
        constant c_left       : natural := c_data_width-1;
        constant c_right      : natural := addBits(c_last_step)-addBits(i);
        --constant c_right_next : natural := addBits(c_last_step)-addBits(i+1);
      begin
        if rising_edge(clk) then
          if reset = '1' then
              r_y(i+1)(c_left downto c_right-(i+1)) <= (others => '0');
              r_z(i+1) <= (others => '0');
          else
              if strobe_in = '1' then
                r_y(i+1)(c_left downto c_right-(i+1)) <= 
                                  shift_left(resize(r_y(i)(c_left downto c_right),c_next_data_width),i) -- this appends i zeros to the end of the valid bits of r_x(i) 
                                  + shift_right(s_d_mul_x(i)(c_left downto c_right-i),i); -- this divides by 2^i
                r_z(i+1) <= r_z(i)-s_d_mul_atan(i);
              end if;
          end if;
        end if;
      end process;
    end generate;

    STEP_LAST : if i = c_last_step generate
      s_d_mul_y(i)(c_data_width-1 downto addBits(c_last_step)-addBits(i)) <=
                            -r_y(i)(c_data_width-1 downto addBits(c_last_step)-addBits(i))
                            when s_d(i) = '0'
                            else r_y(i)(c_data_width-1 downto addBits(c_last_step)-addBits(i));
      s_d_mul_atan(i) <=    -c_atan_list(i) 
                            when s_d(i) = '0'
                            else c_atan_list(i);
      p_step_i : process(clk)
        -- x(i+1) = x(i) - d(i) * y(i) * 1/2^i
        -- y(i+1) = y(i) + d(i) * y(i) * 1/2^i
        -- z(i+1) = z(i) - d(i) * atan(1/2^i)
        -- the bit width grows with each step. the unused bits of lower steps are left unasigned
        constant c_this_data_width : natural := gen_input_width+1+addBits(i); -- bitwidth required for step i
        constant c_next_data_width : natural := gen_input_width+1+addBits(i+1); -- bitwidth required for step i+1
        constant c_left       : natural := c_data_width-1;
        constant c_right      : natural := addBits(c_last_step)-addBits(i);
        --constant c_right_next : natural := addBits(c_last_step)-addBits(i+1);
      begin
        if rising_edge(clk) then
          if reset = '1' then
            z_out <= (others => '0');
          else
              if strobe_in = '1' then
                z_out <= r_z(i)-s_d_mul_atan(i);
              end if;
          end if;
        end if;
      end process; 
    end generate;
  end generate;
--    p_step_i : process(clk)
--      -- x(i+1) = x(i) - d(i) * y(i) * 1/2^i
--      -- y(i+1) = y(i) + d(i) * y(i) * 1/2^i
--      -- z(i+1) = z(i) - atan(1/2^i)
--      -- the bit width grows with each step. the unused bits of lower steps are left unasigned
--      --constant c_this_data_width : natural := gen_input_width+1+addBits(i); -- bitwidth required for step i
--      --constant c_next_data_width : natural := gen_input_width+1+addBits(i+1); -- bitwidth required for step i+1
--      constant c_left       : natural := c_data_width-1;
--      --constant c_right      : natural := addBits(c_last_step)-addBits(i);
--      --constant c_right_next : natural := addBits(c_last_step)-addBits(i+1);
--    begin
--      if rising_edge(clk) then
--        if reset = '1' then
--          for i in 0 to c_last_step-2 loop
--            r_x(i+1)(c_left downto addBits(c_last_step)-addBits(i+1)) <= (others => '0');
--          end loop;
--          for i in 0 to c_last_step-1 loop
--            r_y(i+1)(c_left downto addBits(c_last_step)-addBits(i+1)) <= (others => '0');
--            r_z(i+1) <= (others => '0');
--            r_strobe(i+1) <= '0';
--          end loop;
--          
--          strobe_out <= '0';
--          z_out <= (others => '0');
--        
--        else
--        
--          -- FIRST STEP
--          r_strobe(0+1) <= strobe_in;
--          if strobe_in = '1' then
--            r_x(0+1)(c_left downto addBits(c_last_step)-addBits(1)) <= resize(x_in,gen_input_width+1+addBits(0+1)) -- step 0: 1/2^i = 1 => no shift operation required
--                                                                             - resize(s_d_mul_y(0)(c_left downto addBits(c_last_step)-addBits(0)),gen_input_width+1+addBits(0+1)); 
--            r_y(0+1)(c_left downto addBits(c_last_step)-addBits(1)) <= resize(y_in,gen_input_width+1+addBits(0+1)) 
--                                                                             + resize(s_d_mul_x(0)(c_left downto addBits(c_last_step)-addBits(0)),gen_input_width+1+addBits(0+1));
--            r_z(0+1) <= -s_d_mul_atan(0);
--          end if;
--          -- SECOND STEP TO 2 bevor LAST STEP
--          for i in 1 to c_last_step-2 loop
--            r_strobe(i+1) <= r_strobe(i);
--            if r_strobe(i) = '1' then
--            
----                r_x(i+1)(c_left downto c_right-(i+1)) <= 
----                                  shift_left(resize(r_x(i)(c_left downto c_right),c_next_data_width),i) -- this appends i zeros to the end of the valid bits of r_x(i) 
----                                  -- example: i = 3: xxxx xxxx.xxx => resize => xxx xxxx xxxx.xxx => left shift => xxx xxxx x.xxx 000
----                                  - shift_right(s_d_mul_y(i)(c_left downto c_right-i),i); -- this divides by 2^i
----                                  -- example: i = 3: xxxx xxxx.xxxU UU => shift right => 111or000 xxxx xxxx.xxxx xx
----                r_y(i+1)(c_left downto c_right-(i+1)) <= 
----                                  shift_left(resize(r_y(i)(c_left downto c_right),c_next_data_width),i) -- this appends i zeros to the end of the valid bits of r_x(i) 
----                                  + shift_right(s_d_mul_x(i)(c_left downto c_right-i),i); -- this divides by 2^i
----                r_z(i+1) <= r_z(i)-s_d_mul_atan(i);
--              s_d_mul_x2(i+1)(c_left downto addBits(c_last_step)-addBits(i+1)) <= s_d_mul_y(i)(c_left)&shift_right(s_d_mul_y(i)(c_left downto addBits(c_last_step)-(addBits(i)+i)),i);
--              r_x(i+1)(c_left downto addBits(c_last_step)-addBits(i+1)) <= 
--                                shift_left(resize(r_x(i)(c_left downto addBits(c_last_step)-addBits(i)),gen_input_width+1+addBits(i+1)),i+1) -- this appends i zeros to the end of the valid bits of r_x(i) 
--                                -- example: i = 3: xxxx xxxx.xxx => resize => xxx xxxx xxxx.xxx => left shift => xxx xxxx x.xxx 000
--                                - shift_right(s_d_mul_y(i)(c_left downto addBits(c_last_step)-(addBits(i)+i)),i); -- this divides by 2^i
--                                -- example: i = 3: xxxx xxxx.xxxU UU => shift right => 111or000 xxxx xxxx.xxxx xx
--
--              r_y(i+1)(c_left downto addBits(c_last_step)-addBits(i+1)) <= 
--                                shift_left(resize(r_y(i)(c_left downto addBits(c_last_step)-addBits(i)),gen_input_width+1+addBits(i+1)),i+1) -- this appends i zeros to the end of the valid bits of r_x(i) 
--                                + shift_right(s_d_mul_x(i)(c_left downto addBits(c_last_step)-(addBits(i)+i)),i); -- this divides by 2^i
--                                
--              r_z(i+1) <= r_z(i)-s_d_mul_atan(i);
--            end if;
--          end loop;
--          -- STEP 1 bevor LAST STEP
--          r_strobe(c_last_step) <= r_strobe(c_last_step-1);
--          r_y(c_last_step)(c_left downto addBits(c_last_step)-addBits(c_last_step)) <= 
--                        shift_left(resize(r_y(c_last_step-1)(c_left downto addBits(c_last_step)-addBits(c_last_step-1)),gen_input_width+1+addBits(c_last_step)),(c_last_step-1)) -- this appends i zeros to the end of the valid bits of r_x(i) 
--                        + shift_right(s_d_mul_x(c_last_step-1)(c_left downto addBits(c_last_step)-addBits(c_last_step-1)),(c_last_step-1)); -- this divides by 2^i
--                                
--          r_z(c_last_step) <= r_z(c_last_step-1)-s_d_mul_atan(c_last_step-1);
--          -- LAST STEP
--          strobe_out <= r_strobe(c_last_step);
--          z_out <= r_z(c_last_step)-s_d_mul_atan(c_last_step);
--          
--        end if;
--      end if;
--    end process;
end rtl;

