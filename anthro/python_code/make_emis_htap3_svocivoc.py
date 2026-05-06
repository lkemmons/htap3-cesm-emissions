#!/usr/bin/env python
"""
Create SVOC and IVOC emissions for VBS-SOA from HTAP3 emissions.

Reference:
Jathar et al. [2014, Table 1]: IVOC fraction = 0.2 x NMVOC
                                SVOC fraction = 0.6 x POA

IVOC mass emissions = 0.2 * sum of mass emissions of following HCs:
  C3H6, C3H8, C2H6, C2H4, BIGENE, BIGALK
  CH3COCH3, MEK, CH3CHO, CH2O
  BENZENE, TOLUENE, XYLENES

SVOC mass emissions = 0.6 * sum of mass of emissions of hydrophilic and hydrophobic POA
Note: Convert OC to OA using 1.4 factor if needed.

IVOC_emissions_total = IVOC mass emissions + (SVOC mass emissions)*1.25
Only anthropogenic sources.
"""

import numpy as np
import xarray as xr
from pathlib import Path
from datetime import datetime

def make_emis_htap3_svocivoc():
    """
    Create SVOC and IVOC emissions for VBS-SOA from HTAP3 emissions.
    """
    # Get current date
    today = datetime.now()
    todaystr = today.strftime('%Y/%m/%d')
    sdate_today = today.strftime('%Y%m%d')
    creation_date = '20260409'

    path_in = Path('/glade/campaign/acom/acom-weather/emmons/HTAP3/emissions/anthro_v3.2/cesm_ready/netcdf4/')
    path_out = path_in
    path_in.mkdir(parents=True, exist_ok=True)

    specs_ivoc = [
        'C2H4', 'C2H6', 'C3H6', 'C3H8', 'BIGENE', 'BIGALK',
        'CH3COCH3', 'MEK', 'CH3CHO', 'CH2O', 'BENZENE', 'TOLUENE', 'XYLENES'
    ]

    # Molecular weights
    mw_ivoc = 184.0
    mw_svoc = 310.0

    # Get dimensions from first file
    file0 = path_in / f'HTAPv32_C2H4_anthro_2000-2020_f09_c{creation_date}.nc'
    ds0 = xr.open_dataset(file0)
    lon = ds0['lon'].values
    lat = ds0['lat'].values
    time = ds0['time'].values
    date = ds0['date'].values
    time_units = ds0['time'].attrs.get('units', '')
    ds0.close()

    nlon = len(lon)
    nlat = len(lat)
    ntim = len(date)

    print(f"Grid dimensions: nlon={nlon}, nlat={nlat}, ntim={ntim}")

    # ========================================================================
    # IVOC = 0.2 * sum(HCs)
    # ========================================================================
    print("\nCreating IVOC emissions...")
    emis_ivoc = np.zeros((nlon, nlat, ntim), dtype=np.float32)

    for ispec, spec_hc in enumerate(specs_ivoc):
        file_hc = path_in / f'HTAPv32_{spec_hc}_anthro_2000-2020_f09_c{creation_date}.nc'
        print(f"  Reading {spec_hc}...")

        ds_hc = xr.open_dataset(file_hc)
        emis_hc = ds_hc['anthro'].values.astype(np.float32)
        mw_hc = float(ds_hc.attrs['molecular_weight'])
        ds_hc.close()

        # Convert to IVOC mass basis and add
        emis_ivoc += 0.2 * emis_hc * mw_hc / mw_ivoc

    hist = 'IVOC=0.2*(' + '+'.join(specs_ivoc) + ')'
    spec = 'IVOC'

    # Create IVOC output file
    newfile = path_out / f'HTAPv32_{spec}_anthro_2000-2020_f09_c{creation_date}.nc'
    print(f"\nWriting IVOC file: {newfile}")

    ds_ivoc = xr.Dataset(
        data_vars={
            'anthro': (['lon', 'lat', 'time'], emis_ivoc)
        },
        coords={
            'lon': lon,
            'lat': lat,
            'time': time
        }
    )

    # Add date as a coordinate
    ds_ivoc['date'] = (['time'], date)

    # Set variable attributes
    ds_ivoc['lon'].attrs = {
        'units': 'degrees_east',
        'long_name': 'Longitude'
    }
    ds_ivoc['lat'].attrs = {
        'units': 'degrees_north',
        'long_name': 'Latitude'
    }
    ds_ivoc['time'].attrs = {
        'units': time_units,
        'long_name': 'time',
        'calendar': 'Gregorian'
    }
    ds_ivoc['date'].attrs = {
        'units': 'YYYYMMDD',
        'long_name': 'Date'
    }
    ds_ivoc['anthro'].attrs = {
        'units': 'molecules/cm2/s',
        'long_name': 'IVOC anthro emissions',
        'description': hist,
        'molecular_weight': mw_ivoc
    }

    # Set global attributes
    ds_ivoc.attrs = {
        'data_title': f'HTAPv3.2 anthro emissions of {spec}',
        'molecular_weight': mw_ivoc,
        'data_creator': 'Louisa Emmons (emmons@ucar.edu)',
        'data_summary': 'Lumped HCs precursor of SOA for VBS scheme, based on fractions of various HCs.',
        'data_source': 'HTAPv3.2 anthropogenic emissions mosaic (https://zenodo.org/records/17086684). Original files: edgar_HTAPv32_YYYY_NMVOC.nc. Speciated according to NMVOC_speciation_HTAP_v3.xls (https://edgar.jrc.ec.europa.eu/dataset_htap_v32#p3).',
        'creation_date': creation_date,
        'data_script': __file__
    }

    # Write to NetCDF4
    path_out.mkdir(parents=True, exist_ok=True)
    ds_ivoc.to_netcdf(newfile, format='NETCDF4', unlimited_dims=['time'])
    print(f"Closed: {newfile}")

    # ========================================================================
    # SVOC = 0.6 * POM_a4
    # ========================================================================
    print("\nCreating SVOC emissions...")

    file_pom = path_in / f'HTAPv32_pom_a4_2000-2020_f09_c{creation_date}.nc'
    print(f"  Reading {file_pom}...")

    ds_pom = xr.open_dataset(file_pom)
    emis_pom = ds_pom['anthro'].values.astype(np.float32)
    mw_pom = float(ds_pom.attrs['molecular_weight'])
    ds_pom.close()

    # Convert to SVOC mass basis
    emis_svoc = emis_pom * 0.6 * mw_pom / mw_svoc

    spec = 'SVOC'

    # Create SVOC output file
    newfile = path_out / f'HTAPv32_{spec}_anthro_2000-2020_f09_c{creation_date}.nc'
    print(f"\nWriting SVOC file: {newfile}")

    ds_svoc = xr.Dataset(
        data_vars={
            'anthro': (['lon', 'lat', 'time'], emis_svoc)
        },
        coords={
            'lon': lon,
            'lat': lat,
            'time': time
        }
    )

    # Add date as a coordinate
    ds_svoc['date'] = (['time'], date)

    # Set variable attributes
    ds_svoc['lon'].attrs = {
        'units': 'degrees_east',
        'long_name': 'Longitude'
    }
    ds_svoc['lat'].attrs = {
        'units': 'degrees_north',
        'long_name': 'Latitude'
    }
    ds_svoc['time'].attrs = {
        'units': time_units,
        'long_name': 'time',
        'calendar': 'Gregorian'
    }
    ds_svoc['date'].attrs = {
        'units': 'YYYYMMDD',
        'long_name': 'Date'
    }
    ds_svoc['anthro'].attrs = {
        'units': 'molecules/cm2/s',
        'long_name': 'SVOC anthro emissions',
        'description': '0.6*pom_a4',
        'molecular_weight': mw_svoc
    }

    # Set global attributes
    ds_svoc.attrs = {
        'data_title': f'HTAPv3.2 anthro emissions of {spec}',
        'molecular_weight': mw_svoc,
        'data_creator': 'Louisa Emmons (emmons@ucar.edu)',
        'data_summary': 'Precursor of SOA for VBS scheme, based on POM(OC).',
        'data_source': 'HTAPv3.2 anthropogenic emissions mosaic (https://zenodo.org/records/17086684). Original files: edgar_HTAPv32_YYYY_NMVOC.nc. Speciated according to NMVOC_speciation_HTAP_v3.xls (https://edgar.jrc.ec.europa.eu/dataset_htap_v32#p3).',
        'creation_date': creation_date,
        'data_script': __file__
    }

    # Write to NetCDF4
    ds_svoc.to_netcdf(newfile, format='NETCDF4', unlimited_dims=['time'])
    print(f"Closed: {newfile}")

    print("\nDone!")


if __name__ == '__main__':
    make_emis_htap3_svocivoc()
