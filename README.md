lsTES AOI Input Generator

Purpose
- Prepare domain, surfdata, and forcing subsets for a user-defined Area Of Interest (AOI) for TES/uELM workflows.

Key features
- One-shot experiment preparation using a config JSON.
- Re-runnable generation scripts with exported environment variables.
- Forcing generation supports MPI (mpi4py); default tasks can be overridden via env.

Quickstart (CADES)
1) Set up and activate the Python environment (CADES)
```bash    (add source /sw/baseline/nsp/init/profile  in .bashrc)
module load miniforge3
conda create -p /path/to/my_env python=3.11   (e.g. /gpfs/wolf2/cades/cli185/proj-shared/wangd/my_env)
source activate /path/to/my_env

# If you prefer to install packages now
conda install -c conda-forge netcdf4 numpy pandas scipy pyproj mpi4py
```
Optional alternatives:
```bash
# If you want to source an existing python env for kiloCraft on baseline
# add the following commands into your .bashrc 

#  use the new default software stack
source /sw/baseline/nsp/init/profile

#  use this command wisely, as it will purge all the previous modules
(OPTIONAL) module purge  

# load and activate existing venv for kiloCraft
module load miniforge3
source /gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/python_test_env/activate_shared_env.sh /gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/python_test_env/conda_envs/testvenv miniforge3 

which python; python -V
python -c "import sys; print(sys.executable); import netCDF4; print(netCDF4.__version__)"

export PS1="\[\e]0;\u@\h: \w\a\]\u@\h:\w\$ "
```

2) Use one of the provided configs (edit if needed)
- TNdemo (example): `/gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/tes_aoi_release/aoi_experiment_config.example.json`
- Helene: `/gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/tes_aoi_release/aoi_helene_config.json`

Ensure the following fields are correct for your run: `expid`, `experiment_root`, `aoi_points.dir/file`, `source.base_domain_file`, `source.surfdata_dir`, `source.surfdata_file`, `source.forcing_dir`, `scheduler`, `e3sm`.

3) Prepare an experiment directory (generates wrappers)
```bash
python3 /gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/tes_aoi_release/aoi_prepare_experiment.py \
  --config /path/to/your_config.json
```
Creates: <experiment_root>/{domain_surfdata,forcing,scripts}

Important: Steps 4–7 must be executed from the newly created `scripts` directory.

4) Generate domain and surfdata
```bash
cd <experiment_root>/scripts
source ./export_env.sh
bash run_domain_surfdata.sh
```

5) Generate forcing
- Via Slurm:
```bash
sbatch run_forcing.sbatch
```
- Or run directly (uses `srun` with env overrides):
```bash
sh run_forcing.sbatch
```
Optional overrides before submitting:
```bash
export SCHED_TASKS=2               # MPI ranks for forcing generation
export SCHED_ACCOUNT=CLI185        # Slurm account
export SCHED_PARTITION=batch_ccsi  # Slurm partition
```

6) Create model-facing links (writes `atm_forcing.datm7.km.1d`)
```bash
bash create_links.sh
```

7) (Optional) Create a uELM accelerated spinup case
```bash
bash create_uELM_adspin.sh
```
This script auto-discovers the latest domain/surfdata files.

Notes
- The generated `run_forcing.sbatch` infers `<experiment_root>` relative to the repository root; run it from the prepared layout. If your repo is not a git checkout, set `EXP_ROOT` in the environment before running.
- Input data paths under `source.*` must be readable from CADES.

Workflow: TNdemo
Use the provided example config as-is (paths are already set for CADES) or adjust to your project.

