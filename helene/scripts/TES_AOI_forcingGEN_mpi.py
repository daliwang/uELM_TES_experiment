
# TES_AOI_forcingGEN_mpi: MPI-parallel (with local multiprocessing fallback) forcing subsetting

import os, sys
import netCDF4 as nc
import numpy as np
import pandas as pd
from time import process_time
from datetime import datetime

# Try MPI first
try:
    from mpi4py import MPI  # type: ignore
    COMM = MPI.COMM_WORLD
    RANK = COMM.Get_rank()
    SIZE = COMM.Get_size()
    USING_MPI = True
except Exception:
    COMM = None
    RANK = 0
    SIZE = 1
    USING_MPI = False

# Local CPU fallback
try:
    from concurrent.futures import ProcessPoolExecutor, as_completed
except Exception:
    ProcessPoolExecutor = None
    as_completed = None


# Get current date
current_date = datetime.now()
formatted_date = current_date.strftime('%y%m%d')


def AOI_forcing_save_1d(input_path, file, AOI, AOI_points, output_path):
    os.makedirs(output_path, exist_ok=True)

    source_file = input_path + '/' + file
    print("Opening source file: ", source_file)
    src = nc.Dataset(source_file, 'r', format='NETCDF3_64BIT')

    grid_ids = src['gridID'][...]  # global gridID array

    AOI_idx = np.where(np.in1d(grid_ids, AOI_points))[0]
    AOI_mask = np.isin(grid_ids, AOI_points)

    dst_name = output_path + '/' + AOI + '_' + file
    print("Generating AOI file: ", dst_name)

    if os.path.exists(dst_name):
        os.remove(dst_name)

    dst = nc.Dataset(dst_name, 'w', format='NETCDF3_64BIT')
    dst.title = dst_name + ' created from ' + source_file + ' on ' + formatted_date

    # Copy global attrs
    for name in src.ncattrs():
        dst.setncattr(name, src.getncattr(name))

    # Copy dimensions (override ni/gridcell to AOI size)
    for name, dimension in src.dimensions.items():
        if name != 'ni' and name != 'gridcell':
            dst.createDimension(name, (len(dimension) if not dimension.isunlimited() else None))
        else:
            dst.createDimension(name, AOI_points.size)

    # Copy variables with subsetting on last dim
    for name, variable in src.variables.items():
        x = dst.createVariable(name, variable.datatype, variable.dimensions)
        print(name, variable.dimensions)

        if name != 'lambert_conformal_conic':
            if (variable.dimensions[-1] != 'ni') and (variable.dimensions[-1] != 'gridcell'):
                dst[name][...] = src[name][...]

            elif len(variable.dimensions) == 2:
                dst[name][...] = src[name][:, AOI_idx]

            elif len(variable.dimensions) == 3:
                d0, d1, d2 = variable.shape
                chunk_size = 16
                num_chunks = d0 // chunk_size + (d0 % chunk_size > 0)
                data_arr = np.empty((d0, d1, AOI_points.shape[1]))

                for chunk in range(num_chunks):
                    start = chunk * chunk_size
                    end = min((chunk + 1) * chunk_size, d0)
                    print(f"Reading source data for chunk {chunk + 1} of {num_chunks}")
                    source_data = src[name][start:end, :, :]

                    print(f"Subsetting source data for chunk {chunk + 1} of {num_chunks}")
                    for i in range(start, end):
                        AOI_data = np.copy(source_data[i - start, AOI_mask])
                        data_arr[i, :, :] = AOI_data[:]

                print("Putting back data into netcdf")
                dst[name][...] = data_arr

        # Copy variable attributes (skip _FillValue to avoid redef warnings)
        for attr_name in variable.ncattrs():
            if attr_name != '_FillValue':
                dst[name].setncattr(attr_name, variable.getncattr(attr_name))

    src.close()
    dst.close()


