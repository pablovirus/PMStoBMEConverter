import os
import binascii

#Change the following to your IIDX 'sound' dir
rootdir = r'C:\GamesC\Heroic Verse Popn C\contents\data\sound'


#Reorder HEX data to change Hyper chart into Another and Another into Leggendaria
for subdir, dirs, files in os.walk(rootdir):
    for file in files:
        flagfile = 'flag' + file[:-2] + '.txt'
        if file.endswith('.1') and not flagfile in files:
            print(f'Workign on file: {file}')
            with open(os.path.join(subdir, file), 'rb') as file_b:
                read_data = file_b.read()
                hex_data = binascii.hexlify(read_data)
                hyper_chart = hex_data[0:16]
                another_chart = hex_data[32:32+16]
                rest_of_file = hex_data[80:]
                replacement_hex = b''.join([
                    bytes('0'*16, 'ascii'),
                    bytes('0'*16, 'ascii'),
                    hyper_chart,
                    bytes('0'*16, 'ascii'),
                    another_chart,
                    rest_of_file,
                    ])
            with open(os.path.join(subdir, file), 'wb') as output_file:
                output_file.write(binascii.unhexlify(replacement_hex))
                print(f'File {file} modified successfully.')
            with open(os.path.join(subdir, flagfile), 'w') as output_file:
                output_file.write('1')
        elif flagfile in files:
            print(f'Flag found, skipping file {file}')
            