```bash
# 1) Environment
source activate /path/to/my_env

# 2) Prepare experiment
python3 /gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/tes_aoi_release/aoi_prepare_experiment.py \
  --config /gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/tes_aoi_release/aoi_experiment_config.example.json

# 3) Run domain and surfdata
cd /gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/tes_aoi_release/TNdemo/scripts
source ./export_env.sh
bash run_domain_surfdata.sh

# 4) Generate forcing (Slurm)  (Takes upto 90 minutes for TNdemo case)
sbatch run_forcing.sbatch

# 5) Create model links
bash create_links.sh

# 6) (Optional) Create uELM adspin case
bash create_uELM_adspin.sh
```

Outputs
- Domain/Surfdata: `/gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/tes_aoi_release/TNdemo/domain_surfdata/`
- Forcing: `/gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/tes_aoi_release/TNdemo/forcing/`
- Model links: `/gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/tes_aoi_release/TNdemo/atm_forcing.datm7.km.1d/`

Workflow: Helene
Use the provided Helene config; the experiment directory will be created.

```bash
# 1) Environment
source activate /path/to/my_env

# 2) Prepare experiment
python3 /gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/tes_aoi_release/aoi_prepare_experiment.py \
  --config /gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/tes_aoi_release/aoi_helene_config.json

# 3) Run domain and surfdata  (1-2 minutes)
cd /gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/tes_aoi_release/helene/scripts
source ./export_env.sh
bash run_domain_surfdata.sh

# 4) Generate forcing (Slurm) (around 75 minutes for ERA5 with 1500 files with 4 MPI processes)
sbatch run_forcing.sbatch

# 5) Create model links
bash create_links.sh

# 6) (Optional) Create uELM adspin case
bash create_uELM_adspin.sh
```

Config reference (brief)
- `expid`: experiment ID; should match the prefix of AOI files.
- `experiment_root`: destination for outputs (absolute path recommended).
- `aoi_points`: `{dir, file}` path to AOI grid IDs (`.csv`) or AOI domain (`.nc`).
- `source`: `{base_domain_file, surfdata_dir, surfdata_file, forcing_dir}` full paths to source data.
- `scheduler`: Slurm defaults; consumed by `run_forcing.sbatch` and wrappers. Override at submit time with `SCHED_*` env vars.
- `e3sm`: `{din_root, src_root, mach, compiler, mpilib, compset}` used by `create_uELM_adspin.sh`.

Environment
- See `env/environment.yml` for dependencies (`python=3.11`, `netcdf4`, `numpy`, `pandas`, `scipy`, `pyproj`, `mpi4py`).

License
- MIT (see `LICENSE`)

---

# Knox AOI Workflow: Creating kmELM Cases and Spinup

This README guides you through creating kmELM cases and performing accelerated spinup (adspin) and final spinup using the `tes_aoi_release` repository. All case creation and spinup operations are performed within the `tes_aoi_release` directory structure.

## Overview

This workflow consists of three main phases:
1. **AOI Data Preparation**: Prepare domain, surfdata, and forcing data for your AOI
2. **Accelerated Spinup**: Create and run the uELM accelerated spinup case
3. **Final Spinup**: Create and run the final spinup case (optionally using AI-adjusted restart files from LandSim)

## Phase 1: AOI Data Preparation

### Step 0. Update the config

Edit `aoi_knox_config.json` before running anything:
- Line 9 `experiment_root`: change to **your** desired output folder.
- Line 10/11 `aoi_points.dir`: change to the directory that contains `knox_xcyc.csv` under your path.

Example:
```json
"experiment_root": "/gpfs/.../yourname/tes_aoi_release/knox",
"aoi_points": {
  "dir": "/gpfs/.../yourname/tes_aoi_release",
  "file": "knox_xcyc.csv"
}
```

### Step 1. Prepare the experiment layout

```bash
cd tes_aoi_release
python aoi_prepare_experiment.py --config aoi_knox_config.json
```

Creates `knox/domain_surfdata`, `knox/forcing`, and `knox/scripts/` with helper scripts.

### Step 2. Build domain & surfdata for the point

```bash
cd knox/scripts
source export_env.sh
bash run_domain_surfdata.sh
```

