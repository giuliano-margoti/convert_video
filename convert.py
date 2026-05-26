# -*- coding: utf-8 -*-
import os
import types
import numpy as np
import cv2
import astropy.io.fits as fits
from astropy.time import Time, TimeDelta
from tqdm import tqdm


class SERReader(object):
    def __init__(self, fname):
        self.fname = fname
        self.header = types.SimpleNamespace()
        with open(self.fname, "rb") as f:
            self.header.fileID = f.read(14).decode()
            self.header.luID = int.from_bytes(f.read(4), byteorder='little')
            self.header.colorID = int.from_bytes(f.read(4), byteorder='little')
            
            if self.header.colorID < 99:
                self.header.numPlanes = 1
            else:
                self.header.numPlanes = 3
                
            self.header.littleEndian = int.from_bytes(f.read(4), byteorder='little')
            self.header.imageWidth = int.from_bytes(f.read(4), byteorder='little')
            self.header.imageHeight = int.from_bytes(f.read(4), byteorder='little')
            self.header.PixelDepthPerPlane = int.from_bytes(f.read(4), byteorder='little')
            
            if self.header.PixelDepthPerPlane == 8:
                self.dtype = np.uint8
            elif self.header.PixelDepthPerPlane == 16:
                self.dtype = np.uint16
            
            self.header.frameCount = int.from_bytes(f.read(4), byteorder='little')
            self.header.observer = f.read(40).decode().strip('\x00').strip()
            self.header.instrument = f.read(40).decode().strip('\x00').strip()
            self.header.telescope = f.read(40).decode().strip('\x00').strip()
            self.header.dateTime = int.from_bytes(f.read(8), byteorder='little')
            
            self.imgSizeBytes = int(self.header.imageHeight * self.header.imageWidth * self.header.PixelDepthPerPlane * self.header.numPlanes / 8)
            self.imgNum = 0
        
    def getImg(self, imgNum=None):
        if imgNum is not None:
            self.imgNum = imgNum
            
        with open(self.fname, "rb") as f:
            f.seek(int(178 + self.imgNum * self.imgSizeBytes))
            frame_data = f.read(self.imgSizeBytes)
            if not frame_data:
                return None
            frame = np.frombuffer(frame_data, dtype=self.dtype)
            
        self.imgNum += 1
        frame = np.reshape(frame, (self.header.imageHeight, self.header.imageWidth, self.header.numPlanes))
        return frame


def salvar_fits(data, n, name_output, validacao, output_dir, start_time=None, end_time=None, mid_time=None, cycle_time=None, exposure_time=None, ser_header=None):
    hdu = fits.PrimaryHDU(data)
    
    if validacao.upper() == 'S':
        obs_time_start = start_time + TimeDelta(n * cycle_time, format="sec")
        hdu.header["DATE-OBS"] = (obs_time_start.isot, "Tempo do inicio da exposicao")
        
        obs_time_end = end_time + TimeDelta(n * cycle_time, format="sec")
        hdu.header["DATE-END"] = (obs_time_end.isot, "Tempo do fim da exposicao")
        
        obs_time_mid = mid_time + TimeDelta(n * cycle_time, format="sec")
        hdu.header["DATE-MID"] = (obs_time_mid.isot, "Tempo do meio da exposicao")
        
        hdu.header["EXPTIME"] = (exposure_time, "Tempo de exposicao [s]")    
        hdu.header["CYCLE"]   = (cycle_time, "Tempo entre frames [s]")
        hdu.header["OBJECT"]  = (name_output, "")    

        nome_tempo = obs_time_start.isot.replace(":", "-")
        file_name = f"{name_output}_{nome_tempo}_{n:06d}.fits"
        
    else:
        file_name = f"{name_output}_{n:06d}.fits"

    if ser_header:
        hdu.header['FRAME'] = n
        hdu.header['INSTRUME'] = ser_header.instrument
        hdu.header['TELESCOP'] = ser_header.telescope
        hdu.header['OBSERVER'] = ser_header.observer

    file_path = os.path.join(output_dir, file_name)
    hdu.writeto(file_path, overwrite=True)
    return file_name


