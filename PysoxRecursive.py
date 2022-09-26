import sox
import os

#Define input and output dirs in your PC
INPUT_DIR = r'C:\Users\magan\Desktop\WAVFORMATFIXER\INPUT2' #no slash at end!
OUTPUT_DIR = r'C:\Users\magan\Desktop\WAVFORMATFIXER\OUTPUT2'

#Define SoX format conversion parameters
SAMPLE_RATE = 44100
ENCODING = 'ms-adpcm'
QUALITY = 'v' # change to 'h' for high, 'v' for very high

def format_convert(filename: str) -> str:
    trnsf = sox.Transformer() #define transformer
    trnsf.set_output_format(encoding=ENCODING)
    trnsf.rate(quality='v',samplerate=SAMPLE_RATE)
    output_file = filename.replace(INPUT_DIR, OUTPUT_DIR).replace('.ogg','.wav')
    outdir = output_file.rsplit('\\', maxsplit=1)[0]
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    trnsf.build_file(input_filepath=filename, output_filepath=output_file)
    return f'{filename} converted successfully'

archivos = []

for subdir, dirs, files in os.walk(INPUT_DIR):
    for file in files:
        if file.endswith('.wav') or file.endswith('.ogg'):
            archivos.append(os.path.join(subdir,file))
            format_convert(os.path.join(subdir,file))
