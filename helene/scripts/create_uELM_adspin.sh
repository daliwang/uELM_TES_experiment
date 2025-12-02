#!/bin/bash
set -e

KILOCRAFT_ROOT="/gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/"
KMELM_ROOT="/gpfs/wolf2/cades/cli185/proj-shared/wangd/kmELM/"
KMELM_CASE_ROOT="${KMELM_ROOT}/e3sm_cases/"
KMELM_RUN_ROOT="${KMELM_ROOT}/e3sm_runs/"
E3SM_SRC_ROOT="${KMELM_ROOT}/E3SM/"
E3SM_DIN="//gpfs/wolf2/cades/cli185/world-shared/e3sm"

TES_DATA_ROOT="$KILOCRAFT_ROOT/TES_cases_data/"
TES_DOMAIN_FORCING_GROUP_ID="Daymet_ERA5_TESSFA2"
TES_DATA_GROUP_ID="TES_SE"

EXPID="helene"
CASE_COMPSET="I1850uELMTESCNPRDCTCBC"

CASEDIR="$KMELM_CASE_ROOT/${TES_DOMAIN_FORCING_GROUP_ID}/uELM_${EXPID}_${CASE_COMPSET}"
CASE_DATA="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"

DOMAIN_FILE=$(ls -1 ${CASE_DATA}/domain_surfdata/${EXPID}_domain.lnd.${TES_DATA_GROUP_ID}.4km.1d.c*.nc 2>/dev/null | sort | tail -n1 | xargs -r basename)
if [ -z "${DOMAIN_FILE}" ]; then echo 'ERROR: Domain file not found'; exit 2; fi
SURFDATA_FILE=$(ls -1 ${CASE_DATA}/domain_surfdata/${EXPID}_surfdata.${TES_DATA_GROUP_ID}.4km.1d.NLCD.c*.nc 2>/dev/null | sort | tail -n1 | xargs -r basename)
if [ -z "${SURFDATA_FILE}" ]; then echo 'ERROR: Surfdata file not found'; exit 2; fi

rm -rf "${CASEDIR}"

${E3SM_SRC_ROOT}/cime/scripts/create_newcase --case "${CASEDIR}" --mach cades-baseline --compiler gnu --mpilib openmpi --compset "${CASE_COMPSET}" --res ELM_USRDAT  --handle-preexisting-dirs r --srcroot "${E3SM_SRC_ROOT}"

cd "${CASEDIR}"

./xmlchange PIO_TYPENAME="pnetcdf"
./xmlchange PIO_NETCDF_FORMAT="64bit_data"
./xmlchange DIN_LOC_ROOT="${E3SM_DIN}"
./xmlchange DIN_LOC_ROOT_CLMFORC="${CASE_DATA}"
./xmlchange CIME_OUTPUT_ROOT="$KMELM_RUN_ROOT"

./xmlchange DATM_MODE="uELM_TES"
./xmlchange ATM_DOMAIN_PATH="${CASE_DATA}/domain_surfdata/"
./xmlchange ATM_DOMAIN_FILE="${DOMAIN_FILE}"
./xmlchange LND_DOMAIN_PATH="${CASE_DATA}/domain_surfdata/"
./xmlchange LND_DOMAIN_FILE="${DOMAIN_FILE}"

./xmlchange ATM_NCPL="24"
./xmlchange STOP_N="400"
./xmlchange STOP_OPTION="nyears"
./xmlchange DATM_CLMNCEP_YR_START="1980"
./xmlchange DATM_CLMNCEP_YR_END="1999"

./xmlchange ELM_FORCE_COLDSTART="on"
./xmlchange CONTINUE_RUN="FALSE"
./xmlchange ELM_ACCELERATED_SPINUP="on"
./xmlchange  --append ELM_BLDNML_OPTS="-bgc_spinup on"

cat >> user_nl_elm <<EOF
fsurdat = '${CASE_DATA}/domain_surfdata/${SURFDATA_FILE}'
spinup_state = 1
suplphos = 'ALL'
hist_nhtfrq=-175200
hist_mfilt=1
nyears_ad_carbon_only = 25
spinup_mortality_factor = 10
EOF

# Computational resources
./xmlchange NTASKS="1"
./xmlchange NTASKS_PER_INST="1"
./xmlchange MAX_MPITASKS_PER_NODE="1"
./xmlchange JOB_WALLCLOCK_TIME="6:00:00"

./case.setup --reset
./case.setup

./case.build --clean-all
./case.build

