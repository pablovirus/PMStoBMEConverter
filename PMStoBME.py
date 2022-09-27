import math
from functools import reduce
import re
import random
import os
import sys
import io

# os.system('color')
# GREEN = '\033[92m'
# RED = '\033[31m'
# YELLOW = '\033[33m'
# END = '\033[0m'

#  Function to calculate Least Common multiple
def lcm(denominators):
    return reduce(lambda a, b: a * b // math.gcd(a, b), denominators)

#  Function that determines if a string contains only zeroes
def is_only_zeroes(string):
    charRe = re.compile(r'[^0]')
    string = charRe.search(string)
    return not bool(string)

#  PMS CONVERSION FUNCTION
def convert(chartfile, isKichiku: bool=False, songBPM=150, special_values: list=[100,100,100,100,100],
            songname: str='default name'):
    
    old_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout
    
    try:
        chord_probs = [100,100] + special_values

        if isKichiku:
            print('This is a Kichiku conversion')
        else:
            print(f'This is NOT a Kichiku conversion')

        try:
            with open(chartfile,'rt', encoding='shift-jis') as file:
                entire_chart = file.readlines()
                directory = file.name.rsplit(sep='/', maxsplit=1)[0]
        except:
            with open(chartfile, 'rt', encoding='utf-8') as file:
                entire_chart = file.readlines()
                directory = file.name.rsplit(sep='/', maxsplit=1)[0]

        if isKichiku:
            # songname = chartfile.rsplit(sep='/', maxsplit=1)[1][1:-4].rsplit(sep=' ', maxsplit=1)[0]
            BG_track = 'ZY' # Default to Zy since ZZ sometimes isused  for long notes
            maxsize = 0
            for subdir, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith('.wav') and not file.startswith('preview'):
                        path = os.path.join(subdir, file)
                        size = os.stat(path).st_size # in bytes
                        if size > maxsize:
                            maxsize = size
                            BG_track = file.rsplit(sep='.wav')[0]
            print(f'Detected background track: {BG_track}')

        Tmin = 0.135 #in milisecconds

        # Remove newline characters from read chart.
        print('Removing trailing spaces and newline characters...')
        entire_chart_clean = []
        for element in entire_chart:
            entire_chart_clean.append(element.strip())

        # Search for position of start of data
        chart_start = 0
        for line in entire_chart_clean:
            matched = re.search(r'#00\d\d\d:', line)
            if matched:
                break
            else:
                chart_start+= 1
        print(f'Main data starts at line {chart_start} in the input file')
        
        #Split list into header and chart
        print('Splitting data from file header...')
        header_info = entire_chart_clean[:chart_start]
        chart_with_whitespace = entire_chart_clean[chart_start:]

        # Set PLAYER variable to 1 (IIDX SP) and delete GENRE, COMMENT, ARTIST, and TITLE
        # This is done to prevent problems with character encoding
        print('Removing unwanted tags...')
        comment = '#COMMENT.*'
        genre = '#GENRE.*'
        title = '#TITLE.*'
        artist = '#ARTIST.*'
        strings = [comment, genre, title, artist]
        if (chartfile[len(chartfile)-3:] == 'pms') or (chartfile[len(chartfile)-3:] == 'PMS'):
            try:
                index_player_var = header_info.index('#PLAYER 3')
                header_info[index_player_var] = ('#PLAYER 1')
            except:
                print(f'#PLAYER tag not found in header, skipping')
            
            for element in strings:
                index = [i for i in range(len(header_info)) if re.match(element, 
                        header_info[i], flags=re.IGNORECASE)]
                if index:
                    header_info[index[0]] = ''

        # Remove empty strings from chart using list comprehension
        print('Removing empty strings from chart...')
        chart = [i for i in chart_with_whitespace if i]

        # Determine total number of measures by jumping to last element in chart and slicing
        # e.g. go from #06525:0000B200 to only '065' to then the integer 65
        total_measures = int(chart[len(chart)-1][1:4]) 
        print('Number of Total Measures:', total_measures)

        # Determine LCM and Sfree
        # LCM is the number of divisions per measure we will use, i.e. number of pairs of characteres, 
        # like 'AE' and '00', and Sfree is the number of divisions that should be '00' before and
        # after a given position to avoid creating obnoxious jacks when adding samples to 
        # columns 1-7, shorthand for 'Sample-free zone'
        # Some songs give LCMs that are way too large to handle. These are capped at up to 2000.
        # Small LCMs are increased to 48 to give Sfree better temporal resolution.
        divisions = []
        for line in chart:
            multiple = int(len(line[7:])/2)
            if not(multiple in divisions):
                divisions.append(multiple)
        try:
            divisions.remove(0) # remove 0 to avoid errors
        except:
            pass
        LCM = lcm(divisions)
        if LCM > 2000:
            while (LCM > 2000):
                LCM //= 2
            print(f'WARNING: LCM had to be capped at {LCM}')    
        elif LCM < 48:
            LCM = LCM * 4
            print(f'WARNING: LCM was increased to {LCM}')
        else: print('The LCM is:', LCM)
        Tlcm = (60/songBPM)*4/LCM
        Sfree = math.ceil(Tmin/Tlcm)
        print(f'Sfree is {Sfree} samples, and the BPM is {songBPM}')

        # Pad each line of the chart with zeroes depending on LCM. 
        # Extract lines that are BPM changes, and delete hidden samples
        MCBPM = [] #Master Channel for BPM changes and measure size changes
        hidden_channels = ['31','32','33','34','35','36','37','38','39',
                        '41','42','43','44','45','46','47','48','49','04']
        print('Padding entire chart with zeroes...')
        padded_chart = [] 
        for ind, line in enumerate(chart):
            if (line[4:6] == '03') or (line[4:6] == '08') or (line[4:6] == '02'):
                MCBPM.append(line + '\n') # store lines indicating BPM/measure changes separately
                continue
            if hidden_channels.count(line[4:6]): 
                continue # remove lines that contain hidden samples (only useful for easter eggs)
            linelist = re.findall('..?', line[7:]) # parses string into list of 2-char strings
            paddedline = ''.zfill(LCM * 2)
            paddedlinelist = re.findall('..?', paddedline)
            for samplepos, sample in enumerate(linelist):
                paddedlinelist[samplepos * LCM // len(linelist)] = sample
            line = line[:7] + ''.join(paddedlinelist)
            padded_chart.append(line)
        # newline_char = '\n\n'
        # print(f'This is the padded chart: {newline_char.join(padded_chart)}')
        # Create Master Channels (MCs)
        # The Master Channels will be a continuous list of ALL samples (and '00's) in each channel
        # throughout the entire song, where 'channel' in BMS terms is a column or button in a game
        # such as Buttons 1-7 in IIDX and 1-9 in PopN.
        MClen = LCM*(total_measures+1)

        #Define MC background channels:
        (MCBG1, MCBG2, MCBG3, MCBG4, MCBG5, MCBG6, MCBG7, MCBG8, MCBG9, MCBG10, MCBG11, MCBG12, 
            MCBG13, MCBG14, MCBG15) = (re.findall('..?',''.zfill(MClen*2)) for i in range(15))

        #Define channels for buttons:
        MC1, MC2, MC3, MC4, MC5, MC6, MC7, MC8, MC9, MCTT = \
            (re.findall('..?',''.zfill(MClen*2)) for i in range(10))

        #Define final channels for IIDX
        MC1f, MC2f, MC3f, MC4f, MC5f, MC6f, MC7f, MCTTf = \
            (re.findall('..?',''.zfill(MClen*2)) for i in range(8))

        #Define dictionaries to simplify sample assignment
        MC = {'11': MC1, '12': MC2, '13': MC3, '14': MC4, '15': MC5, '22': MC6, '23': MC7, 
            '24': MC8, '25': MC9, '01': MCBG1, '16': MCTT, '19':MC7, '18':MC6}
        MCf = {'11': MC1f, '12': MC2f, '13': MC3f, '14': MC4f, '15': MC5f, '22': MC6f, '23': MC7f, 
            '01': MCBG1, '16': MCTTf, '19': MC7f, '18': MC6f}
        # MC7 and MC6 are accessable with two different keys in this dict because this 
        # allows the algorithm to either take a PMS file or a BME file as input.

        print('Filling Master Channels...')
        for ind, line in enumerate(padded_chart):
            linelist = re.findall('..?', line[7:])
            if line[4:6] != '01': # '01' corresponds to background samples
                #Fill MCs 1 to 9 with existing samples in the original PopN chart. 
                measure = int(line[1:4])
                # print(f'Assigning samples from {measure} to Master Channel {line[4:6]}')
                for samplepos, sample in enumerate(linelist):
                    MC[line[4:6]][(measure * LCM + samplepos)] = sample
                    # if sample != '00':
                    #     print(f'Sample {sample} goes into {measure * LCM + samplepos}')
                # print(MC[line[4:6]])
            else:
                measure = int(line[1:4]) #Fill MCBGs with background samples of PopN chart
                for samplepos, sample in enumerate(linelist):
                    if sample != 0:
                        if MCBG1[(measure * LCM + samplepos)] == '00':
                            MCBG1[(measure * LCM + samplepos)] = sample
                        elif MCBG2[(measure * LCM + samplepos)] == '00':
                            MCBG2[(measure * LCM + samplepos)] = sample
                        elif MCBG3[(measure * LCM + samplepos)] == '00':
                            MCBG3[(measure * LCM + samplepos)] = sample
                        elif MCBG4[(measure * LCM + samplepos)] == '00':
                            MCBG4[(measure * LCM + samplepos)] = sample
                        elif MCBG5[(measure * LCM + samplepos)] == '00':
                            MCBG5[(measure * LCM + samplepos)] = sample
                        elif MCBG6[(measure * LCM + samplepos)] == '00':
                            MCBG6[(measure * LCM + samplepos)] = sample
                        elif MCBG7[(measure * LCM + samplepos)] == '00':
                            MCBG7[(measure * LCM + samplepos)] = sample
                        elif MCBG8[(measure * LCM + samplepos)] == '00':
                            MCBG8[(measure * LCM + samplepos)] = sample
                        elif MCBG9[(measure * LCM + samplepos)] == '00':
                            MCBG9[(measure * LCM + samplepos)] = sample
                        elif MCBG10[(measure * LCM + samplepos)] == '00':
                            MCBG10[(measure * LCM + samplepos)] = sample
                        elif MCBG11[(measure * LCM + samplepos)] == '00':
                            MCBG11[(measure * LCM + samplepos)] = sample
                        elif MCBG12[(measure * LCM + samplepos)] == '00':
                            MCBG12[(measure * LCM + samplepos)] = sample
                        elif MCBG13[(measure * LCM + samplepos)] == '00':
                            MCBG13[(measure * LCM + samplepos)] = sample
                        elif MCBG14[(measure * LCM + samplepos)] == '00':
                            MCBG14[(measure * LCM + samplepos)] = sample
                        elif MCBG15[(measure * LCM + samplepos)] == '00':
                            MCBG15[(measure * LCM + samplepos)] = sample


        ForbiddenPos = [] # Used for Kichiku conversions with special values, see moveSampleBG

        # divide chart in 'chunks' according to measures
        # count number of samples in columns 1+2, 2+8, 8+9 for each measure
        # decide which of three 'configurations' to be used for that measure
        # adjust sample positions in this measure according to this configuration
        # move samples in the columns that were left out in this measure
        def count_samples(input_list):
            result = 0
            for sample in input_list:
                if sample != '00':
                    result+= 1
            return result
        def winning_config(measure):
            (col_1, col_2, col_3, col_4, col_6, col_7, col_8, col_9) = (
                count_samples(MC1[measure*LCM : (measure + 1) * LCM]),
                count_samples(MC2[measure*LCM : (measure + 1) * LCM]),
                count_samples(MC3[measure*LCM : (measure + 1) * LCM]),
                count_samples(MC4[measure*LCM : (measure + 1) * LCM]),
                count_samples(MC6[measure*LCM : (measure + 1) * LCM]),
                count_samples(MC7[measure*LCM : (measure + 1) * LCM]),
                count_samples(MC8[measure*LCM : (measure + 1) * LCM]),
                count_samples(MC9[measure*LCM : (measure + 1) * LCM]),
            )
            config_1 = col_1 + col_2
            config_2 = col_2 + col_8 # unused for now
            config_3 = col_8 + col_9
            config_1_tie = col_1 + col_2 + col_3 + col_4
            config_3_tie = col_6 + col_7 + col_8 + col_9
            if config_1 > config_3: return 'config_1'
            if config_3 > config_1: return 'config_3'
            if config_1_tie >= config_3_tie: return 'config_1'
            return 'config_3'

        if not isKichiku:
            for measure in range(total_measures+1):
                if winning_config(measure) == 'config_1':     
                    #config 1 wins, assign samples from MC1-7 to final columns 1-7
                    MC1f[measure*LCM : (measure + 1) * LCM] = MC1[measure*LCM : (measure + 1) * LCM]
                    MC2f[measure*LCM : (measure + 1) * LCM] = MC2[measure*LCM : (measure + 1) * LCM]
                    MC3f[measure*LCM : (measure + 1) * LCM] = MC3[measure*LCM : (measure + 1) * LCM]
                    MC4f[measure*LCM : (measure + 1) * LCM] = MC4[measure*LCM : (measure + 1) * LCM]
                    MC5f[measure*LCM : (measure + 1) * LCM] = MC5[measure*LCM : (measure + 1) * LCM]
                    MC6f[measure*LCM : (measure + 1) * LCM] = MC6[measure*LCM : (measure + 1) * LCM]
                    MC7f[measure*LCM : (measure + 1) * LCM] = MC7[measure*LCM : (measure + 1) * LCM]
                    # delete samples from these MCs
                    for channel in (MC1, MC2, MC3, MC4, MC5, MC6, MC7):
                        channel[measure*LCM : (measure + 1) * LCM] = ['00' for i in range(LCM)]
                elif winning_config(measure) == 'config_3':
                    #config 3 wins, assign samples from MC3-9 to final columns 1-7
                    MC1f[measure*LCM : (measure + 1) * LCM] = MC3[measure*LCM : (measure + 1) * LCM]
                    MC2f[measure*LCM : (measure + 1) * LCM] = MC4[measure*LCM : (measure + 1) * LCM]
                    MC3f[measure*LCM : (measure + 1) * LCM] = MC5[measure*LCM : (measure + 1) * LCM]
                    MC4f[measure*LCM : (measure + 1) * LCM] = MC6[measure*LCM : (measure + 1) * LCM]
                    MC5f[measure*LCM : (measure + 1) * LCM] = MC7[measure*LCM : (measure + 1) * LCM]
                    MC6f[measure*LCM : (measure + 1) * LCM] = MC8[measure*LCM : (measure + 1) * LCM]
                    MC7f[measure*LCM : (measure + 1) * LCM] = MC9[measure*LCM : (measure + 1) * LCM]
                    # delete samples from these MCs
                    for channel in (MC3, MC4, MC5, MC6, MC7, MC8, MC9):
                        channel[measure*LCM : (measure + 1) * LCM] = ['00' for i in range(LCM)]
            print('Measures adjusted and samples deleted from original MCs')

        if isKichiku:
            for measure in range(total_measures+1):   
                MC1f[measure*LCM : (measure + 1) * LCM] = MC1[measure*LCM : (measure + 1) * LCM]
                MC2f[measure*LCM : (measure + 1) * LCM] = MC2[measure*LCM : (measure + 1) * LCM]
                MC3f[measure*LCM : (measure + 1) * LCM] = MC3[measure*LCM : (measure + 1) * LCM]
                MC4f[measure*LCM : (measure + 1) * LCM] = MC4[measure*LCM : (measure + 1) * LCM]
                MC5f[measure*LCM : (measure + 1) * LCM] = MC5[measure*LCM : (measure + 1) * LCM]
                MC6f[measure*LCM : (measure + 1) * LCM] = MC6[measure*LCM : (measure + 1) * LCM]
                MC7f[measure*LCM : (measure + 1) * LCM] = MC7[measure*LCM : (measure + 1) * LCM]

        print('Moving remaining samples in MC1, MC2, MC8, and MC9...')

        def moveSample(inputMC, MC, Sfree, button):
            # Defines a function that moves samples from inputMC to the IIDX chart.
            # This function will be used for samples on columns 8 and 9
            # The function performs the necessary checks to see if a sample can be placed on a given channel without causing
            # unfair jacks (this depends on the calculated Sfree).
            # Remember to manually correct for the main long 'background' sample in the song after Kichiku conversions!!
            lastsample = '00'
            lastsampleMC = '11'
            for samplepos, sample in enumerate(inputMC):
                if (sample != '00'):
                    PotentialMCs = ['11', '12', '13', '14', '15', '22', '23']
                    random.shuffle(PotentialMCs) #Shuffle the previous list so that samples are added at random columns
                    #The following checks try to preserve notes from lanes 8 and 9 in the popn chart on the rightmost-hand
                    #side of the IIDX chart and vice-versa for buttons from lanes 1 and 2.
                    if button == 1:
                        auxstr = ''.join(MCf['11'][samplepos-Sfree:samplepos])+\
                                ''.join(MCf['11'][samplepos:samplepos+1+Sfree])
                        if is_only_zeroes(auxstr):
                            PotentialMCs.insert(0, PotentialMCs.pop(PotentialMCs.index('11')))
                        else:
                            auxstr = ''.join(MCf['12'][samplepos - Sfree:samplepos]) + \
                                    ''.join(MCf['12'][samplepos:samplepos + 1 + Sfree])
                            if is_only_zeroes(auxstr):
                                PotentialMCs.insert(0, PotentialMCs.pop(PotentialMCs.index('12'))) 
                    elif button == 2:
                        auxstr = ''.join(MCf['12'][samplepos-Sfree:samplepos])+\
                                ''.join(MCf['12'][samplepos:samplepos+1+Sfree])
                        if is_only_zeroes(auxstr):
                            PotentialMCs.insert(0, PotentialMCs.pop(PotentialMCs.index('12')))
                        else:
                            auxstr = ''.join(MCf['11'][samplepos - Sfree:samplepos]) + \
                                    ''.join(MCf['11'][samplepos:samplepos + 1 + Sfree])
                            if is_only_zeroes(auxstr):
                                PotentialMCs.insert(0, PotentialMCs.pop(PotentialMCs.index('11'))) 
                    elif button == 8:
                        auxstr = ''.join(MCf['22'][samplepos-Sfree:samplepos])+\
                                ''.join(MCf['22'][samplepos:samplepos+1+Sfree])
                        if is_only_zeroes(auxstr):
                            PotentialMCs.insert(0, PotentialMCs.pop(PotentialMCs.index('22')))
                        else:
                            auxstr = ''.join(MCf['23'][samplepos - Sfree:samplepos]) + \
                                    ''.join(MCf['23'][samplepos:samplepos + 1 + Sfree])
                            if is_only_zeroes(auxstr):
                                PotentialMCs.insert(0, PotentialMCs.pop(PotentialMCs.index('23')))
                    elif button == 9:
                        auxstr = ''.join(MCf['23'][samplepos - Sfree:samplepos]) + \
                                ''.join(MCf['23'][samplepos:samplepos + 1 + Sfree])
                        if is_only_zeroes(auxstr):
                            PotentialMCs.insert(0, PotentialMCs.pop(PotentialMCs.index('23')))
                        else:
                            auxstr = ''.join(MCf['22'][samplepos - Sfree:samplepos]) + \
                                    ''.join(MCf['22'][samplepos:samplepos + 1 + Sfree])
                            if is_only_zeroes(auxstr):
                                PotentialMCs.insert(0, PotentialMCs.pop(PotentialMCs.index('22')))
                    #  The two following checks are to avoid an uncommon chord combination
                    #  in IIDX (5+6) as much as possible
                    if MCf['22'][samplepos] != '00':
                        PotentialMCs.append(PotentialMCs.pop(PotentialMCs.index('23')))
                        PotentialMCs.append(PotentialMCs.pop(PotentialMCs.index('15')))
                    if MCf['15'][samplepos] != '00':
                        PotentialMCs.append(PotentialMCs.pop(PotentialMCs.index('14')))
                        PotentialMCs.append(PotentialMCs.pop(PotentialMCs.index('22')))
                    # if lastsample == sample:
                    #     auxstr = ''.join(MCf[lastsampleMC][samplepos - Sfree:samplepos]) + \
                    #              ''.join(MCf[lastsampleMC][samplepos:samplepos + 1 + Sfree])
                    #     if is_only_zeroes(auxstr):
                    #         MCf[lastsampleMC][samplepos] = sample
                    #         inputMC[samplepos] = '00'
                    #         continue
                    for possiblepos in PotentialMCs:
                        # print('Checking for possible allocation of sample',sample,'in position',samplepos, 'in channel:',possiblepos)
                        auxstr = ''.join(MCf[possiblepos][samplepos-Sfree:samplepos])+\
                                ''.join(MCf[possiblepos][samplepos:samplepos+1+Sfree])
                        if is_only_zeroes(auxstr):
                            MCf[possiblepos][samplepos] = sample
                            inputMC[samplepos] = '00'
                            lastsample = sample
                            lastsampleMC = possiblepos
                            break
            return
            
        def moveSampleBG(inputMC,MC,Sfree):
            ''' Defines a function that moves samples from inputMC to the IIDX chart.
            This function will be used for samples on on all BG channels
            The function performs the necessary checks to see if a sample can be 
            placed on a given channel without causing
            unfair jacks (this depends on the calculated Sfree).
            Remember to manually correct for the main long 'background' sample 
            in the song after Kichiku conversions!! '''

            for samplepos, sample in enumerate(inputMC):
                if (sample != '00') and ForbiddenPos.count(samplepos):
                    continue # skip this sample if position is forbidden
                if (sample != '00' and sample != 'ZZ' and sample != BG_track):
                    ChordCount = 0
                    PotentialMCs = ['11','12','13','14','15','22','23']
                    for possiblepos in PotentialMCs:
                        auxstr = MCf[possiblepos][samplepos]
                        if not is_only_zeroes(auxstr):
                            ChordCount = ChordCount + 1
                    # Check if samplepos should be added to forbidden list
                    if ChordCount == 0: ChordCount = ChordCount + 1
                    if ChordCount == 7: ChordCount = 6
                    if random.randint(0,100) > chord_probs[ChordCount]:
                        ForbiddenPos.append(samplepos)
                        continue # skip this sample after rolling random number
                    random.shuffle(PotentialMCs) 
                    for possiblepos in PotentialMCs:
                        auxstr = ''.join(MCf[possiblepos][samplepos-Sfree:samplepos])+\
                                ''.join(MCf[possiblepos][samplepos:samplepos+1+Sfree])
                        if is_only_zeroes(auxstr):
                            MCf[possiblepos][samplepos] = sample
                            inputMC[samplepos] = '00'
                            break
            return

        if not isKichiku:
            print('Moving samples from MCs 1, 2, 8, and 9...')
            moveSample(MC1,MC,Sfree,1)
            moveSample(MC2,MC,Sfree,2)
            moveSample(MC8,MC,Sfree,8)
            moveSample(MC9,MC,Sfree,9)
        if isKichiku:
            print('Moving samples from background channels...')
            print(f'REMEMBER TO CHECK AND MANUALLY ADJUST LONG BACKGROUND SAMPLES LATER')
            moveSampleBG(MCBG1, MC, Sfree)
            moveSampleBG(MCBG2, MC, Sfree)
            moveSampleBG(MCBG3, MC, Sfree)
            moveSampleBG(MCBG4, MC, Sfree)
            moveSampleBG(MCBG5, MC, Sfree)
            moveSampleBG(MCBG6, MC, Sfree)
            moveSampleBG(MCBG7, MC, Sfree)
            moveSampleBG(MCBG8, MC, Sfree)
            moveSampleBG(MCBG9, MC, Sfree)
            moveSampleBG(MCBG10, MC, Sfree)
            moveSampleBG(MCBG11, MC, Sfree)
            moveSampleBG(MCBG12, MC, Sfree)
            moveSampleBG(MCBG13, MC, Sfree)
            moveSampleBG(MCBG14, MC, Sfree)
            moveSampleBG(MCBG15, MC, Sfree)

        # Recreate the modified chart with format #XXXYY:ZZZZZZZZZZ using all MCfs

        #MCf1
        MC1str = ''.join(MC1f)
        MC1divided = [(MC1str[i:i+LCM*2]) for i in range(0, len(MC1str), LCM*2)]
        MC1final = ''
        for ind, measure in enumerate(MC1divided):
            MC1final = MC1final + '#' + str(ind).zfill(3) + '11' + ':' + measure + '\n'

        #MCf2
        MC2str = ''.join(MC2f)
        MC2divided = [(MC2str[i:i+LCM*2]) for i in range(0, len(MC2str), LCM*2)]
        MC2final = ''
        for ind, measure in enumerate(MC2divided):
            MC2final = MC2final + '#' + str(ind).zfill(3) + '12' + ':' + measure + '\n'

        #MCf3
        MC3str = ''.join(MC3f)
        MC3divided = [(MC3str[i:i+LCM*2]) for i in range(0, len(MC3str), LCM*2)]
        MC3final = ''
        for ind, measure in enumerate(MC3divided):
            MC3final = MC3final + '#' + str(ind).zfill(3) + '13' + ':' + measure + '\n'

        #MCf4
        MC4str = ''.join(MC4f)
        MC4divided = [(MC4str[i:i+LCM*2]) for i in range(0, len(MC4str), LCM*2)]
        MC4final = ''
        for ind, measure in enumerate(MC4divided):
            MC4final = MC4final + '#' + str(ind).zfill(3) + '14' + ':' + measure + '\n'

        #MCf5
        MC5str = ''.join(MC5f)
        MC5divided = [(MC5str[i:i+LCM*2]) for i in range(0, len(MC5str), LCM*2)]
        MC5final = ''
        for ind, measure in enumerate(MC5divided):
            MC5final = MC5final + '#' + str(ind).zfill(3) + '15' + ':' + measure + '\n'

        #MCf6
        MC6str = ''.join(MC6f)
        MC6divided = [(MC6str[i:i+LCM*2]) for i in range(0, len(MC6str), LCM*2)]
        MC6final = ''
        for ind, measure in enumerate(MC6divided):
            MC6final = MC6final + '#' + str(ind).zfill(3) + '18' + ':' + measure + '\n'

        #MCf7
        MC7str = ''.join(MC7f)
        MC7divided = [(MC7str[i:i+LCM*2]) for i in range(0, len(MC7str), LCM*2)]
        MC7final = ''
        for ind, measure in enumerate(MC7divided):
            MC7final = MC7final + '#' + str(ind).zfill(3) + '19' + ':' + measure + '\n'

        #Note: Remaining samples in these Master Channels are sent to channel '01' (background)
        MC1surplus = MC2surplus = MC8surplus = MC9surplus = ''

        if not isKichiku:
            #MC1
            MC1str = ''.join(MC1)
            MC1divided = [(MC1str[i:i+LCM*2]) for i in range(0, len(MC1str), LCM*2)]
            for ind, measure in enumerate(MC1divided):
                MC1surplus = MC1surplus + '#' + str(ind).zfill(3) + '01' + ':' + measure + '\n'

            #MC2
            MC2str = ''.join(MC2)
            MC2divided = [(MC2str[i:i+LCM*2]) for i in range(0, len(MC2str), LCM*2)]
            for ind, measure in enumerate(MC2divided):
                MC2surplus = MC2surplus + '#' + str(ind).zfill(3) + '01' + ':' + measure + '\n'

            #MC8
            MC8str = ''.join(MC8)
            MC8divided = [(MC8str[i:i+LCM*2]) for i in range(0, len(MC8str), LCM*2)]
            for ind, measure in enumerate(MC8divided):
                MC8surplus = MC8surplus + '#' + str(ind).zfill(3) + '01' + ':' + measure + '\n'

            #MC9 
            MC9str = ''.join(MC9)
            MC9divided = [(MC9str[i:i+LCM*2]) for i in range(0, len(MC9str), LCM*2)]
            for ind, measure in enumerate(MC9divided):
                MC9surplus = MC9surplus + '#' + str(ind).zfill(3) + '01' + ':' + measure + '\n'

        #MCTT
        MCTTstr = ''.join(MCTT)
        MCTTdivided = [(MCTTstr[i:i+LCM*2]) for i in range(0, len(MCTTstr), LCM*2)]
        MCTTfinal = ''
        for ind, measure in enumerate(MCTTdivided):
            MCTTfinal = MCTTfinal + '#' + str(ind).zfill(3) + '16' + ':' + measure + '\n'
            
        #MCBGs
        MCBGs = [MCBG1,MCBG2,MCBG3,MCBG4,MCBG5,MCBG6,MCBG7,MCBG8,MCBG9,
                MCBG10,MCBG11,MCBG12,MCBG13,MCBG14,MCBG15]
        MCBGconcat = ''
        for MCBG in MCBGs:
            MCBGstr = ''.join(MCBG)
            MCBGdivided = [(MCBGstr[i:i + LCM*2]) for i in range(0, len(MCBGstr), LCM*2)]
            MCBGfinal = ''
            for ind, measure in enumerate(MCBGdivided):
                MCBGfinal = MCBGfinal + '#' + str(ind).zfill(3) + '01' + ':' + measure + '\n'
            MCBGconcat = MCBGconcat + MCBGfinal
            
        #Create Chart
        #After the chart is created, open it in iBMSC and save it immediately. This will correct 
        # the ordering and simplify the formatting of the .bme file.
        ConvertedChart = '\n'.join(header_info) + '\n' + MC1final + MC2final + MC3final + \
            MC4final + MC5final + MC6final + MC7final + \
            MC1surplus + MC2surplus + MC8surplus + MC9surplus + MCTTfinal + MCBGconcat + '\n'.join(MCBPM)
        print('Chart created successfully. Writing to file...')
        outfolder = chartfile.rsplit('/',maxsplit=1) 
        outfolder[0] = outfolder[0]+'/'
        if isKichiku:
            difficulty = 'leggendaria'
        else:
            difficulty = 'another'

        output_file_name = outfolder[0]+ f'[{songname} {difficulty}.bme'

        try: 
            os.remove(output_file_name)
            print(f'WARNING: Previously existing Output Chart file deleted')
        except: 
            pass

        with open(output_file_name,'w', encoding='utf-8') as outputfile:
            outputfile.write(ConvertedChart)
        print('File written to:')
        print(outfolder[0])
        print(f'[{songname} {difficulty}.bme')
        print('Job complete!')

        log = new_stdout.getvalue()
        sys.stdout = old_stdout
        return log
    except:
        print('ERROR!!')
        log = new_stdout.getvalue()
        sys.stdout = old_stdout
        return log
    