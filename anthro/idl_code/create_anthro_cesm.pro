; create CESM-ready emissions files for HTAP3 of base species
;   read files for each species for each year, 
;   sum sectors leaving out Aviation and Ag waste burning 
;   concatenate
;   create date and time variables
;   convert from kg/m2/s to molecules/cm2/s
;   shift lon from -180 - 180 to 0-360

pro create_anthro_cesm

  path_orig = '/glade/campaign/acom/acom-weather/emmons/HTAP3/emissions/anthro_v3.2/monthly/'
  path_out = '/glade/campaign/acom/acom-weather/emmons/HTAP3/emissions/anthro_v3.2/monthly_combined/0.1deg/'

  species = [ 'BC', 'CO', 'NH3', 'NOx', 'OC', 'SO2' ]
  mws =     [  12,   28,    17,    46,   12,   64 ]   ;g/mole
  Navog = 6.022E23
  
  for ispec = 0, n_elements(species)-1 do begin
     spec = species[ispec]
     mw = mws[ispec]

     file_new = path_out+'HTAPv32_'+spec+'_anthro_2000-2020_01x01.nc'
     print,'creating: ',file_new
     ncid2 = ncdf_create(file_new, /netcdf4_format)

     nlon = 3600
     nlat = 1800
     ntim = 12*21
     help,ntim
     date = lonarr(ntim)
     time_all = fltarr(ntim)
     time_all_units = "days since 1750-01-01 00:00:00"
     anthro_all = fltarr(nlon,nlat,ntim)
     lon_shift = findgen(3600)*0.1 + 0.05

     for yr=2000,2020 do begin
        file_sp_y = path_orig + 'edgar_HTAPv32_'+string(yr,format='(i4)')+'_'+spec+'.nc'
        print, file_sp_y
        
        ncid = ncdf_open(file_sp_y)
        ncdf_varget,ncid,'lon',lon
        ncdf_varget,ncid,'lat',lat
        ncdf_varget,ncid,'time',time1
        ncdf_attget,ncid,'time','units',time_units
        print, min(time1),max(time1),String(time_units)

        for imon = 0,11 do begin
           jtim = (yr-2000)*12 + imon
           time_all[jtim] = julday((imon+1),15,yr) - Julday(1,1,1750)
           date[jtim] = yr*10000L + (imon+1)*100 + 15
           print,jtim, date[jtim], time_all[jtim]
        endfor
        
        inq = ncdf_inquire(ncid)
        varlist = ['']
        for ivar = 0,inq.nvars-1 do begin
           vinq = ncdf_varinq(ncid, ivar)
           if (vinq.ndims eq 3) then begin
              if ((strpos(vinq.name, 'Aviation') lt 0) and $
              (strpos(vinq.name, 'Agricultural_waste_burning') lt 0)) then varlist = [varlist, vinq.name]
           endif
        endfor
        varlist = varlist[1:(n_elements(varlist)-1)]
        
        help,varlist
        print,varlist
        
        for ivar = 0,n_elements(varlist)-1 do begin
           print,varlist[ivar]
           ncdf_varget,ncid, varlist[ivar], var1
           ;help,var1
           if (ivar eq 0) then anthro_kg = var1 else anthro_kg = anthro_kg+var1
           print,max(anthro_kg)
        endfor
        ncdf_close, ncid
        help,anthro_kg

        ; convert from kg/m2 to molecules/cm2
        ; (molecules/mole) /(kg/mole) * (m2/cm2)
        ; and shift lon
        sf = Navog /(mw * 1.E-3) * 1.E-4
        jtim1 = (yr-2000)*12
        jtim2 = (yr-2000)*12 + 11
        print,jtim1,jtim2
        anthro_all[0:1799,*,jtim1:jtim2] = anthro_kg[1800:3599,*,*] *sf
        anthro_all[1800:3599,*,jtim1:jtim2] = anthro_kg[0:1799,*,*] *sf
     endfor

     out_varlist = Strjoin(varlist,'+')
     
     lonid = ncdf_dimdef(ncid2, 'lon', n_elements(lon))
     latid = ncdf_dimdef(ncid2, 'lat', n_elements(lat))
     timid = ncdf_dimdef(ncid2, 'time', /unlimited)
     varid = ncdf_vardef(ncid2, 'lon', [lonid], /float)
     ncdf_attput,ncid2,'lon','units','degrees_east'
     ncdf_attput,ncid2,'lon','long_name','Longitude'
     varid = ncdf_vardef(ncid2, 'lat', [latid], /float)
     ncdf_attput,ncid2,'lat','units', 'degrees_north'
     ncdf_attput,ncid2,'lat','long_name', 'Latitude'
     varid = ncdf_vardef(ncid2, 'time', [timid], /float)
     ncdf_attput,ncid2,'time','units', time_all_units
     ncdf_attput,ncid2,'time','long_name', 'Time'
     varid = ncdf_vardef(ncid2, 'date', [timid], /long)
     ncdf_attput,ncid2, 'date', 'units', 'YYYYMMDD', /string
     ncdf_attput,ncid2, 'date', 'long_name', 'date', /string
     varid = ncdf_vardef(ncid2, 'anthro', [lonid,latid,timid], /float)
     ncdf_attput,ncid2, 'anthro', 'units', 'molecules cm-2 s-1', /string
     ncdf_attput,ncid2, 'anthro', 'long_name', spec+' anthro emissions', /string

     ncdf_attput,ncid2,/GLOBAL,/char,'data_title','HTAPv3.2 anthro emissions of '+spec
     ncdf_attput,ncid2,/GLOBAL,/float,'molecular_weight',mw
     ncdf_attput,ncid2,/GLOBAL,/char,'data_creator','Louisa Emmons (emmons@ucar.edu)'
     ncdf_attput,ncid2,/GLOBAL,/char,'data_summary','HTAPv3.2 anthropogenic emissions mosaic (https://zenodo.org/records/17086684). Original files: edgar_HTAPv32_YYYY_'+spec+'.nc'
     ncdf_attput,ncid2,/GLOBAL,/char,'sectors_summed', out_varlist
     ncdf_attput,ncid2,/GLOBAL,/char,'creation_date','2026-01-14'
     thisfile = Routine_filepath()
     ncdf_attput,ncid2,/GLOBAL,/char,'data_script',thisfile     
     
     ncdf_control, ncid2, /endef

     ncdf_varput,ncid2,'lon',lon_shift
     ncdf_varput,ncid2,'lat',lat
     ncdf_varput,ncid2,'time',time_all
     ncdf_varput,ncid2,'date',date
     ncdf_varput,ncid2,'anthro',anthro_all
     ncdf_close, ncid2

     print,'closed: ',file_new
  endfor

end

  
