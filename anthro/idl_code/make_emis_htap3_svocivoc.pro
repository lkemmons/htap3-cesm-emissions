;Create SVOC and IVOC emissions for VBS-SOA
;Copy of /glade/u/home/emmons/CMIP6/emissions_hist/make_emis_cmip6_svocivoc.pro
;
; "As suggested by Jathar et al. [2014, Table 1], these precursor
;species were emitted as 0.6 x POA emissions for the IVOC fraction
;considered as lost by evaporation, and as 0.2 x NMVOC emissions for
;the unspeciated IVOC fraction of organic carbon mass. The
;corresponding SOA yields (Table 2) are derived from the GECKO-A model
;(Generator of Explicit Chemistry and Kinetics of Organics in the
;Atmosphere, [Aumont et al., 2005]) for low and high NOx conditions
;considering a mixture of n-alkane species shown in Table 3." 
;
; IVOC and SVOC emissions
;IVOC mass emissions =
;0.2 * sum of mass emissions of following HCs
;C3H6, C3H8, C2H6, C2H4, BIGENE, BIGALK
;CH3COCH3, MEK, CH3CHO, CH2O
;BENZENE, TOLUENE, XYLENES
;SVOC mass emissions = 
;0.6 * sum of mass of emissions of hydrophilic and hydrophobic POA
;You need to be careful to convert OC if emissions are in OC to OA (we used 1.4 factor).
;IVOC_emissions_total = IVOC mass emissions + (SVOC mass emissions)*1.25
;And these are only anthropogenic sources, see Jathar et al. [2014, Table 1]

pro make_emis_htap3_svocivoc

today = bin_date(systime())
todaystr = String(today[0:2],format='(i4,"/",i2.2,"/",i2.2)')
sdate_today = String(today[0:2],format='(i4,i2.2,i2.2)')
creation_date = '20260409'

path_in = '/glade/campaign/acom/acom-weather/emmons/HTAP3/emissions/anthro_v3.2/cesm_ready/netcdf4/'
path_out = path_in

specs_ivoc = ['C2H4', 'C2H6', 'C3H6', 'C3H8', 'BIGENE', 'BIGALK', $
 'CH3COCH3', 'MEK', 'CH3CHO', 'CH2O', 'BENZENE', 'TOLUENE', 'XYLENES']

;get dims
file0 = path_in+'HTAPv32_C2H4_anthro_2000-2020_f09_c'+creation_date+'.nc'
ncid = ncdf_open(file0)
ncdf_varget,ncid,'lon',lon
ncdf_varget,ncid,'lat',lat
ncdf_varget,ncid,'time',time
ncdf_varget,ncid,'date',date
ncdf_close,ncid
nlon = n_elements(lon)
nlat = n_elements(lat)
ntim = n_elements(date)

mw_ivoc = 184.
mw_svoc = 310.


 ;IVOC = 0.2*(HCs)
 emis_ivoc = fltarr(nlon,nlat,ntim)
 for ispec = 0,n_elements(specs_ivoc)-1 do begin
   spec_hc = specs_ivoc[ispec]
   file_hc = path_in+'HTAPv32_'+spec_hc+'_anthro_2000-2020_f09_c'+creation_date+'.nc'
   ncid = ncdf_open(file_hc)
   varname = 'anthro'
   ncdf_varget,ncid,varname,emis_hc1
   ncdf_attget,ncid,/global,'molecular_weight',mw_hc
   ncdf_close,ncid
   emis_ivoc = emis_ivoc + 0.2*emis_hc1*mw_hc/mw_ivoc
 endfor
 hist = 'IVOC=0.2*('+strjoin(specs_ivoc,"+")+')'
 spec = 'IVOC'
