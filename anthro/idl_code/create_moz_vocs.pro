pro create_moz_vocs

  ; output directory
  path_out = '/glade/campaign/acom/acom-weather/emmons/HTAP3/emissions/anthro_v3.2/cesm_ready/'
  ;date_created = '20260116' ; incorrectly included Ag Waste Burning
  date_created = '20260409'
  
  ; Total VOC emissions for each sector at 0.9x1.25deg
  file_nmvoc = '/glade/campaign/acom/acom-weather/emmons/HTAP3/emissions/anthro_v3.2/f09/2000-2020_kg/HTAPv3.2_NMVOC_anthro-sectors_2000-2020_f09_kg_c20251203.nc'

  ; file of VOC speciation factors for each sector, for several regions
  ; created for MOZART species from NMVOC_speciation_HTAP_v3.xls from https://edgar.jrc.ec.europa.eu/dataset_htap_v32#p3
  file_htap_moz = '/glade/u/home/emmons/EMISSIONS/HTAP/MOZART_VOCspeciation_forHTAP3_c20260116.csv'
  sdum=' '

  nreg = 5
  regions = ['Asia', 'NorthAmerica', 'Europe', 'Other', 'World']
  sectors0 = ['HTAPv3_1_International_Shipping', 'HTAPv3_3_Energy', 'HTAPv3_4_1_Industry', 'HTAPv3_4_2_Fugitive', $
             'HTAPv3_4_3_Solvents', 'HTAPv3_5_1_Road_Transport', 'HTAPv3_5_3_Domestic_shipping', $
             'HTAPv3_5_4_Other_ground_transport', 'HTAPv3_6_Residential', 'HTAPv3_7_Waste', $
             'HTAPv3_8_2_Agriculture_livestock', 'HTAPv3_8_3_Agriculture_crops']
             ;'HTAPv3_8_1_Agricultural_waste_burning', 
  sectors = Strlowcase(sectors0)
  nsectors = n_elements(sectors)
  out_varlist = Strjoin(sectors0,'+')
  
  openr,jlun,file_htap_moz, /get_lun
  readf,jlun,sdum
  print,sdum
  readf,jlun,sdum
  print,sdum
  colnames = strsplit(sdum,',',/extract)
  ;for i=0,n_elements(colnames)-1 do print,i,' ',colnames[i]
  nspec = n_elements(colnames)-3
  species = strtrim(colnames[3:(n_elements(colnames)-1)], 2)
  for i=0,nspec-1 do print,i,' ',species[i]
  
  factors = fltarr(nspec,nsectors,nreg)
  help,factors
  stop
  
  while not eof(jlun) do begin 
     readf,jlun,sdum
     ;print,sdum
     dataline = strsplit(sdum,',',/extract)
     ;print,dataline[0],' ',dataline[1],' ',dataline[2]
     region = Strcompress(dataline[0],/remove_all)
     code0 = Strjoin(Strsplit(dataline[1],'.',/extract),'_')
     code = 'HTAPv3'+Strmid(code0,4)
     name = Strjoin(Strsplit(dataline[2],' ',/extract),'_')
     sector = Strlowcase(code+'_'+name)
     ireg = where(regions eq region) & ireg=ireg[0]
     if (ireg lt 0) then print,'bad region: ', region
     isect = where(sectors eq sector) & isect=isect[0]
     if (isect ge 0) then begin
        data = float(dataline[3:(nspec+2)])
        ;print,isect,' ',sectors[isect]
        factors[*,isect,ireg] = data
        ;print,reform(factors[*,isect,ireg])
     endif else print,'not using: ',sector
  endwhile
  free_lun,jlun

  for ireg=0,4 do begin
   print,regions[ireg]
   for ispec=0,nspec-1 do begin
     print,species[ispec],' ',reform(factors[ispec,*,ireg])
   endfor
  endfor

  print,'Molecular Weights: '
  molwts = fltarr(nspec)
  openr,ilun,'/glade/u/home/emmons/EMISSIONS/species_molwts.csv',/get_lun
  sdum = ' '
  readf,ilun,sdum
  while not eof(ilun) do begin
   readf,ilun,sdum
   parts = strsplit(sdum,',',/extract)
   ind = where(species eq strtrim(parts[0],2))
   if (ind[0] ge 0) then molwts[ind[0]] = float(parts[1])
  endwhile
  free_lun,ilun
  for ispec = 0,nspec-1 do begin
    mw = molwts[ispec]
    if (mw le 0.) then begin
     read,mw,prompt='MW missing, enter new value: '
     molwts[ispec] = mw
    endif
    print,species[ispec],molwts[ispec]
  endfor  

  stop

  ; get array of regions for f09
  get_map_region, map_region

