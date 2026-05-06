
#!/usr/bin/env python
"""
Create CESM-ready emissions files for HTAP3 of base species.
Read files for each species for each year,
sum sectors leaving out Aviation and Ag waste burning,
concatenate,
create date and time variables,
convert from kg/m2/s to molecules/cm2/s,
shift lon from -180 - 180 to 0-360
"""

import numpy as np
import xarray as xr
from pathlib import Path
from datetime import datetime, timedelta
import inspect


def create_anthro_cesm():
    path_orig = Path('/glade/campaign/acom/acom-weather/emmons/HTAP3/emissions/anthro_v3.2/monthly/')
    path_out = Path('/glade/campaign/acom/acom-weather/emmons/HTAP3/emissions/anthro_v3.2/monthly_combined/0.1deg/')
    
    # Ensure output directory exists
    path_out.mkdir(parents=True, exist_ok=True)
    
    species = ['BC', 'CO', 'NH3', 'NOx', 'OC', 'SO2']
    mws = [12, 28, 17, 46, 12, 64]  # g/mole
    navog = 6.022e23
    
    for ispec, spec in enumerate(species):
        mw = mws[ispec]
        
        file_new = path_out / f'HTAPv32_{spec}_anthro_2000-2020_01x01.nc'
        print(f'Creating: {file_new}')
        
        nlon = 3600
        nlat = 1800
        ntim = 12 * 21
        
        date = np.zeros(ntim, dtype=np.int64)
        time_all = np.zeros(ntim, dtype=np.float32)
        time_all_units = "days since 1750-01-01 00:00:00"
        anthro_all = np.zeros((nlon, nlat, ntim), dtype=np.float32)
        lon_shift = np.arange(3600) * 0.1 + 0.05
        
        for yr in range(2000, 2021):
            file_sp_y = path_orig / f'edgar_HTAPv32_{yr}_{spec}.nc'
            print(f'{file_sp_y}')
            
            # Open the input file
            ds = xr.open_dataset(file_sp_y)
            lon = ds['lon'].values
            lat = ds['lat'].values
            time1 = ds['time'].values
            time_units = ds['time'].attrs.get('units', '')
            print(f'{time1.min()}, {time1.max()}, {time_units}')
            
            # Create date and time arrays
            for imon in range(12):
                jtim = (yr - 2000) * 12 + imon
                # Calculate days since 1750-01-01 for the 15th of each month
                date_obj = datetime(yr, imon + 1, 15)
                date_ref = datetime(1750, 1, 1)
                time_all[jtim] = (date_obj - date_ref).days
                date[jtim] = yr * 10000 + (imon + 1) * 100 + 15
                print(f'{jtim}, {date[jtim]}, {time_all[jtim]}')
            
            # Get list of variables to sum (exclude Aviation and Agricultural_waste_burning)
            varlist = []
            for var_name in ds.data_vars:
                if len(ds[var_name].dims) == 3:
                    if 'Aviation' not in var_name and 'Agricultural_waste_burning' not in var_name:
                        varlist.append(var_name)
            
            print(f'Variables: {varlist}')
            
            # Sum all sectors
            anthro_kg = None
            for ivar, var_name in enumerate(varlist):
                print(f'{var_name}')
                var1 = ds[var_name].values
                if ivar == 0:
                    anthro_kg = var1.copy()
                else:
                    anthro_kg += var1
                print(f'Max: {np.max(anthro_kg)}')
            
            ds.close()
            
            # Convert from kg/m2 to molecules/cm2
            # (molecules/mole) / (kg/mole) * (m2/cm2)
            sf = navog / (mw * 1.0e-3) * 1.0e-4
            jtim1 = (yr - 2000) * 12
            jtim2 = (yr - 2000) * 12 + 12
            print(f'{jtim1}, {jtim2-1}')
            
            # Shift longitude from -180-180 to 0-360
            anthro_all[0:1800, :, jtim1:jtim2] = anthro_kg[1800:3600, :, :] * sf
            anthro_all[1800:3600, :, jtim1:jtim2] = anthro_kg[0:1800, :, :] * sf
        
        # Create output dataset
        out_varlist = '+'.join(varlist)
        
        # Create coordinates and data arrays
        ds_out = xr.Dataset(
            data_vars={
                'anthro': (['lon', 'lat', 'time'], anthro_all),
            },
            coords={
                'lon': ('lon', lon_shift),
                'lat': ('lat', lat),
                'time': ('time', time_all),
                'date': ('time', date),
            }
        )
        
        # Add attributes
        ds_out['lon'].attrs['units'] = 'degrees_east'
        ds_out['lon'].attrs['long_name'] = 'Longitude'
        
        ds_out['lat'].attrs['units'] = 'degrees_north'
        ds_out['lat'].attrs['long_name'] = 'Latitude'
        
        ds_out['time'].attrs['units'] = time_all_units
        ds_out['time'].attrs['long_name'] = 'Time'
        
        ds_out['date'].attrs['units'] = 'YYYYMMDD'
        ds_out['date'].attrs['long_name'] = 'date'
        
        ds_out['anthro'].attrs['units'] = 'molecules cm-2 s-1'
        ds_out['anthro'].attrs['long_name'] = f'{spec} anthro emissions'
        
        # Global attributes
        ds_out.attrs['data_title'] = f'HTAPv3.2 anthro emissions of {spec}'
        ds_out.attrs['molecular_weight'] = mw
        ds_out.attrs['data_creator'] = 'Louisa Emmons (emmons@ucar.edu)'
        ds_out.attrs['data_summary'] = 'HTAPv3.2 anthropogenic emissions mosaic (https://zenodo.org/records/17086684). Original files: edgar_HTAPv32_YYYY_' + spec + '.nc'
        ds_out.attrs['sectors_summed'] = out_varlist
        ds_out.attrs['creation_date'] = '2026-01-14'
        ds_out.attrs['data_script'] = inspect.getfile(inspect.currentframe())
        
        # Write to netCDF4 format
        ds_out.to_netcdf(file_new, engine='netcdf4', unlimited_dims=['time'])
        print(f'Closed: {file_new}')


if __name__ == '__main__':
    create_anthro_cesm()
