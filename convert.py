import numpy as np
import pylab as pl
import cv2
import os
import astropy.io.fits as fits
from astropy.time import Time, TimeDelta

inn_video = str(input("Nome do arquivo de vídeo: "))
name_output = str(input("Nome do objeto observado: "))

video = cv2.VideoCapture(inn_video)

validacao = ''
while validacao.upper() not in ['S', 'N']:

    validacao = str(input("tempo de no header? s/n: "))
    if validacao.upper() == 'S':
    	
    	while True:
    	
            ref_time_ins = str(input("tempo de inicio (i), meio (m) ou fim (f) da exposição? "))
        
            exposure_time = float(input("tempo de exposição: "))
            cycle_time = float(input("tempo de ciclo: ")) 
        
            hora = int(input('hora: '))
            minu = int(input('minuto: '))
            segu = float(input('segundo: '))
            diaa = int(input('dia: '))
            mess = int(input('mês: '))
            anoo = int(input('ano: '))
            
            if ref_time_ins.upper() == 'I':

                start_time = Time(f"{anoo}-{mess}-{diaa}T{hora}:{minu}:{segu:.3f}", format="isot", scale="utc")
                end_time = Time(f"{anoo}-{mess}-{diaa}T{hora}:{minu}:{segu+exposure_time:.3f}", format="isot", scale="utc")
                mid_time = Time(f"{anoo}-{mess}-{diaa}T{hora}:{minu}:{segu+(exposure_time/2):.3f}", format="isot", scale="utc")
                
                break
                
            elif ref_time_ins.upper() == 'M':

                start_time = Time(f"{anoo}-{mess}-{diaa}T{hora}:{minu}:{segu:.3f}", format="isot", scale="utc") - TimeDelta(exposure_time/2, format="sec")
                end_time = Time(f"{anoo}-{mess}-{diaa}T{hora}:{minu}:{segu+exposure_time:.3f}", format="isot", scale="utc")  - TimeDelta(exposure_time/2, format="sec")
                mid_time = Time(f"{anoo}-{mess}-{diaa}T{hora}:{minu}:{segu+(exposure_time/2):.3f}", format="isot", scale="utc") - TimeDelta(exposure_time/2, format="sec")
                
                break

            elif ref_time_ins.upper() == 'F':

                start_time = Time(f"{anoo}-{mess}-{diaa}T{hora}:{minu}:{segu:.3f}", format="isot", scale="utc") - TimeDelta(exposure_time, format="sec")
                end_time = Time(f"{anoo}-{mess}-{diaa}T{hora}:{minu}:{segu+exposure_time:.3f}", format="isot", scale="utc") - TimeDelta(exposure_time, format="sec")
                mid_time = Time(f"{anoo}-{mess}-{diaa}T{hora}:{minu}:{segu+(exposure_time/2):.3f}", format="isot", scale="utc") - TimeDelta(exposure_time, format="sec")
                
                break
            
            else:
                print('Informe apenas i, m ou f')

    elif validacao.upper() == 'N':
    
        print('tempos ignorados')
        
    else:
        
        print('\nescreva apenas s ou n\n')
        
        
print('Tempos definido')



n = 1
sucess, image = video.read() 

while sucess == True:
    image_sum = np.mean(image, axis=2)
    data = image_sum[::-1]
    
    hdu = fits.PrimaryHDU(data)
    
    if validacao.upper() == 'S':
    
        obs_time = start_time + TimeDelta(n * cycle_time, format="sec")
        hdu.header["DATE-OBS"] = (obs_time.isot, "Tempo do inicio da exposicao")
        
        file_name = f"{name_output}_{obs_time}_{n:06d}.fits"
        
        obs_time = end_time + TimeDelta(n * cycle_time, format="sec")
        hdu.header["DATE-END"] = (obs_time.isot, "Tempo do inicio da exposicao")
        
        obs_time = mid_time + TimeDelta(n * cycle_time, format="sec")
        hdu.header["DATE-MID"] = (obs_time.isot, "Tempo do inicio da exposicao")
        
        hdu.header["EXPTIME"] = (exposure_time, "Tempo de exposicao [s]")    
        hdu.header["CYCLE"]   = (cycle_time, "Tempo entre frames [s]")
        
        hdu.header["OBJECT"]   = (name_output, "")    
    
        print(f"Salvo: {file_name} - Time {obs_time.isot}")
        
    elif validacao.upper() == 'N':
    
        file_name = f"{name_output}_{n:06d}.fits"
        print(f"Salvo: {file_name}")

    hdu.writeto(file_name, overwrite=True)
    
    n += 1
    sucess, image = video.read()
