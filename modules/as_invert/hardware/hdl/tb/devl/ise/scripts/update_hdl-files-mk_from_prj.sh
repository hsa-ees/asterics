#!/bin/bash

PRJ_FILE=ise/asterics_sim_top_isim_beh.prj
HDL_FILE=hdl/hdl_files.mk

HDL_FILES_SED=$( awk -F " " '{print $3;}' ${PRJ_FILE} | tr '\n' '#' | tr -d '"' | sed 's/\.\.\///g' | sed 's/#/ /g' | sed 's/\//\\\//g')
SED_CMD=(-i "s/HDL_FILES=.*/HDL_FILES=${HDL_FILES_SED}/g")
sed "${SED_CMD[@]}" $HDL_FILE

echo "Updated '${HDL_FILE}' according to entries in '${PRJ_FILE}'."
