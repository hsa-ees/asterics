# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_window_pipeline_spec.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Python module used by as_automatics to build a fake module to store the driver 
location for common window pipeline functions.
"""
# --------------------- LICENSE -----------------------------------------------
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
# or write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# --------------------- DOXYGEN -----------------------------------------------
##
# @file as_gauss_spec.py
# @author Philip Manke
# @brief Specifics for as_window_pipeline used by as_automatics
# -----------------------------------------------------------------------------

from as_automatics_2d_pipeline import As2DWindowPipeline
from as_automatics_module import AsModule


def get_module_instance(module_dir: str) -> AsModule:

    pipe = As2DWindowPipeline(640, 480, "as_window_pipeline_helper", None)
    pipe.add_software_driver_files(
        [
            module_dir + "/software/driver/as_window_pipeline_common.c",
            module_dir + "/software/driver/as_window_pipeline_common.h",
        ]
    )

    pipe.show_in_browser = True
    pipe.dev_status = AsModule.DevStatus.BETA
    pipe.module_type = AsModule.ModuleTypes.HARDWARE_SW_CTRL
    pipe.module_category = "Image Processing Operations"

    pipe.brief_description = "Placeholder module for window pipeline systems. These are automatically generated!"

    return pipe