def _discover_tasks(input_path, output_path):
    tasks = []
    for root, dirs, files in os.walk(input_path):
        for file in files:
            if file.endswith('.nc'):
                new_dir = os.path.join(output_path, os.path.relpath(root, input_path))
                tasks.append((root, file, new_dir))
    return tasks


def _load_aoi_points(aoi_path, aoi_file):
    full = os.path.join(aoi_path, aoi_file)
    if full.endswith('.csv'):
        df = pd.read_csv(full, sep=",", skiprows=1, names=['gridID'])
        return np.array(df['gridID'])
    if full.endswith('.nc'):
        src = nc.Dataset(full, 'r')
        return src['gridID'][:]
    raise RuntimeError('Invalid AOI_points file; must be CSV or NC')


def main():
    args = sys.argv[1:]
    if len(sys.argv) != 5 or sys.argv[1] == '--help':
        print("Example use: python TES_AOI_forcingGEN_mpi.py <input_path> <output_path> <AOI_gridID_path> <AOI_points_file>")
        print(" <input_path>: path to the 1D source data directory")
        print(" <output_path>: path for the 1D AOI forcing data directory")
        print(" <AOI_gridID_path>: path to the AOI gridIDs (csv or domain.nc)")
        print(" <AOI_points_file>: <AOI>_gridID.csv or <AOI>_domain.nc")
        sys.exit(0)

    input_path = args[0]
    if not input_path.endswith("/"): input_path += '/'
    output_path = args[1]
    if not output_path.endswith("/"): output_path += '/'
    aoi_path = args[2]
    if not aoi_path.endswith("/"): aoi_path += '/'
    aoi_file = args[3]
    AOI = aoi_file.split('_')[0]

    AOI_points = _load_aoi_points(aoi_path, aoi_file)

    # Build the task list and distribute
    if USING_MPI and SIZE > 1:
        if RANK == 0:
            tasks = _discover_tasks(input_path, output_path)
        else:
            tasks = None
        tasks = COMM.bcast(tasks, root=0)
        local_tasks = [t for i, t in enumerate(tasks) if (i % SIZE) == RANK]

        start_total = process_time()
        for root, file, new_dir in local_tasks:
            os.makedirs(new_dir, exist_ok=True)
            parts = file.split('.')
            var_name = parts[4] if len(parts) > 4 else ''
            period = parts[5] if len(parts) > 5 else ''
            print(f"[rank {RANK}/{SIZE}] processing {var_name} ({period}) in {file}")
            start = process_time()
            AOI_forcing_save_1d(root, file, AOI, AOI_points, new_dir)
            end = process_time()
            print(f"[rank {RANK}] Done {file} in {end-start:.2f}s")
        end_total = process_time()
        print(f"[rank {RANK}] Finished {len(local_tasks)} files in {end_total-start_total:.2f}s")

    else:
        # Local fallback: default 32 workers (override with FORCING_SERIAL_WORKERS)
        tasks = _discover_tasks(input_path, output_path)
        default_workers = int(os.environ.get('FORCING_SERIAL_WORKERS', '32'))
        if ProcessPoolExecutor is None or default_workers <= 1:
            for root, file, new_dir in tasks:
                os.makedirs(new_dir, exist_ok=True)
                parts = file.split('.')
                var_name = parts[4] if len(parts) > 4 else ''
                period = parts[5] if len(parts) > 5 else ''
                print('processing ' + var_name + '(' + period + ') in the file ' + file)
                start = process_time()
                AOI_forcing_save_1d(root, file, AOI, AOI_points, new_dir)
                end = process_time()
                print("Generating 1D forcing data for " + AOI + " domain takes {}".format(end-start))
        else:
            with ProcessPoolExecutor(max_workers=default_workers) as executor:
                futures = []
                for root, file, new_dir in tasks:
                    os.makedirs(new_dir, exist_ok=True)
                    futures.append(executor.submit(AOI_forcing_save_1d, root, file, AOI, AOI_points, new_dir))
                for fut in as_completed(futures):
                    fut.result()


if __name__ == '__main__':
    main()


