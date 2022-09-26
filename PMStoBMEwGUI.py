import tkinter as tk
import tkinter.font as TkFont
import PMStoBME
from tkinter import filedialog
from functools import partial
import logging

root = tk.Tk()
root.title('PMS to BME converter')
root.resizable(False, False)
root.config()

isKichiku = tk.IntVar(value=0)
log_var = tk.StringVar(value='\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n')

class WidgetLogger(logging.Handler):
    def __init__(self, widget):
        logging.Handler.__init__(self)
        self.setLevel(logging.INFO)
        self.widget = widget
        self.widget.config(state='disabled')

    def emit(self, record):
        self.widget.config(state='normal')
        # Append message (record) to the widget
        self.widget.insert(tk.END, self.format(record) + '\n')
        self.widget.see(tk.END)  # Scroll to the bottom
        self.widget.config(state='disabled')


#FONT DEFINITIONS
title_font = TkFont.Font(family='Ink Free', size=36, weight='bold')
text_font = TkFont.Font(family='Tahoma', size=12)
log_font = TkFont.Font(family='Arial', size=11)
TkFont.nametofont("TkDefaultFont").configure(family='Tahoma', size=12)

#TITLE
title_text = tk.Label(root, text='PMS to BME converter', font=title_font)
title_text.grid(column=0, row=0, sticky=tk.W, padx=12, pady=20, columnspan=2)

#FILE SELECT FRAME
file_select_frame = tk.Frame(root, borderwidth=4)
file_select_frame.config()
file_select_frame.grid(column=0, row=1, padx=12, sticky=tk.W, columnspan=2)
#FILE SELECT WIDGETS
file_select_label = tk.Label(file_select_frame, text='File: ')
selected_file_label = tk.Label(file_select_frame, text='No chart selected')
selected_file_var = tk.StringVar(value='No chart selected')

def select_file():
    try:
        chartfile = filedialog.askopenfilename(filetypes=[
            ('BME, PMS, BMS files', '*.bme;*.bms;*.pms'), ('All files', '*.*')
            ], title='Select chart file')
        selected_file_var.set(chartfile)
        selected_file_label.configure(text=selected_file_var.get().rsplit(sep='/', maxsplit=1)[1])  
    except:
        chartfile = 'No chart selected'
        selected_file_var.set(chartfile)
        selected_file_label.configure(text=selected_file_var.get())  

kichiku_box = tk.Checkbutton(file_select_frame, text='Kichiku', variable=isKichiku)
file_select_button = tk.Button(file_select_frame, text='Select chart', command=select_file)
#displays
file_select_label.grid(sticky=tk.W, column=0, row=0)
selected_file_label.grid(column=1, row=0, padx=(20,20))
kichiku_box.grid(column=2, row=0, padx=(10,10))
file_select_button.grid(sticky=tk.E, column=3, row=0)

#SONG INFO
song_info_frame = tk.LabelFrame(root, text='Song information')
song_info = tk.Text(song_info_frame, width=80, height=5, bg='#D3D3D3', font=text_font)
#displays
song_info_frame.grid(column=0, row=2, padx=12, pady=(10,10), sticky=tk.W, columnspan=2)
song_info.configure(state='disabled')
song_info.grid()

#CONFIGURATIONS
configuration_frame = tk.LabelFrame(root, text='Conversion configuration')
songname_frame = tk.Frame(configuration_frame)
songname_label = tk.Label(songname_frame, text='Song name: ', width=12)
songname_var = tk.StringVar()
songname_input = tk.Entry(songname_frame, width=25, font=text_font, textvariable=songname_var)
bpm_frame = tk.Frame(configuration_frame)
bpm_label = tk.Label(bpm_frame, text='Highest BPM: ', width=12)
bpm_var = tk.StringVar()
bpm_input = tk.Entry(bpm_frame, font=text_font, width=20, textvariable=bpm_var)
special_values_frame = tk.Frame(configuration_frame)
special_values_label = tk.Label(special_values_frame, text='Special values: ', width=12)
three_chord = tk.IntVar(value='100')
four_chord = tk.IntVar(value='100')
five_chord = tk.IntVar(value='100')
six_chord = tk.IntVar(value='100')
seven_chord = tk.IntVar(value='100')
chord_probs = [three_chord, four_chord, five_chord, six_chord, seven_chord]
#displays
configuration_frame.grid(column=0, row=3, padx=12, pady=(10,10), columnspan=2, sticky=tk.W)
songname_frame.grid(column=0, row=0, sticky=tk.W, pady=(6,6))
songname_label.grid(column=0,row=0)
songname_input.grid(column=1,row=0)
bpm_frame.grid(column=0, row=1, pady=(6,6), sticky=tk.W)
bpm_label.grid(column=0, row=0)
bpm_input.grid(column=1, row=0)
#bpm multipliers
selected_multiplier = tk.StringVar()
selected_multiplier.set(1.51)
multipliers = ('x1','1'),('x1.5','1.51'),('x2','2'),('x3','3.05'),('x4','4')
for ind, varbut in enumerate(multipliers):
    tk.Radiobutton(bpm_frame, 
                   text=varbut[0],
                   value=varbut[1],
                   variable=selected_multiplier).grid(row=0, column=2+ind)

#special values displays
special_values_frame.grid(column=0, row=2, pady=(6,6), sticky=tk.W)
special_values_label.grid(column=0,row=0, rowspan=2)
special_values_strings = ['3-chord', '4-chord', '5-chord', '6-chord', '7-chord']
for ind, var in enumerate(chord_probs):
    tk.Entry(special_values_frame, textvariable=var, width=5, font=text_font).grid(row=0, column=1+ind)
for ind, str in enumerate(special_values_strings):
    tk.Label(special_values_frame, text=str).grid(column=ind+1, row=1, padx=5)

#CONVERT! BUTTON
def convert():
    final_chartfile = selected_file_var.get()
    final_BPM = int(bpm_var.get()) * float(selected_multiplier.get())
    final_special_values = [three_chord.get(), four_chord.get(), five_chord.get(),
                            six_chord.get(), seven_chord.get(), ]
    final_iskichiku = isKichiku.get()
    final_songname = songname_var.get()
    convert_log = PMStoBME.convert(final_chartfile, final_iskichiku,
                           final_BPM, final_special_values, final_songname)
    log_var.set(convert_log)


convert_button = tk.Button(root, text='CONVERT!', width=15, height=6, 
                           command=convert, background='#00CC66')
convert_button.grid(column=1, row=3, sticky=tk.E, padx=(10,40))

#LOG
log = tk.Label(root, background='#A1A1A1', textvariable=log_var,
               width=80, justify=tk.LEFT, anchor=tk.W, font=log_font)
log.grid(column=0, row=4, padx=12, sticky=tk.W, columnspan=2)

#QUIT BUTTON
quitButton = tk.Button(root, text='Exit', command=root.quit)
quitButton.grid(column=0, row=5, sticky=tk.S, pady=(10,10), columnspan=2)

root.mainloop()

