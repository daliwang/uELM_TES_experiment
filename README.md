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
- TNdemo (example): `/gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/uELM_TES_experiment/aoi_experiment_config.example.json`
- Helene: `/gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/uELM_TES_experiment/aoi_helene_config.json`

Ensure the following fields are correct for your run: `expid`, `experiment_root`, `aoi_points.dir/file`, `source.base_domain_file`, `source.surfdata_dir`, `source.surfdata_file`, `source.forcing_dir`, `scheduler`, `e3sm`.

3) Prepare an experiment directory (generates wrappers)
```bash
python3 /gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/uELM_TES_experiment/aoi_prepare_experiment.py \
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
python3 /gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/uELM_TES_experiment/aoi_prepare_experiment.py \
  --config /gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/uELM_TES_experiment/aoi_experiment_config.example.json

# 3) Run domain and surfdata
cd /gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/uELM_TES_experiment/TNdemo/scripts
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
- Domain/Surfdata: `/gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/uELM_TES_experiment/TNdemo/domain_surfdata/`
- Forcing: `/gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/uELM_TES_experiment/TNdemo/forcing/`
- Model links: `/gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/uELM_TES_experiment/TNdemo/atm_forcing.datm7.km.1d/`

Workflow: Helene
Use the provided Helene config; the experiment directory will be created.

```bash
# 1) Environment
source activate /path/to/my_env

# 2) Prepare experiment
python3 /gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/uELM_TES_experiment/aoi_prepare_experiment.py \
  --config /gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/uELM_TES_experiment/aoi_helene_config.json

# 3) Run domain and surfdata  (1-2 minutes)
cd /gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/uELM_TES_experiment/helene/scripts
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