; write new file
  newfile = path_out+'HTAPv32_'+spec+'_anthro_2000-2020_f09_c'+creation_date+'.nc'
  print,newfile
  ncid = ncdf_create(newfile, /netcdf4_format, /clobber)
  xid = ncdf_dimdef(ncid,'lon',nlon)
  yid = ncdf_dimdef(ncid,'lat',nlat)
  tid = ncdf_dimdef(ncid,'time',/unlimited)
  ; Define variables with attributes
  xvarid = ncdf_vardef(ncid,'lon',[xid],/float)
  ncdf_attput, ncid, xvarid,/char, 'units', 'degrees_east'
  ncdf_attput, ncid, xvarid,/char, 'long_name', 'Longitude'
  yvarid = ncdf_vardef(ncid,'lat',[yid],/float)
  ncdf_attput, ncid, yvarid,/char, 'units', 'degrees_north'
  ncdf_attput, ncid, yvarid,/char, 'long_name', 'Latitude'
  tvarid = ncdf_vardef(ncid,'time',[tid],/float)
  ncdf_attput, ncid, tvarid,/char, 'long_name', 'time'
  ncdf_attput, ncid, tvarid,/char, 'units', 'days since 1750-01-01 00:00:00'
  ncdf_attput, ncid, tvarid,/char, 'calendar', 'Gregorian'
  tvarid = ncdf_vardef(ncid,'date',[tid],/long)
  ncdf_attput, ncid, tvarid,/char, 'units', 'YYYYMMDD'
  ncdf_attput, ncid, tvarid,/char, 'long_name', 'Date'
  varid = ncdf_vardef(ncid,varname,[xid,yid,tid],/float)
  ncdf_attput,ncid,/char,varid,'units','molecules/cm2/s'
  ncdf_attput,ncid,/char,varid,'long_name','IVOC anthro emissions'
  ncdf_attput,ncid,/char,varid,'description',hist
  ;Define global attributes
  ncdf_attput,ncid,/GLOBAL,/char,'data_title','HTAPv3.2 anthro emissions of '+spec
  ncdf_attput,ncid,/GLOBAL,/float,'molecular_weight',mw_ivoc
  ncdf_attput,ncid,/GLOBAL,/char,'data_creator','Louisa Emmons (emmons@ucar.edu)'
  ncdf_attput,ncid,/GLOBAL,/char,'data_summary','Lumped HCs precursor of SOA for VBS scheme, based on fractions of various HCs.'
  ncdf_attput,ncid,/GLOBAL,/char,'data_source','HTAPv3.2 anthropogenic emissions mosaic (https://zenodo.org/records/17086684). Original files: edgar_HTAPv32_YYYY_NMVOC.nc. Speciated according to NMVOC_speciation_HTAP_v3.xls (https://edgar.jrc.ec.europa.eu/dataset_htap_v32#p3).'
  ncdf_attput,ncid,/GLOBAL,/char,'creation_date',creation_date
  thisfile = Routine_filepath()
  ncdf_attput,ncid,/GLOBAL,/char,'data_script',thisfile
     
  ncdf_control,ncid,/ENDEF

  ncdf_varput,ncid,'lon',lon
  ncdf_varput,ncid,'lat',lat
  ncdf_varput,ncid,'time',time
  ncdf_varput,ncid,'date',date
  ncdf_varput,ncid,varname,emis_ivoc
  ncdf_close,ncid


 ;SVOC = 0.6*pom_a4
  file_pom = path_in+'HTAPv32_pom_a4_2000-2020_f09_c20260409.nc'
  ncid = ncdf_open(file_pom)
  varname = 'anthro'
  ncdf_varget,ncid,varname,emis_pom1
  ncdf_attget,ncid,/global,'molecular_weight',mw_pom
  ncdf_close,ncid
  emis_svoc = emis_pom1 * 0.6 *mw_pom/mw_svoc

 spec = 'SVOC'
; write new file
  newfile = path_out+'HTAPv32_'+spec+'_anthro_2000-2020_f09_c20260409.nc'
  print,newfile
  ncid = ncdf_create(newfile, /netcdf4_format, /clobber)
  xid = ncdf_dimdef(ncid,'lon',nlon)
  yid = ncdf_dimdef(ncid,'lat',nlat)
  tid = ncdf_dimdef(ncid,'time',/unlimited)
  ; Define variables with attributes
  xvarid = ncdf_vardef(ncid,'lon',[xid],/float)
  ncdf_attput, ncid, xvarid,/char, 'units', 'degrees_east'
  ncdf_attput, ncid, xvarid,/char, 'long_name', 'Longitude'
  yvarid = ncdf_vardef(ncid,'lat',[yid],/float)
  ncdf_attput, ncid, yvarid,/char, 'units', 'degrees_north'
  ncdf_attput, ncid, yvarid,/char, 'long_name', 'Latitude'
  tvarid = ncdf_vardef(ncid,'time',[tid],/float)
  ncdf_attput, ncid, tvarid,/char, 'long_name', 'time'
  ncdf_attput, ncid, tvarid,/char, 'units', 'days since 1750-01-01 00:00:00'
  ncdf_attput, ncid, tvarid,/char, 'calendar', 'Gregorian'
  tvarid = ncdf_vardef(ncid,'date',[tid],/long)
  ncdf_attput, ncid, tvarid,/char, 'units', 'YYYYMMDD'
  ncdf_attput, ncid, tvarid,/char, 'long_name', 'Date'
  varid = ncdf_vardef(ncid,varname,[xid,yid,tid],/float)
  ncdf_attput,ncid,/char,varid,'units','molecules/cm2/s'
  ncdf_attput,ncid,/char,varid,'long_name','SVOC anthro emissions'
  ncdf_attput,ncid,/float,varid,'molecular_weight',mw_svoc
  ncdf_attput,ncid,/char,varid,'history','0.6*pom_a4'
  ;Define global attributes
  ncdf_attput,ncid,/GLOBAL,/char,'data_title','HTAPv3.2 anthro emissions of '+spec
  ncdf_attput,ncid,/GLOBAL,/float,'molecular_weight',mw_svoc
  ncdf_attput,ncid,/GLOBAL,/char,'data_creator','Louisa Emmons (emmons@ucar.edu)'
  ncdf_attput,ncid,/GLOBAL,/char,'data_summary','Precursor of SOA for VBS scheme, based on POM(OC).'
  ncdf_attput,ncid,/GLOBAL,/char,'data_source','HTAPv3.2 anthropogenic emissions mosaic (https://zenodo.org/records/17086684). Original files: edgar_HTAPv32_YYYY_NMVOC.nc. Speciated according to NMVOC_speciation_HTAP_v3.xls (https://edgar.jrc.ec.europa.eu/dataset_htap_v32#p3).'
  ncdf_attput,ncid,/GLOBAL,/char,'creation_date',creation_date
  thisfile = Routine_filepath()
  ncdf_attput,ncid,/GLOBAL,/char,'data_script',thisfile

  ncdf_control,ncid,/ENDEF

  ncdf_varput,ncid,'lon',lon
  ncdf_varput,ncid,'lat',lat
  ncdf_varput,ncid,'time',time
  ncdf_varput,ncid,'date',date
  ncdf_varput,ncid,varname,emis_svoc
  ncdf_close,ncid

end
