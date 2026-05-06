
; rewrite date of last time in file (2020/12/15) to be Jan 1 of next year

pro add_jan1


path_emis= '/glade/campaign/acom/acom-weather/emmons/HTAP3/emissions/anthro_v3.2/cesm_ready/netcdf4/'
files = File_search(path_emis+'HTAPv32*.nc', count=nfiles)
print,nfiles

varname = 'anthro'
newdate = 20210101L
;time:units = "days since 1950-01-01 00:00:00" ;
newtime = Julday(1,1,2021) - Julday(1,1,1950)
print,newdate,newtime

for ifile=0,nfiles-1 do begin

  file1 = files[ifile]
  print,ifile,' ',file1
  ncid = ncdf_open(file1,/write)
  ncdf_varget,ncid,'lon',lon
  ncdf_varget,ncid,'lat',lat
  ncdf_varget,ncid,'date',date
  ncdf_varget,ncid,'time',time
  ncdf_varget,ncid,varname,emis
  nlon = n_elements(lon)
  nlat = n_elements(lat)
  ntim = n_elements(time)
  
  print,date[ntim-1]
  print,time[ntim-1]  ;25916
  
  time[ntim-1] = newtime
  date[ntim-1] = newdate

  ncdf_varput,ncid,'date',date
  ncdf_varput,ncid,'time',time
  ncdf_close,ncid

endfor


end

