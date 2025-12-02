#!/bin/bash
set -euo pipefail

cd "/gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/uELM_TES_experiment/helene/scripts"
# Source exported environment if present
if [ -f ./export_env.sh ]; then . ./export_env.sh; fi

date_string=$(date +'%y%m%d-%H%M')
: "${EXPID:=helene}"
EXP_ROOT="/gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/uELM_TES_experiment/helene"
SCRIPT_DIR="/gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/uELM_TES_experiment/helene/scripts"
: "${AOI_POINTS_DIR:=/gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/uELM_TES_experiment}"
: "${AOI_POINTS_FILE:=helene_xcyc.csv}"
: "${BASE_DOMAIN_FILE:=/gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/TES_cases_data/Daymet_ERA5_TESSFA2/entire_domain/domain_surfdata/domain.lnd.TES_SE.4km.1d.c240827.nc}"
: "${SURFDATA_DIR:=/gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/TES_cases_data/Daymet_ERA5_TESSFA2/entire_domain/domain_surfdata}"
: "${SURFDATA_FILE:=surfdata.TESSFA_SE.4km.1d.NLCD.c240827.nc}"
DOM_SURF_DIR="${EXP_ROOT}/domain_surfdata"
mkdir -p "${DOM_SURF_DIR}"

# Ensure domain source file is available with expected local name
if [ ! -e domain.lnd.TES_SE.4km.1d.nc ]; then
  ln -sf "${BASE_DOMAIN_FILE}" domain.lnd.TES_SE.4km.1d.nc
fi

echo "[1/2] Generating AOI domain..."
python3 TES_AOI_domainGEN.py "${AOI_POINTS_DIR}" "${DOM_SURF_DIR}" "${AOI_POINTS_FILE}" 2>&1 | tee "${DOM_SURF_DIR}/${EXPID}_domaingen.log.${date_string}"

echo "Resolving latest AOI domain file..."
AOI_PREFIX="$(echo "${AOI_POINTS_FILE}" | awk -F'_' '{print $1}')"
AOI_DOMAIN=$(ls -1 ${DOM_SURF_DIR}/${AOI_PREFIX}_domain.lnd.TES_SE.4km.1d.c*.nc 2>/dev/null | sort | tail -n1)
if [ -z "${AOI_DOMAIN}" ]; then echo 'ERROR: AOI domain file not found'; exit 2; fi

echo "[2/2] Generating AOI surfdata..."
python3 TES_AOI_surfdataGEN.py "${SURFDATA_DIR}" "${SURFDATA_FILE}" "${DOM_SURF_DIR}" "${DOM_SURF_DIR}/" "$(basename "${AOI_DOMAIN}")" 2>&1 | tee "${DOM_SURF_DIR}/${EXPID}_surfdargen.log.${date_string}"

echo 'Domain and surfdata generation complete.'
