# Python Conversion of IDL Scripts

This directory contains Python conversions of the IDL scripts from the `idl_code/` directory. All four scripts have been converted from IDL to Python while maintaining the same functionality and logic.

## Files

### 1. `create_anthro_cesm.py`
Converts HTAP3 monthly emissions to CESM-ready format for base species (BC, CO, NH3, NOx, OC, SO2).

**Key operations:**
- Reads monthly HTAP3 emissions files by species and year
- Sums sectors while excluding Aviation and Agricultural waste burning
- Creates date and time variables
- Converts units from kg/m²/s to molecules/cm²/s
- Shifts longitude from -180-180 to 0-360 range

**Requirements:**
- Input files: `edgar_HTAPv32_YYYY_SPECIES.nc` (monthly data from 2000-2020)
- Output directory: Must exist or be created

### 2. `create_moz_vocs.py`
Creates MOZART-speciated VOC emissions from HTAP3 NMVOC emissions.

**Key operations:**
- Reads VOC speciation factors from CSV file (species × sectors × regions)
- Reads molecular weights for each MOZART species
- Applies region-specific speciation factors to NMVOC emissions
- Creates separate files for each speciated VOC species

**Dependencies:**
- `file_htap_moz`: CSV file with speciation factors
- `species_molwts.csv`: Molecular weights for MOZART species
- `template_0.9x1.25_L32.nc`: Template file for grid and region mapping

**Functions:**
- `create_moz_vocs()`: Main function to create VOC emissions
- `get_map_region()`: Creates region assignment map for 0.9×1.25° grid
- `map_regions()`: Visualization function (requires matplotlib)

### 3. `make_emis_htap3_svocivoc.py`
Creates SVOC and IVOC emissions for VBS-SOA from HTAP3 emissions.

**Key operations:**
IVOC = 0.2 × sum of HC emissions (C2H4, C2H6, C3H6, C3H8, BIGENE, BIGALK, CH3COCH3, MEK, CH3CHO, CH2O, BENZENE, TOLUENE, XYLENES)

SVOC = 0.6 × POM_a4 emissions (with molecular weight conversion)

**References:**
- Jathar et al. [2014, Table 1]
- GECKO-A model for SOA yields

### 4. `add_jan1.py`
Updates the date of the last time step in all HTAP3 emissions files from 2020/12/15 to 2021/01/01.

**Key operations:**
- Finds all `HTAPv32*.nc` files in output directory
- Updates last date value to 20210101
- Updates last time value (days since 1950-01-01)
- Writes changes back to files

## Installation

Required Python packages:
```bash
pip install xarray netCDF4 numpy pandas
```

Optional (for visualization):
```bash
pip install matplotlib
```

## Usage

Each script can be run independently:

```bash
python create_anthro_cesm.py
python create_moz_vocs.py
python make_emis_htap3_svocivoc.py
python add_jan1.py
```

Or run in sequence in a batch script:
```bash
for script in create_anthro_cesm.py create_moz_vocs.py make_emis_htap3_svocivoc.py add_jan1.py; do
    python $script
done
```

## Key Differences from IDL

1. **File I/O**: Uses `xarray` for NetCDF operations instead of IDL's `ncdf_*` functions
2. **Array Operations**: Uses NumPy arrays; xarray handles NetCDF structure automatically
3. **String Operations**: Uses Python string methods (`.replace()`, `.lower()`, etc.)
4. **Array Indexing**: Uses NumPy's `where()` and boolean indexing
5. **Date/Time**: Uses `datetime` module for Julian day calculations
6. **File Paths**: Uses `pathlib.Path` for cross-platform compatibility
7. **Attributes**: Set via `.attrs` dictionary on xarray datasets and variables
8. **Error Handling**: Interactive input with `input()` instead of IDL's `read()`

## Metadata Handling

All scripts preserve metadata including:
- Variable attributes (units, long_name, etc.)
- Global attributes (data_title, data_creator, data_summary, etc.)
- NetCDF4 format with unlimited time dimensions

## Performance Notes

- `create_anthro_cesm.py`: Fast (single-pass file operations)
- `create_moz_vocs.py`: May be slow due to nested loops over grid points (~5-10 minutes)
- `make_emis_htap3_svocivoc.py`: Fast (vectorized operations)
- `add_jan1.py`: Very fast (simple updates)

The nested loops in `create_moz_vocs.py` could be optimized using NumPy broadcasting for large grids.

## Troubleshooting

**File not found errors**: Check that all input data directories exist and contain expected files.

**Memory errors**: Large grids may require breaking up operations; reduce data dimensions if needed.

**NetCDF encoding issues**: Ensure netCDF4 library is properly installed with HDF5 support.
