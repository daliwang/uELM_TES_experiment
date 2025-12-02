#!/bin/bash
#SBATCH -A CLI185
#SBATCH -J TES_TN_forcingGEN
#SBATCH -p batch_ccsi
#SBATCH -N 1
#SBATCH -t 24:00:00
#SBATCH --mem=500GB


module load python/3.11-anaconda3
source activate /ccsopen/home/wangd/compEnv

TES_AOI_scripts=/gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/TES_inputGEN/TES_AOI_scripts
cd $TES_AOI_scripts

date_string=$(date +'%y%m%d-%H%M')

EXPID=TN
Daymet_ERA5_TESSFA2_ROOT=/gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/TES_cases_data/Daymet_ERA5_TESSFA2/
TES_forcing_path=$Daymet_ERA5_TESSFA2_ROOT/entire_domain/forcing

output_path=$Daymet_ERA5_TESSFA2_ROOT/${EXPID}/forcing/
echo ${output_path}
rm -rf ${output_path}
mkdir ${output_path}

AOI_file_path=$Daymet_ERA5_TESSFA2_ROOT/${EXPID}/domain_surfdata/ 
AOI_points_file=${EXPID}_domain.lnd.TES_SE.4km.1d.c241127.nc


#if len(sys.argv) != 5  or sys.argv[1] == '--help':  # sys.argv includes the script name as the first argument
#    print("Example use: python AOI_forcingGEN.py <input_path> <output_path> <AOI_gridID_path> <AOI_points_file>")
#    print(" <input_path>: path to the 1D source data directory")
#    print(" <output_path>:  path for the 1D AOI forcing data directory")
#    print(" <AOI_gridID_path>:  path to the AOI_gridID_file")
#    print(" <AOI_gridID_file>:  <AOI>_gridID.csv or <AOI>_domain.nc")
#    print(" The code uses TES forcing to generation 1D AOI forcing")              
#    exit(0)

TES_AOI_local_scripts=$Daymet_ERA5_TESSFA2_ROOT/${EXPID}/scripts
cd $TES_AOI_local_scripts

echo "python3 TES_AOI_forcingGEN.py" ${TES_forcing_path}/Precip3Hrly ${output_path} ${AOI_file_path} ${AOI_points_file} >& ${output_path}${EXPID}_forcinggen.log.${date_string}
srun -n 1 python3 TES_AOI_forcingGEN.py ${TES_forcing_path} ${output_path} ${AOI_file_path} ${AOI_points_file} >& ${output_path}${EXPID}_forcinggen.log.${date_string}


