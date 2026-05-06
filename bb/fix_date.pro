; change dates from Jan 15 to Jan 1 2003, Dec 15,2023 to Jan 1, 2024

pro fix_date


  path_emis = '/glade/campaign/acom/acom-weather/emmons/HTAP3/emissions/gfas4htap/mozart/f09/'

  files_emis = File_search(path_emis+'gfas4htap-moz_*_bb_2003-2023_f09_c20260306.nc', count = nfiles)

 for ifile=0,nfiles-1 do begin


  file1 = files_emis[ifile]
  print,ifile,' ',file1
  ncid = ncdf_open(file1,/write)
  ncdf_varget,ncid,'date',date
  ncdf_varget,ncid,'time',time
  ntim = n_elements(date)
  print, date[0],time[0], date[ntim-1], time[ntim-1]
  date[0] = 20030101
  time_new = time
  time_new[0] = 19358.
  date[ntim-1] = 20240101
  time_new[ntim-1] = 27028.
  print, date[0], date[ntim-1],time_new[0],time_new[ntim-1]
 
  ncdf_varput,ncid,'date',date
  ncdf_varput,ncid,'time',time_new
  ncdf_close,ncid
endfor



end