; create emissions for each species - scale each sector depending on region

ncid_v = ncdf_open(file_nmvoc)
ncdf_varget,ncid_v, 'lon',lon
ncdf_varget,ncid_v, 'lat',lat
ncdf_varget,ncid_v, 'time',time
ncdf_attget,ncid_v, 'time', 'units',time_units
ncdf_varget,ncid_v, 'date',date
nlon = n_elements(lon)
nlat = n_elements(lat)
ntim = n_elements(time)

for ispec = 0,nspec-1 do begin
   spec = species[ispec]
   mw = molwts[ispec]
   print,spec,mw
   file_spec = path_out+'HTAPv32_'+spec+'_anthro_2000-2020_f09_c'+date_created+'.nc'
   print,'creating: ',file_spec
   ncid_s = ncdf_create(file_spec, /netcdf4_format)
     lonid = ncdf_dimdef(ncid_s, 'lon', nlon)
     latid = ncdf_dimdef(ncid_s, 'lat', nlat)
     timid = ncdf_dimdef(ncid_s, 'time', /unlimited)
     varid = ncdf_vardef(ncid_s, 'lon', [lonid], /float)
     ncdf_attput,ncid_s,'lon','units','degrees_east'
     ncdf_attput,ncid_s,'lon','long_name','Longitude'
     varid = ncdf_vardef(ncid_s, 'lat', [latid], /float)
     ncdf_attput,ncid_s,'lat','units', 'degrees_north'
     ncdf_attput,ncid_s,'lat','long_name', 'Latitude'
     varid = ncdf_vardef(ncid_s, 'time', [timid], /float)
     ncdf_attput,ncid_s,'time','units', String(time_units)
     ncdf_attput,ncid_s,'time','long_name', 'Time'
     varid = ncdf_vardef(ncid_s, 'date', [timid], /long)
     ncdf_attput,ncid_s, 'date', 'units', 'YYYYMMDD', /string
     ncdf_attput,ncid_s, 'date', 'long_name', 'date', /string
     varid = ncdf_vardef(ncid_s, 'anthro', [lonid,latid,timid], /float)
     ncdf_attput,ncid_s, 'anthro', 'units', 'molecules cm-2 s-1', /string
     ncdf_attput,ncid_s, 'anthro', 'long_name', spec+' anthro emissions', /string
     ncdf_attput,ncid_s,/GLOBAL,/char,'data_title','HTAPv3.2 anthro emissions of '+spec
     ncdf_attput,ncid_s,/GLOBAL,/float,'molecular_weight',mw
     ncdf_attput,ncid_s,/GLOBAL,/char,'data_creator','Louisa Emmons (emmons@ucar.edu)'
     ncdf_attput,ncid_s,/GLOBAL,/char,'data_summary','HTAPv3.2 anthropogenic emissions mosaic (https://zenodo.org/records/17086684). Original files: edgar_HTAPv32_YYYY_NMVOC.nc. Speciated according to NMVOC_speciation_HTAP_v3.xls (https://edgar.jrc.ec.europa.eu/dataset_htap_v32#p3).'
     ncdf_attput,ncid_s,/GLOBAL,/char,'sectors_summed', out_varlist
     ncdf_attput,ncid_s,/GLOBAL,/char,'creation_date',date_created
     thisfile = Routine_filepath()
     ncdf_attput,ncid_s,/GLOBAL,/char,'data_script',thisfile

     ncdf_control, ncid_s, /endef

     anthro = fltarr(nlon,nlat,ntim)
     for isect = 0,nsectors-1 do begin
        ncdf_varget,ncid_v, sectors0[isect],data_sect1
        for ilon=0,nlon-1 do begin
           for ilat=0,nlat-1 do begin
              ireg = map_region[ilon,ilat]
              voc = data_sect1[ilon,ilat,*] * factors[ispec,isect,ireg]
              voc_w = data_sect1[ilon,ilat,*] * factors[ispec,isect,4] ;world region
              anthro[ilon,ilat,*] = anthro[ilon,ilat,*] + voc + voc_w
           endfor
        endfor
        print,sectors0[isect],anthro[220,138,0]  ; a point in eastern US
     endfor
     
     ncdf_varput,ncid_s,'lon',lon
     ncdf_varput,ncid_s,'lat',lat
     ncdf_varput,ncid_s,'time',time
     ncdf_varput,ncid_s,'date',date
     ncdf_varput,ncid_s,'anthro',anthro
     ncdf_close, ncid_s

  endfor 


