#!/usr/bin/env python
"""
Create MOZART VOC emissions from HTAP3 NMVOC emissions using speciation factors.

This script:
  - Reads VOC speciation factors from CSV file
  - Reads molecular weights for MOZART species
  - Reads NMVOC emissions by sector and region
  - Applies speciation factors to create species-specific emissions
"""

import numpy as np
import xarray as xr
import pandas as pd
from pathlib import Path

def create_moz_vocs():
    """
    Create MOZART VOC emissions from HTAP3 NMVOC emissions using speciation factors.
    """
    path_out = Path('/glade/campaign/acom/acom-weather/emmons/HTAP3/emissions/anthro_v3.2/cesm_ready/')
    path_out.mkdir(parents=True, exist_ok=True)

    date_created = '20260409'

    # Total VOC emissions for each sector at 0.9x1.25deg
    file_nmvoc = '/glade/campaign/acom/acom-weather/emmons/HTAP3/emissions/anthro_v3.2/f09/2000-2020_kg/HTAPv3.2_NMVOC_anthro-sectors_2000-2020_f09_kg_c20251203.nc'

    # VOC speciation factors for each sector and region
    file_htap_moz = '/glade/u/home/emmons/EMISSIONS/HTAP/MOZART_VOCspeciation_forHTAP3_c20260116.csv'

    nreg = 5
    regions = ['Asia', 'NorthAmerica', 'Europe', 'Other', 'World']
    sectors0 = [
        'HTAPv3_1_International_Shipping',
        'HTAPv3_3_Energy',
        'HTAPv3_4_1_Industry',
        'HTAPv3_4_2_Fugitive',
        'HTAPv3_4_3_Solvents',
        'HTAPv3_5_1_Road_Transport',
        'HTAPv3_5_3_Domestic_shipping',
        'HTAPv3_5_4_Other_ground_transport',
        'HTAPv3_6_Residential',
        'HTAPv3_7_Waste',
        'HTAPv3_8_2_Agriculture_livestock',
        'HTAPv3_8_3_Agriculture_crops'
    ]
    sectors = [s.lower() for s in sectors0]
    nsectors = len(sectors)
    out_varlist = '+'.join(sectors0)

    # Read speciation factors from CSV
    print(f"Reading speciation factors from {file_htap_moz}")
    df = pd.read_csv(file_htap_moz, skiprows=2)
    colnames = df.columns.tolist()
    species = [s.strip() for s in colnames[3:]]
    nspec = len(species)

    print(f"Species ({nspec}): {species}")

    # Initialize factors array [species, sectors, regions]
    factors = np.zeros((nspec, nsectors, nreg), dtype=np.float32)

    # Parse the CSV data
    for idx, row in df.iterrows():
        region = str(row[colnames[0]]).replace(' ', '')
        code0 = row[colnames[1]].replace('.', '_')
        code = 'HTAPv3' + code0[4:]
        name = '_'.join(str(row[colnames[2]]).split())
        sector = (code + '_' + name).lower()

        # Find region index
        try:
            ireg = regions.index(region)
        except ValueError:
            print(f"  Bad region: {region}")
            continue

        # Find sector index
        try:
            isect = sectors.index(sector)
            data = np.array([float(row[col]) for col in colnames[3:]], dtype=np.float32)
            factors[:, isect, ireg] = data
        except ValueError:
            print(f"  Not using: {sector}")

    # Print factors
    print("\nSpeciation Factors:")
    for ireg in range(5):
        print(f"  {regions[ireg]}")
        for ispec in range(nspec):
            print(f"    {species[ispec]}: {factors[ispec, :, ireg]}")

    # Read molecular weights
    print("\nMolecular Weights:")
    molwts = np.zeros(nspec, dtype=np.float32)
    mw_file = '/glade/u/home/emmons/EMISSIONS/species_molwts.csv'
    mw_df = pd.read_csv(mw_file)

    for ispec, spec in enumerate(species):
        match = mw_df[mw_df.iloc[:, 0].str.strip() == spec]
        if not match.empty:
            molwts[ispec] = float(match.iloc[0, 1])

    for ispec in range(nspec):
        mw = molwts[ispec]
        if mw <= 0:
            mw = float(input(f"  MW missing for {species[ispec]}, enter new value: "))
            molwts[ispec] = mw
        print(f"  {species[ispec]}: {molwts[ispec]:.1f}")

    # Get map of regions for f09 grid
    map_region = get_map_region()

    # Open NMVOC file
    print(f"\nReading NMVOC emissions from {file_nmvoc}")
    ds_v = xr.open_dataset(file_nmvoc)
    lon = ds_v['lon'].values
    lat = ds_v['lat'].values
    time = ds_v['time'].values
    time_units = ds_v['time'].attrs.get('units', '')
    date = ds_v['date'].values

    nlon = len(lon)
    nlat = len(lat)
    ntim = len(time)

    # Create emissions for each species
    for ispec in range(nspec):
        spec = species[ispec]
        mw = molwts[ispec]

        file_spec = path_out / f'HTAPv32_{spec}_anthro_2000-2020_f09_c{date_created}.nc'
        print(f"\nCreating: {file_spec}")

        # Initialize output dataset
        ds_out = xr.Dataset(
            data_vars={
                'anthro': (['lon', 'lat', 'time'], np.zeros((nlon, nlat, ntim), dtype=np.float32))
            },
            coords={
                'lon': lon,
                'lat': lat,
                'time': time
            }
        )

        # Add date variable
        ds_out['date'] = (['time'], date)

        # Add attributes
        ds_out['lon'].attrs = {'units': 'degrees_east', 'long_name': 'Longitude'}
        ds_out['lat'].attrs = {'units': 'degrees_north', 'long_name': 'Latitude'}
        ds_out['time'].attrs = {'units': time_units, 'long_name': 'Time'}
        ds_out['date'].attrs = {'units': 'YYYYMMDD', 'long_name': 'date'}
        ds_out['anthro'].attrs = {
            'units': 'molecules cm-2 s-1',
            'long_name': f'{spec} anthro emissions'
        }

        # Global attributes
        ds_out.attrs = {
            'data_title': f'HTAPv3.2 anthro emissions of {spec}',
            'molecular_weight': mw,
            'data_creator': 'Louisa Emmons (emmons@ucar.edu)',
            'data_summary': 'HTAPv3.2 anthropogenic emissions mosaic (https://zenodo.org/records/17086684). Original files: edgar_HTAPv32_YYYY_NMVOC.nc. Speciated according to NMVOC_speciation_HTAP_v3.xls (https://edgar.jrc.ec.europa.eu/dataset_htap_v32#p3).',
            'sectors_summed': out_varlist,
            'creation_date': date_created,
            'data_script': __file__
        }

        # Calculate emissions for each sector
        anthro = np.zeros((nlon, nlat, ntim), dtype=np.float32)

        for isect in range(nsectors):
            sector_name = sectors0[isect]
            if sector_name in ds_v.data_vars:
                data_sect = ds_v[sector_name].values.astype(np.float32)

                for ilon in range(nlon):
                    for ilat in range(nlat):
                        ireg = map_region[ilon, ilat]
                        # Regional factor + World factor
                        voc = data_sect[ilon, ilat, :] * factors[ispec, isect, ireg]
                        voc_w = data_sect[ilon, ilat, :] * factors[ispec, isect, 4]  # World region
                        anthro[ilon, ilat, :] += voc + voc_w

                # Print diagnostic value (eastern US point)
                print(f"  {sector_name}: {anthro[220, 138, 0]:.6e}")

        ds_out['anthro'].values = anthro

        # Write to file
        ds_out.to_netcdf(file_spec, format='NETCDF4', unlimited_dims=['time'])
        print(f"Closed: {file_spec}")

    ds_v.close()


