#!/usr/bin/env python
"""
Create CESM-ready emissions files for HTAP3 of base species.

This script:
  - Reads files for each species for each year
  - Sums sectors leaving out Aviation and Ag waste burning
  - Concatenates data across years
  - Creates date and time variables
  - Converts from kg/m2/s to molecules/cm2/s
  - Shifts longitude from -180-180 to 0-360
"""

import numpy as np
import xarray as xr
from pathlib import Path
from datetime import datetime

def create_anthro_cesm():
    """
    Create CESM-ready anthropogenic emissions files for HTAP3 base species.
    """
    path_orig = Path('/glade/campaign/acom/acom-weather/emmons/HTAP3/emissions/anthro_v3.2/monthly/')
    path_out = Path('/glade/campaign/acom/acom-weather/emmons/HTAP3/emissions/anthro_v3.2/monthly_combined/0.1deg/')
    path_out.mkdir(parents=True, exist_ok=True)

    species = ['BC', 'CO', 'NH3', 'NOx', 'OC', 'SO2']
    mws = np.array([12, 28, 17, 46, 12, 64], dtype=float)  # g/mole
    navog = 6.022e23

    for ispec, spec in enumerate(species):
        mw = mws[ispec]
        file_new = path_out / f'HTAPv32_{spec}_anthro_2000-2020_01x01.nc'
        print(f'Creating: {file_new}')

        nlon = 3600
        nlat = 1800
        ntim = 12 * 21  # 12 months × 21 years (2000-2020)

        # Initialize arrays
        date = np.zeros(ntim, dtype=np.int64)
        time_all = np.zeros(ntim, dtype=np.float32)
        time_all_units = "days since 1750-01-01 00:00:00"
        anthro_all = np.zeros((nlon, nlat, ntim), dtype=np.float32)
        lon_shift = np.arange(3600) * 0.1 + 0.05

        # Reference date for Julian day calculation
        ref_date = datetime(1750, 1, 1)

        for yr in range(2000, 2021):
            file_sp_y = path_orig / f'edgar_HTAPv32_{yr:04d}_{spec}.nc'
            print(f'  Reading {file_sp_y}')

            # Open input file
            ds = xr.open_dataset(file_sp_y)
            lon = ds['lon'].values
            lat = ds['lat'].values
            time1 = ds['time'].values
            time_units = ds['time'].attrs.get('units', '')
            print(f"    Time range: {np.min(time1):.1f} to {np.max(time1):.1f} ({time_units})")

            # Create date and time variables
            for imon in range(12):
                jtim = (yr - 2000) * 12 + imon
                # Calculate Julian day for middle of month
                mid_date = datetime(yr, imon + 1, 15)
                time_all[jtim] = (mid_date - ref_date).days
                date[jtim] = yr * 10000 + (imon + 1) * 100 + 15
                print(f"    Time step {jtim}: date={date[jtim]}, time={time_all[jtim]:.1f}")

            # Get list of 3D variables, excluding Aviation and Agricultural_waste_burning
            varlist = []
            for var_name in ds.data_vars:
                var = ds[var_name]
                if var.ndim == 3:  # 3D variables
                    if 'Aviation' not in var_name and 'Agricultural_waste_burning' not in var_name:
                        varlist.append(var_name)

            print(f"    Variables to sum: {varlist}")

            # Sum sectors
            anthro_kg = None
            for ivar, var_name in enumerate(varlist):
                print(f"      {var_name}")
                var1 = ds[var_name].values.astype(np.float32)
                if ivar == 0:
                    anthro_kg = var1.copy()
                else:
                    anthro_kg += var1
                print(f"        Max: {np.max(anthro_kg):.6e}")

            ds.close()

            # Convert from kg/m2 to molecules/cm2
            # sf = (molecules/mole) / (kg/mole) * (m2/cm2)
            sf = navog / (mw * 1.0e-3) * 1.0e-4
            jtim1 = (yr - 2000) * 12
            jtim2 = (yr - 2000) * 12 + 12
            print(f"    Storing time steps {jtim1}:{jtim2}")

            # Shift longitude from -180-180 to 0-360
            # Old grid: 0-1799 is -180 to 0, 1800-3599 is 0 to 180
            # New grid: 0-1799 is 0 to 180, 1800-3599 is 180 to 360
            anthro_all[0:1800, :, jtim1:jtim2] = anthro_kg[1800:3600, :, :] * sf
            anthro_all[1800:3600, :, jtim1:jtim2] = anthro_kg[0:1800, :, :] * sf

        # Create output dataset
        out_varlist = '+'.join(varlist)

        ds_out = xr.Dataset(
            data_vars={
                'anthro': (['lon', 'lat', 'time'], anthro_all)
            },
            coords={
                'lon': lon_shift,
                'lat': lat,
                'time': time_all
            }
        )

        # Add date variable
        ds_out['date'] = (['time'], date)

        # Set variable attributes
        ds_out['lon'].attrs = {
            'units': 'degrees_east',
            'long_name': 'Longitude'
        }
        ds_out['lat'].attrs = {
            'units': 'degrees_north',
            'long_name': 'Latitude'
        }
        ds_out['time'].attrs = {
            'units': time_all_units,
            'long_name': 'Time'
        }
        ds_out['date'].attrs = {
            'units': 'YYYYMMDD',
            'long_name': 'date'
        }
        ds_out['anthro'].attrs = {
            'units': 'molecules cm-2 s-1',
            'long_name': f'{spec} anthro emissions'
        }

        # Set global attributes
        ds_out.attrs = {
            'data_title': f'HTAPv3.2 anthro emissions of {spec}',
            'molecular_weight': float(mw),
            'data_creator': 'Louisa Emmons (emmons@ucar.edu)',
            'data_summary': f'HTAPv3.2 anthropogenic emissions mosaic (https://zenodo.org/records/17086684). Original files: edgar_HTAPv32_YYYY_{spec}.nc',
            'sectors_summed': out_varlist,
            'creation_date': '2026-01-14',
            'data_script': __file__
        }

        # Write to NetCDF4
        ds_out.to_netcdf(file_new, format='NETCDF4', unlimited_dims=['time'])
        print(f'Closed: {file_new}\n')


if __name__ == '__main__':
    create_anthro_cesm()
