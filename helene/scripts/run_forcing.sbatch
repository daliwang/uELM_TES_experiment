#!/bin/bash
#SBATCH -A CLI185
#SBATCH -J TES_helene_forcingGEN
#SBATCH -p batch_ccsi
#SBATCH -N 1
#SBATCH -t 6:00:00
#SBATCH --mem=500GB

set -euo pipefail

# Source exported environment if present
if [ -f ./export_env.sh ]; then . ./export_env.sh; fi
EXP_ROOT="/gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/uELM_TES_experiment/helene"
SCRIPT_DIR="/gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/uELM_TES_experiment/helene/scripts"
echo "EXP_ROOT: ${EXP_ROOT}"
cd "${SCRIPT_DIR}"

date_string=$(date +'%y%m%d-%H%M')
: "${EXPID:=helene}"
: "${FORCING_DIR:=/gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/TES_cases_data/Daymet_ERA5_TESSFA2/entire_domain/forcing}"
OUT_DIR="${EXP_ROOT}/forcing"
mkdir -p "${OUT_DIR}"

# Locate the latest AOI domain to derive gridIDs
AOI_FILE_PATH="${EXP_ROOT}/domain_surfdata"
AOI_POINTS_FILE=$(ls -1 ${AOI_FILE_PATH}/*_domain.lnd.TES_SE.4km.1d.c*.nc 2>/dev/null | sort | tail -n1 | xargs -r basename)
if [ -z "${AOI_POINTS_FILE}" ]; then echo 'ERROR: AOI domain file not found'; exit 2; fi

# If not running inside a Slurm allocation, run with srun using env SCHED_* overrides
if [ -z "${SLURM_JOB_ID:-}" ]; then
  ACCOUNT="${SCHED_ACCOUNT:-CLI185}"
  PARTITION="${SCHED_PARTITION:-batch_ccsi}"
  NODES="${SCHED_NODES:-1}"
  TIME="${SCHED_TIME:-6:00:00}"
  MEM="${SCHED_MEM:-500GB}"
  SRUN_NTASKS="${SCHED_TASKS:-2}"
  echo "srun -A '${ACCOUNT}' -p '${PARTITION}' -N '${NODES}' -t '${TIME}' --mem='${MEM}' -n '${SRUN_NTASKS}' python3 TES_AOI_forcingGEN_mpi.py '${FORCING_DIR}' '${OUT_DIR}' '${AOI_FILE_PATH}/' '${AOI_POINTS_FILE}'" | tee "${OUT_DIR}/${EXPID}_forcinggen.cmd.${date_string}"
  exec srun -A "${ACCOUNT}" -p "${PARTITION}" -N "${NODES}" -t "${TIME}" --mem="${MEM}" -n "${SRUN_NTASKS}" python3 TES_AOI_forcingGEN_mpi.py "${FORCING_DIR}" "${OUT_DIR}" "${AOI_FILE_PATH}/" "${AOI_POINTS_FILE}" 2>&1 | tee "${OUT_DIR}/${EXPID}_forcinggen.log.${date_string}"
fi

# Running under Slurm allocation
echo "srun -n '${SCHED_TASKS}' python3 TES_AOI_forcingGEN_mpi.py '${FORCING_DIR}' '${OUT_DIR}' '${AOI_FILE_PATH}/' '${AOI_POINTS_FILE}'" | tee "${OUT_DIR}/${EXPID}_forcinggen.cmd.${date_string}"
srun -n "${SCHED_TASKS:-2}" python3 TES_AOI_forcingGEN_mpi.py "${FORCING_DIR}" "${OUT_DIR}" "${AOI_FILE_PATH}/" "${AOI_POINTS_FILE}" 2>&1 | tee "${OUT_DIR}/${EXPID}_forcinggen.log.${date_string}"
