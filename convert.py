import numpy as np
import pylab as pl
import cv2
import os
import astropy.io.fits as fits
from astropy.time import Time, TimeDelta

inn_video = str(input("Nome do arquivo de vídeo: "))
name_output = str(input("Nome do arquivo de saída: "))

video = cv2.VideoCapture(inn_video)


# ===== Header =====

validacao = ''
while validacao.upper() not in ['S', 'N']:

    validacao = str(input("tempo de no header? s/n: "))
    print(validacao, validacao.upper())
    if validacao.upper() == 'S':

        exposure_time = float(input("tempo de exposição: "))
        cycle_time = float(input("tempo de ciclo: ")) 
        
        hora = int(input('hora: '))
        minu = int(input('minuto: '))
        segu = float(input('segundo: '))
        diaa = int(input('dia: '))
        mess = int(input('mês: '))
        anoo = int(input('ano: '))

        start_time = Time(f"{anoo}-{mess}-{diaa}T{hora}:{minu}:{segu:.3f}", format="isot", scale="utc")

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
    
    file_name = f"{name_output}_{n:06d}.fits"
    
    hdu = fits.PrimaryHDU(data)
    
    if validacao.upper() == 'S':
    
        obs_time = start_time + TimeDelta(n * cycle_time, format="sec")
    
        hdu.header["EXPTIME"] = (exposure_time, "Tempo de exposicao [s]")    
        hdu.header["CYCLE"]   = (cycle_time, "Tempo entre frames [s]")    
        hdu.header["DATE-OBS"] = (obs_time.isot, "Tempo do inicio da exposicao")
    
        print(f"Salvo: {file_name} - Time {obs_time.isot}")
        
    elif validacao.upper() == 'N':
        print(f"Salvo: {file_name}")

    hdu.writeto(file_name, overwrite=True)
    
    n += 1
    sucess, image = video.read()