def get_map_region():
    """
    Create a map of regions for the 0.9x1.25 degree grid.
    Returns array of region indices for each grid point.
    """
    print("Creating region map from template file")

    template_file = '/glade/work/emmons/ic/template_0.9x1.25_L32.nc'
    ds = xr.open_dataset(template_file)
    lon = ds['lon'].values
    lat = ds['lat'].values
    ds.close()

    nlon = len(lon)
    nlat = len(lat)
    map_region = np.full((nlon, nlat), 3, dtype=np.int32)  # Default to 'Other'

    regions = ['Asia', 'NorthAmerica', 'Europe', 'Other']
    region_bounds = {
        'Asia': {'latmin': 0, 'latmax': 90, 'lonmin': 60, 'lonmax': 180},
        'NorthAmerica': {'latmin': 0, 'latmax': 90, 'lonmin': 180, 'lonmax': 330},
        'Europe': {'latmin': 30, 'latmax': 90, 'lonmin': -30, 'lonmax': 60}
    }

    for ireg, reg in enumerate(regions[:3]):
        bounds = region_bounds[reg]
        latmin, latmax = bounds['latmin'], bounds['latmax']
        lonmin, lonmax = bounds['lonmin'], bounds['lonmax']

        # Find latitude indices
        indlat = np.where((lat >= latmin) & (lat <= latmax))[0]

        # Find longitude indices
        if lonmin > 0:
            indlon = np.where((lon >= lonmin) & (lon < lonmax))[0]
        else:
            indl1 = np.where((lon >= (lonmin + 360)) & (lon <= 360))[0]
            indl2 = np.where((lon >= 0) & (lon < lonmax))[0]
            indlon = np.concatenate([indl2, indl1])

        # Set region indices
        for ilat in indlat:
            map_region[np.ix_(indlon, [ilat])] = ireg

    return map_region


def map_regions():
    """
    Visualize the region map (requires matplotlib).
    """
    import matplotlib.pyplot as plt

    print("Creating region visualization")

    template_file = '/glade/work/emmons/ic/template_0.9x1.25_L32.nc'
    ds = xr.open_dataset(template_file)
    lon = ds['lon'].values
    lat = ds['lat'].values
    ds.close()

    map_region = get_map_region()

    # Plot
    fig, ax = plt.subplots(figsize=(12, 8))

    # Create scatter plot with colors for each region
    colors = [50, 100, 150, 250]
    region_names = ['Asia', 'NorthAmerica', 'Europe', 'Other']

    for ilon in range(len(lon)):
        for ilat in range(len(lat)):
            jreg = map_region[ilon, ilat]
            ax.scatter(lon[ilon], lat[ilat], c=[colors[jreg]], s=1, alpha=0.5)

    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title('HTAP3 Region Map')
    plt.show()


if __name__ == '__main__':
    create_moz_vocs()