if __name__ == '__main__':
    inn_video = str(input("Nome do arquivo de vídeo (com a extensão .avi ou .ser): "))
    name_output = str(input("Nome do objeto observado: "))

    _, extensao = os.path.splitext(inn_video)
    extensao = extensao.lower()

    start_time, end_time, mid_time, exposure_time, cycle_time = None, None, None, None, None

    validacao = ''
    while validacao.upper() not in ['S', 'N']:
        validacao = str(input("Adicionar tempo no header? (s/n): "))
        if validacao.upper() == 'S':
            while True:
                ref_time_ins = str(input("Tempo de inicio (i), meio (m) ou fim (f) da exposição? "))
                
                exposure_time = float(input("Tempo de exposição (s): "))
                cycle_time = float(input("Tempo de ciclo (s): ")) 
                
                hora = int(input('Hora: '))
                minu = int(input('Minuto: '))
                segu = float(input('Segundo: '))
                diaa = int(input('Dia: '))
                mess = int(input('Mês: '))
                anoo = int(input('Ano: '))
                
                if ref_time_ins.upper() == 'I':
                    start_time = Time(f"{anoo}-{mess:02d}-{diaa:02d}T{hora:02d}:{minu:02d}:{segu:.3f}", format="isot", scale="utc")
                    end_time = Time(f"{anoo}-{mess:02d}-{diaa:02d}T{hora:02d}:{minu:02d}:{segu+exposure_time:.3f}", format="isot", scale="utc")
                    mid_time = Time(f"{anoo}-{mess:02d}-{diaa:02d}T{hora:02d}:{minu:02d}:{segu+(exposure_time/2):.3f}", format="isot", scale="utc")
                    break
                    
                elif ref_time_ins.upper() == 'M':
                    start_time = Time(f"{anoo}-{mess:02d}-{diaa:02d}T{hora:02d}:{minu:02d}:{segu:.3f}", format="isot", scale="utc") - TimeDelta(exposure_time/2, format="sec")
                    end_time = Time(f"{anoo}-{mess:02d}-{diaa:02d}T{hora:02d}:{minu:02d}:{segu+exposure_time:.3f}", format="isot", scale="utc")  - TimeDelta(exposure_time/2, format="sec")
                    mid_time = Time(f"{anoo}-{mess:02d}-{diaa:02d}T{hora:02d}:{minu:02d}:{segu+(exposure_time/2):.3f}", format="isot", scale="utc") - TimeDelta(exposure_time/2, format="sec")
                    break

                elif ref_time_ins.upper() == 'F':
                    start_time = Time(f"{anoo}-{mess:02d}-{diaa:02d}T{hora:02d}:{minu:02d}:{segu:.3f}", format="isot", scale="utc") - TimeDelta(exposure_time, format="sec")
                    end_time = Time(f"{anoo}-{mess:02d}-{diaa:02d}T{hora:02d}:{minu:02d}:{segu+exposure_time:.3f}", format="isot", scale="utc") - TimeDelta(exposure_time, format="sec")
                    mid_time = Time(f"{anoo}-{mess:02d}-{diaa:02d}T{hora:02d}:{minu:02d}:{segu+(exposure_time/2):.3f}", format="isot", scale="utc") - TimeDelta(exposure_time, format="sec")
                    break
                else:
                    print('Informe apenas i, m ou f')

        elif validacao.upper() == 'N':
            print('Tempos ignorados.')
        else:
            print('\nEscreva apenas s ou n\n')
            
    print('Configurações de tempo definidas.\n')

    output_dir = 'frames_fits'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    n = 1
    
    if extensao in ['.avi', '.mp4']:
        video = cv2.VideoCapture(inn_video)
        
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        sucess, image = video.read() 
        
        print(f"Iniciando conversão de {total_frames} frames do vídeo padrão...")
        
        with tqdm(total=total_frames, desc="Salvando FITS", unit="frame") as pbar:
            while sucess:
                image_sum = np.mean(image, axis=2)
                data = image_sum[::-1]
                
                salvar_fits(data, n, name_output, validacao, output_dir, start_time, end_time, mid_time, cycle_time, exposure_time)
                
                n += 1
                sucess, image = video.read()
                pbar.update(1) 
            
    elif extensao == '.ser':
        ser = SERReader(inn_video)
        print(f"Iniciando conversão de {ser.header.frameCount} frames do arquivo SER...")
        
        for n_frame in tqdm(range(ser.header.frameCount), desc="Salvando FITS", unit="frame"):
            frame = ser.getImg()
            if frame is None:
                break
            
            if ser.header.numPlanes == 1:
                data = frame[:, :, 0]
            else:
                data = np.transpose(frame, (2, 0, 1))
                
            salvar_fits(data, n, name_output, validacao, output_dir, start_time, end_time, mid_time, cycle_time, exposure_time, ser_header=ser.header)
            
            n += 1

    else:
        print(f"Erro: Extensão de arquivo '{extensao}' não suportada. Use .avi ou .ser.")

    print("\nProcessamento concluído com sucesso!")