end

pro get_map_region,  map_region

  ncid = ncdf_open('/glade/work/emmons/ic/template_0.9x1.25_L32.nc')
  ncdf_varget,ncid, 'lon',lon
  ncdf_varget,ncid, 'lat',lat
  ncdf_close,ncid
  nlon = n_elements(lon)
  nlat = n_elements(lat)
  map_region = intarr(nlon,nlat)
  
  regions = ['Asia', 'NorthAmerica', 'Europe', 'Other']
  map_region[*,*] = 3

  for ireg = 0,2 do begin
     reg = regions[ireg]
     case reg of
        'Asia': begin
           latmin=0
           latmax=90
           lonmin=60
           lonmax=180
        end
        'NorthAmerica': begin
           latmin=0
           latmax=90
           lonmin=180
           lonmax=330
        end
        'Europe': begin
           latmin=30
           latmax=90
           lonmin=-30
           lonmax=60
        end
     endcase

     indlat = where(lat ge latmin and lat le latmax)
     if (lonmin gt 0) then begin
         indlon = where(lon ge lonmin and lon lt lonmax)
     endif else begin
         indl1 = where(lon ge (lonmin+360) and lon le 360)
         indl2 = where(lon ge 0 and lon lt lonmax)
         indlon = [indl2,indl1]
     endelse

     for ilat = 0,n_elements(indlat)-1 do begin
        map_region[indlon,indlat[ilat]] = ireg
     endfor
  endfor
end

pro map_regions

  ncid = ncdf_open('/glade/work/emmons/ic/template_0.9x1.25_L32.nc')
  ncdf_varget,ncid, 'lon',lon
  ncdf_varget,ncid, 'lat',lat
  ncdf_close,ncid
  nlon = n_elements(lon)
  nlat = n_elements(lat)
  map_region = intarr(nlon,nlat)
  
  regions = ['Asia', 'NorthAmerica', 'Europe', 'Other']
  map_region[*,*] = 3

  for ireg = 0,2 do begin
     reg = regions[ireg]
     print, reg
     case reg of
        'Asia': begin
           latmin=0
           latmax=90
           lonmin=60
           lonmax=180
        end
        'NorthAmerica': begin
           latmin=0
           latmax=90
           lonmin=180
           lonmax=330
        end
        'Europe': begin
           latmin=30
           latmax=90
           lonmin=-30
           lonmax=60
        end
     endcase

     indlat = where(lat ge latmin and lat le latmax)
     print,lat[indlat]
     if (lonmin gt 0) then begin
         indlon = where(lon ge lonmin and lon lt lonmax)
     endif else begin
         indl1 = where(lon ge (lonmin+360) and lon le 360)
         indl2 = where(lon ge 0 and lon lt lonmax)
         indlon = [indl2,indl1]
     endelse
     print,lon[indlon]

     for ilat = 0,n_elements(indlat)-1 do begin
        map_region[indlon,indlat[ilat]] = ireg
     endfor
  endfor

     loadct,3
     map_set,0,0,/continents
     colors = [50,100,150,250]
     syms = [1,4,5,6]
     for ilon=0,nlon-1 do begin
        for ilat = 0,nlat-1 do begin
           jreg = map_region[ilon,ilat]
           plots,lon[ilon],lat[ilat],color=colors[jreg],psym=syms[jreg] 
        endfor
     endfor 
         

end
