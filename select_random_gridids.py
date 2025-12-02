#!/usr/bin/env python3

import argparse
import os
from typing import Optional, Dict, Any, Tuple

import numpy as np
from netCDF4 import Dataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Randomly select a percentage of gridIDs from a domain NetCDF and write them to a new NetCDF file. If --out is not specified, the output name is constructed as <caseName><percent>pct_gridID.nc in --output-dir."
    )
    parser.add_argument(
        "--domain",
        required=True,
        help="Path to the domain NetCDF containing variable 'gridID' with dims (nj, ni).",
    )
    parser.add_argument(
        "--percent",
        required=True,
        type=float,
        help="Percentage of gridcells to sample. If <1, treated as a fraction; otherwise treated as percent in [0,100].",
    )
    parser.add_argument(
        "--case-name",
        required=True,
        help="Case name prefix to use when constructing the default output name <caseName><percent>pct_gridID.nc (ignored if --out is provided).",
    )
    parser.add_argument(
        "--out",
        required=False,
        help="Output NetCDF path to write selected gridIDs.",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory to place the auto-generated output file when --out is not provided (default: current directory).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional RNG seed for reproducibility.",
    )
    parser.add_argument(
        "--like",
        default="/gpfs/wolf2/cades/cli185/proj-shared/wangd/kiloCraft/uELM_TES_experiment/TNdemo_gridID.nc",
        help="Optional NetCDF file whose variable/global attributes to emulate (defaults to TNdemo_gridID.nc).",
    )
    parser.add_argument(
        "--no-sort",
        action="store_true",
        help="Do not sort selected gridIDs; keep random order.",
    )
    return parser.parse_args()


def _format_percent_token(percent: float) -> str:
    """
    Convert user-provided percent/fraction to a string token like '5pct'.
    """
    pct_value = percent if percent >= 1.0 else (percent * 100.0)
    pct_rounded = int(round(pct_value))
    return f"{pct_rounded}pct"


def _derive_output_path(case_name: str, percent: float, output_dir: str) -> str:
    token = _format_percent_token(percent)
    base = f"{case_name}{token}_gridID.nc"
    return os.path.join(output_dir or ".", base)


def read_gridids(domain_path: str) -> Tuple[np.ndarray, Dict[str, Any], Dict[str, Any]]:
    """
    Return:
        grid_ids: shape (ni,) int array
        var_attrs: attributes from domain gridID variable
        global_attrs: dict of global attributes from domain file
    """
    with Dataset(domain_path, mode="r") as ds:
        if "gridID" not in ds.variables:
            raise KeyError("Variable 'gridID' not found in domain file.")
        grid_var = ds.variables["gridID"]
        grid = grid_var[:]
        if grid.ndim != 2:
            raise ValueError(f"Expected 'gridID' to be 2D (nj, ni), got shape {grid.shape}")
        # Expect nj=1
        if grid.shape[0] != 1:
            raise ValueError(f"Expected first dim nj=1, got {grid.shape[0]} for 'gridID'.")
        grid_ids = np.asarray(grid).reshape(-1)
        var_attrs = {k: getattr(grid_var, k) for k in grid_var.ncattrs()}
        global_attrs = {k: getattr(ds, k) for k in ds.ncattrs()}
        return grid_ids, var_attrs, global_attrs


def read_like_attrs(like_path: Optional[str]) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    if not like_path:
        return None, None
    if not os.path.exists(like_path):
        return None, None
    with Dataset(like_path, mode="r") as ds:
        var_attrs = None
        if "gridID" in ds.variables:
            var = ds.variables["gridID"]
            var_attrs = {k: getattr(var, k) for k in var.ncattrs()}
        global_attrs = {k: getattr(ds, k) for k in ds.ncattrs()}
        return var_attrs, global_attrs


def compute_sample_size(total: int, percent: float) -> int:
    if percent < 0:
        raise ValueError("Percent must be non-negative.")
    # Values < 1 are treated as fractions; values >= 1 are treated as percents
    fraction = percent if percent < 1.0 else (percent / 100.0)
    if fraction <= 0:
        return 1
    k = int(round(total * fraction))
    k = max(1, min(k, total))
    return k


def select_indices(num_total: int, num_select: int, seed: Optional[int]) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.choice(num_total, size=num_select, replace=False)


def write_output(
    out_path: str,
    selected_grid_ids: np.ndarray,
    like_var_attrs: Optional[Dict[str, Any]],
    like_global_attrs: Optional[Dict[str, Any]],
    fallback_var_attrs: Optional[Dict[str, Any]],
    title_annotation: str,
) -> None:
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    ni = int(selected_grid_ids.shape[0])
    with Dataset(out_path, mode="w", format="NETCDF4") as ds_out:
        # Dimensions to mirror reference: nj=1, ni=num_selected
        ds_out.createDimension("nj", 1)
        ds_out.createDimension("ni", ni)

        var = ds_out.createVariable("gridID", "i4", ("nj", "ni"))
        # Populate data
        var[0, :] = selected_grid_ids.astype(np.int32, copy=False)

        # Apply attributes: prefer --like, fall back to domain var attrs if available
        attrs_to_apply = like_var_attrs if like_var_attrs else (fallback_var_attrs or {})
        for k, v in attrs_to_apply.items():
            try:
                setattr(var, k, v)
            except Exception:
                # Be robust to non-serializable attributes
                pass

        # Global attributes: prefer --like; always add a helpful title annotation
        if like_global_attrs:
            for k, v in like_global_attrs.items():
                try:
                    setattr(ds_out, k, v)
                except Exception:
                    pass

        # Ensure a meaningful title is present/updated
        try:
            prev_title = getattr(ds_out, "title", "")
            new_title = f"{prev_title} | {title_annotation}" if prev_title else title_annotation
            setattr(ds_out, "title", new_title)
        except Exception:
            pass


def main() -> None:
    args = parse_args()

    grid_ids, domain_var_attrs, _ = read_gridids(args.domain)
    total = grid_ids.shape[0]
    num_select = compute_sample_size(total, args.percent)
    indices = select_indices(total, num_select, args.seed)
    selected = grid_ids[indices]

    if not args.no_sort:
        selected = np.sort(selected)

    like_var_attrs, like_global_attrs = read_like_attrs(args.like)

    out_path = args.out if args.out else _derive_output_path(args.case_name, args.percent, args.output_dir)

    title_annotation = (
        f"Random selection of {num_select}/{total} gridIDs "
        f"({(num_select/total)*100:.3f}%) from {os.path.basename(args.domain)}"
    )
    write_output(
        out_path=out_path,
        selected_grid_ids=selected,
        like_var_attrs=like_var_attrs,
        like_global_attrs=like_global_attrs,
        fallback_var_attrs=domain_var_attrs,
        title_annotation=title_annotation,
    )


if __name__ == "__main__":
    main()


