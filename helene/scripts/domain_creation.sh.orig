# Domain data generation

#!/bin/bash

kiloCraft='/gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/'

TES_inputGEN_path=${kiloCraft}/TES_inputGEN/TES_AOI_scripts/

TES_domain_path=${kiloCraft}/TES_cases_data/Daymet_ERA5_TESSFA2/entire_domain/domain_surfdata/

TES_domain="domain.lnd.TES_SE.4km.1d.c240827.nc"

AOI_case_name="TN"

output_path=${kiloCraft}/TES_cases_data/Daymet_ERA5_TESSFA2/${AOI_case_name}/domain_surfdata/

cd ${TES_inputGEN_path}

AOI_case_date=241127
# create gridIDs 
#echo ${TES_domain_path}  ${output_path}  ${AOI_case_name}
#python3 TES_subdomain.py  ${TES_domain_path}  ${output_path}  ${AOI_case_name}

# create domain files

AOI_gridID_file=${AOI_case_name}_gridID.c${AOI_case_date}.nc
AOI_domain_output_path=${kiloCraft}/TES_cases_data/Daymet_ERA5_TESSFA2/${AOI_case_name}/domain_surfdata/
#AOI_gridfile_path=${output_path}
#AOI_domain_output_path=${output_path}

echo "python3 TES_AOI_domainGEN.py" ${TES_domain_path} ${AOI_domain_output_path} ${AOI_gridID_file}
python3 TES_AOI_domainGEN.py ${TES_domain_path} ${AOI_domain_output_path} ${AOI_gridID_file}
