# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_logging.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
This module sets up Pythons logging module for as_automatics.
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
# @file as_automatics_logging.py
# @author Philip Manke
# @brief This module sets up Pythons logging module for as_automatics.
# -----------------------------------------------------------------------------

import logging


def init_log(
    logfilename: str = "as_automatics.log",
    *,
    loglevel_console="WARNING",
    loglevel_file="INFO"
):
    """Initialize logging and return the logger.
       Should only be run once per kernel."""
    # Setup logging
    logger = logging.getLogger("as_automatics")

    ll_console = getattr(logging, loglevel_console, logging.INFO)
    ll_file = getattr(logging, loglevel_file, logging.INFO)

    logger.setLevel(min((ll_console, ll_file)))
    logger.disabled = False

    # Make sure only the handlers we want are instantiated
    # (Not sure if this is a particularly 'neat' implementation...)
    if logger.hasHandlers():
        # "Nuke" all references to old handlers
        logger.handlers.clear()

    # Set format for log entries
    formatter_logfile = logging.Formatter(
        "%(asctime)s, %(module)s: %(levelname)s - %(message)s"
    )
    formatter_console = logging.Formatter("Automatics %(levelname)s: %(message)s")

    # Setup logfile log handler
    logfile = logging.FileHandler(logfilename)
    logfile.setLevel(ll_file)
    logfile.setFormatter(formatter_logfile)
    logger.addHandler(logfile)

    # Setup console log handler
    logstream = logging.StreamHandler()
    logstream.setLevel(ll_console)
    logstream.setFormatter(formatter_console)
    logger.addHandler(logstream)
    return logger


def get_log():
    """Returns the logger, initializing it if necessary."""
    logger = logging.getLogger("as_automatics")
    if logger.hasHandlers():
        return logger
    return init_log()


LOGLEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


def set_loglevel(console, logfile):
    console = console.upper()
    logfile = logfile.upper()
    if console in LOGLEVELS and logfile in LOGLEVELS:
        init_log(loglevel_console=console, loglevel_file=logfile)
    else:
        print("Invalid loglevels! - {}, {}".format(console, logfile))