Outputs single-point domain/surfdata files in `knox/domain_surfdata/`.

### Step 3. Subset forcing data

```bash
sbatch run_forcing.sbatch        # preferred on Slurm
# or: sh run_forcing.sbatch      # run interactively (uses srun inside)
```

Results appear in `knox/forcing/` (three subfolders).

### Step 4. Create model-facing links

```bash
bash create_links.sh
```

Generates `knox/atm_forcing.datm7.km.1d/` with symlinks that match E3SM expectations.

## Phase 2: Accelerated Spinup (Adspin)

### Step 1. Generate uELM accelerated spinup case

1. Edit `knox/scripts/create_uELM_adspin.sh` so the paths at the top point to **your** installs. The script honours the environment variables `KILOCRAFT_ROOT` and `KMELM_ROOT`. Set them or edit the file (line 8) before running.

   ```bash
   export KMELM_ROOT=/gpfs/.../yourname/kmELM
   export KILOCRAFT_ROOT=/gpfs/.../yourname/kiloCraft
   ```

2. Generate the case skeleton:

   ```bash
   cd knox/scripts
   bash create_uELM_adspin.sh
   ```

   This script creates the uELM case under `${KMELM_ROOT}/e3sm_cases/` using the domain, surfdata, and forcing data prepared in Phase 1.

3. Enter the new case directory and submit it:

   ```bash
   cd "${KMELM_ROOT}/e3sm_cases/uELM_knox_*"
   ./case.submit
   ```

   The case will run and produce history (`*.elm.h0.*.nc`) and restart (`*.elm.r.*.nc`) files in `${KMELM_ROOT}/e3sm_runs/uELM_knox_*/`.

### Step 2. Locate outputs for LandSim integration

After the accelerated spinup completes, you'll need the following outputs for LandSim inference (see LandSim README for details):

- **Domain and surfdata files**: Located in `knox/domain_surfdata/`
  - `knox_domain.lnd.TES_SE.4km.1d.c*.nc`
  - `knox_surfdata.TES_SE.4km.1d.NLCD.c*.nc`

- **Forcing data**: Located in `knox/forcing/` (three subfolders)

- **Model outputs**: The latest run directory under `${KMELM_ROOT}/e3sm_runs/` contains:
  - History files: `*.elm.h0.*.nc`
  - Restart files: `*.elm.r.*.nc`

These files will be used as inputs for LandSim's training data generation and inference workflow (see LandSim documentation).

## Phase 3: Final Spinup

### Step 1. Prepare AI-adjusted restart file (optional)

If you've used LandSim to generate an AI-adjusted restart file, you can use it for the final spinup. The restart file should be generated using LandSim's workflow (see LandSim README for details).

Set the path to your AI restart file:

```bash
export AI_RESTART_FILE=/path/to/LandSim/cnp_inference_knox_initial/uELM_knox_AIrestart.elm.r.0021-01-01-00000.nc
```

If you prefer to use the original restart from accelerated spinup, you can skip this step and the script will use the default restart.

### Step 2. Create the final spinup case

1. Regenerate the final-spinup case. The script honours the `AI_RESTART_FILE` environment variable if set:

   ```bash
   cd /gpfs/.../tes_aoi_release/knox/scripts
   AI_RESTART_FILE=/path/to/LandSim/cnp_inference_knox_initial/uELM_knox_AIrestart.elm.r.0021-01-01-00000.nc \
     bash create_uELM_finalspin.sh
   ```

   Or without AI restart (uses original restart):

   ```bash
   cd /gpfs/.../tes_aoi_release/knox/scripts
   bash create_uELM_finalspin.sh
   ```

2. Enter the new case directory and submit:

   ```bash
   cd "${KMELM_ROOT}/e3sm_cases/uELM_knox_*_finalspin"
   ./case.submit
   ```

   (Adjust the wildcard if your case name differs.)

