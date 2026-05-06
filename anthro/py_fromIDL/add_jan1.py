import numpy as np
import xarray as xr
from pathlib import Path
from glob import glob

def add_jan1():
    """
    Rewrite date of last time in file (2020/12/15) to be Jan 1 of next year.
    Updates both the 'date' and 'time' variables in all HTAP3 emissions files.
    """
    
    path_emis = Path('/glade/campaign/acom/acom-weather/emmons/HTAP3/emissions/anthro_v3.2/cesm_ready/netcdf4/')
    
    # Find all HTAPv32 NetCDF files
    files = sorted(path_emis.glob('HTAPv32*.nc'))
    nfiles = len(files)
    print(f"{nfiles} files found")
    
    varname = 'anthro'
    newdate = 20210101
    
    # Calculate new time value in days since 1950-01-01 00:00:00
    # julday(month, day, year) returns days since Jan 1, year -4713 (Julian calendar)
    # So we need: Julday(1, 1, 2021) - Julday(1, 1, 1950)
    from datetime import datetime
    date_ref = datetime(1950, 1, 1)
    date_new = datetime(2021, 1, 1)
    newtime = (date_new - date_ref).days
    
    print(f"newdate: {newdate}, newtime: {newtime}")
    
    for ifile, file1 in enumerate(files):
        print(f"{ifile} {file1}")
        
        # Open file with write mode
        ds = xr.open_dataset(file1)
        
        # Get dimensions
        lon = ds['lon'].values
        lat = ds['lat'].values
        date = ds['date'].values
        time = ds['time'].values
        
        nlon = len(lon)
        nlat = len(lat)
        ntim = len(time)
        
        print(f"  Last date: {date[ntim-1]}")
        print(f"  Last time: {time[ntim-1]}")
        
        # Update last time and date values
        time[ntim-1] = newtime
        date[ntim-1] = newdate
        
        # Write updated values back to file
        ds['date'].values = date
        ds['time'].values = time
        
        # Save with same encoding as original
        ds.to_netcdf(file1, format='NETCDF4', unlimited_dims=['time'])
        ds.close()
        
        print(f"  Updated to date: {date[ntim-1]}, time: {time[ntim-1]}")


if __name__ == '__main__':
    add_jan1()