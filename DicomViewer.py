import tkinter as tk
from scipy.interpolate import make_interp_spline
import numpy as np
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 16 13:40:16 2022

@author: ASUS ZenBook
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 14 17:47:49 2022
Varinata Mergeuita a aplicatiei 
@author: mariasavu
"""

#%%
import sys
from tkinter import * 
import tkinter as tk
from tkinter import messagebox
from PIL import ImageTk,Image
import pydicom as py
from tkinter import filedialog as fd
import tkinter.ttk as ttk
from tkinter.messagebox import showinfo
import numpy as np
from PIL import ImageGrab   
import random
from PIL import ImageEnhance, ImageFile
import os.path 
from matplotlib.pyplot import figure
global filepath_imag
import matplotlib.pyplot as plt 
from scipy.spatial import ConvexHull
from skimage import measure
from PIL import Image, ImageDraw
import cv2

filepath_imag = "./image.png"
global original 
global copie 




ImageFile.LOAD_TRUNCATED_IMAGES = True
original = Image.open(filepath_imag)
copie = original 

#%%  spline line 
def on_canvas_click(event):
    global line, is_adjusting
    if not line:
        add_point(event)
    elif line and not is_adjusting:
        select_point(event)

def add_point(event):
    global points
    x, y = event.x, event.y
    points.append((x, y))
    canvas.create_oval(x - 2, y - 2, x + 2, y + 2, fill="red",tags= "points")

def draw_spline():
    global points, line, is_adjusting
    if len(points) < 2:
        tk.messagebox.showinfo("Error", "Please add at least 2 points to draw the line.")
        return

    x_coords, y_coords = zip(*points)
    t = range(len(points))

    interp_func = make_interp_spline(t, list(x_coords), k=3)
    x_smooth = interp_func(np.linspace(0, len(points) - 1, 100))
    interp_func = make_interp_spline(t, list(y_coords), k=3)
    y_smooth = interp_func(np.linspace(0, len(points) - 1, 100))

    if line:
        canvas.delete(line)

    points_smooth = [(int(x), int(y)) for x, y in zip(x_smooth, y_smooth)]
    line = canvas.create_line(points_smooth, fill="blue", width=2)
    button_adjust.config(state="normal")
    button_delete.config(state="normal")
    button_save_mask.config(state="normal")

    
    
    

def enable_adjustment():
    global line, is_adjusting
    if not line:
        tk.messagebox.showinfo("Error", "Please draw a line first.")
    else:
        is_adjusting = True

def select_point(event):
    global selected_point
    items = canvas.find_closest(event.x, event.y)
    if items:
        selected_point = items[0]
def adjust_point(event):
    global selected_point, points
    if selected_point:
        index = selected_point - 1
        if 0 <= index < len(points):
            coords = canvas.coords(selected_point)
            if len(coords) == 4:  # Check if the coordinates contain four values
                x1, y1, _, _ = coords
                x2, y2 = event.x - 2, event.y - 2
                canvas.move(selected_point, x2 - x1, y2 - y1)
                points[index] = (event.x, event.y)
                redraw_spline()

def redraw_spline():
    global line
    if line:
        canvas.delete(line)
    draw_spline()

def on_canvas_drag(event):
    global is_adjusting, selected_point
    if is_adjusting and selected_point:
        adjust_point(event)

def on_canvas_release(event):
    
    global is_adjusting
    if is_adjusting:
        is_adjusting = False
def delete_line():
    global line, points, is_adjusting, selected_point
    canvas.delete(line)
    line = None
    points = []
    is_adjusting = False
    selected_point = None
    canvas.delete("points") 
    button_adjust.config(state="disabled")
    button_delete.config(state="disabled")
def save_contour():
    global points
    if len(points) < 2:
        tk.messagebox.showinfo("Error", "Please add at least 2 points to draw the line.")
        return

    file_name = entry_file_name.get()  # Get the file name from a text box

    if not file_name:
        tk.messagebox.showinfo("Error", "Please enter a file name.")
        return

    x_coords, y_coords = zip(*points)
    t = range(len(points))

    interp_func = make_interp_spline(t, list(x_coords), k=3)
    x_smooth = interp_func(np.linspace(0, len(points) - 1, 100))
    interp_func = make_interp_spline(t, list(y_coords), k=3)
    y_smooth = interp_func(np.linspace(0, len(points) - 1, 100))

    points_smooth = [(int(x), int(y)) for x, y in zip(x_smooth, y_smooth)]
    contour_points = np.array(points_smooth, dtype=np.int32)
    contour = np.zeros((canvas.winfo_height(), canvas.winfo_width()), dtype=np.uint8)
    cv2.drawContours(contour, [contour_points], 0, 255, thickness=cv2.FILLED)
    cv2.imwrite(file_name + ".png", contour)



#%% Functia de segemnatre si tot ce ii mai trebuie ei 
"""""
def overlay_plot(im, mask):
    plt.figure()
    plt.imshow(im.T, 'gray', interpolation='none')
    plt.imshow(mask.T, 'jet', interpolation='none', alpha=0.5)
"""
 
#%%


def intensity_seg(ct_numpy, min, max):
    clipped = ct_numpy.clip(min, max)
    clipped[clipped != max] = 1
    clipped[clipped == max] = 0
    return measure.find_contours(clipped, 0.8)

def set_is_closed(contour):
    if contour_distance(contour) < 1:
        return True
    else:
        return False

def find_lungs(contours):
   
    body_and_lung_contours = []
    vol_contours = []
   
    for contour in contours:
        hull = ConvexHull(contour)
       
      
        if hull.volume > 2000 and set_is_closed(contour):
          
            body_and_lung_contours.append(contour)
            vol_contours.append(hull.volume)

    if len(body_and_lung_contours) == 2:
        return body_and_lung_contours
    elif len(body_and_lung_contours) > 2:
        vol_contours, body_and_lung_contours = (list(t) for t in
                                                zip(*sorted(zip(vol_contours, body_and_lung_contours))))
        body_and_lung_contours.pop(-1)
        return body_and_lung_contours


def show_contour(image, contours, name=None, save=False):
    
    fig, ax = plt.subplots()
    ax.imshow(image.T, cmap=plt.cm.gray)
    for contour in contours:
        ax.plot(contour[:, 0], contour[:, 1], linewidth=1)

    ax.set_xticks([])
    ax.set_yticks([])

    if save:
        plt.savefig(name, bbox_inches='tight')
        plt.close(fig)
    else:
        plt.show()



def create_mask_from_polygon(image, contours):
    
    lung_mask = np.array(Image.new('L', image.shape, 0))
    for contour in contours:
        x = contour[:, 0]
        y = contour[:, 1]
        polygon_tuple = list(zip(x, y))
        img = Image.new('L', image.shape, 0)
        ImageDraw.Draw(img).polygon(polygon_tuple, outline=0, fill=0)
        mask = np.array(img)
        lung_mask += mask

    lung_mask[lung_mask > 1] = 1  # sanity check to make 100% sure that the mask is binary

    return lung_mask.T  # transpose it to be aligned with the image dims



def find_pix_dim(path):
  
    dicom_header = py.read_file(path)
    pixdim_1 = dicom_header.PixelSpacing[1]
    pixdim_2 = dicom_header.PixelSpacing[0]
    
    return [pixdim_1, pixdim_2]
   
  
   
   

def contour_distance(contour):
  
    dx = contour[0, 1] - contour[-1, 1]
    dy = contour[0, 0] - contour[-1, 0]
    return np.sqrt(np.power(dx, 2) + np.power(dy, 2))

def compute_area(mask, pixdim):
  
    mask[mask >= 1] = 1
    lung_pixels = np.sum(mask)
    return lung_pixels * pixdim[0] * pixdim[1]


def image_seg(path):  
   
    lung_areas = []

    exam_path = path
    try:
        img_name = exam_path.split("/")[-1].split('.dcm')[0]
    
        
        ct_img = py.dcmread(exam_path)
        pixdim = find_pix_dim(exam_path)

    
        ct_numpy = ct_img.pixel_array.astype(float)

        contours = intensity_seg(ct_numpy, min=-1200, max=800)

        # Check if contours is empty
        if not contours:
            print("No contours found for:", img_name)
        
        lungs = find_lungs(contours)
        show_contour(ct_numpy, lungs, name= 'imagine_segmentata.png',save = True)
        image = Image.open('imagine_segmentata.png')

# Rotate the image by 90 degrees clockwise
        
       

        resized_image = image.resize((500, 500))
        rotated_image = resized_image.rotate(-90)
       
        rotated_image.save('imagine_segmentata.png')
        lung_mask = create_mask_from_polygon(ct_numpy, lungs)
        
        # show_slice(lung_mask)

        lung_area = compute_area(lung_mask, find_pix_dim(exam_path))
        lung_areas.append([img_name, lung_area])  # int is ok since the units are already mm^2
        print(img_name, 'lung area:', lung_area)
    except Exception as e:
        print("Error processing:", img_name)
        print("Error message:", str(e))



#%% Functia de conversie a imaginii 

def convert(path):

    ds = py.dcmread(path) # Put the right path of the image that you want to convert
    new_image = ds.pixel_array.astype(float) # Convert the values into float
    scaled_image = (np.maximum(new_image, 0) / new_image.max()) * 255.0
    scaled_image = np.uint8(scaled_image)
    final_image = Image.fromarray(scaled_image)
    final_image.save('image.png') # Save the image as PNG
   

def tipul_imaginii(filename): 
    global mod
    df = py.dcmread(filename)
    if df[0x8,0x60].value == 'CT':
        text = 'Computer Tomograf'
        mod = 0
    elif df[0x8,0x60].value == 'XA':
        text ='Angiografie'
        mod = 1
    elif df[0x8,0x60].value == 'US':
        text= 'Ecografie'
        mod = 2
    return mod   

#%%

def save_widget_as_image( file_name):
   ImageGrab.grab(bbox = (450,230,950,730)).save(file_name) #mac
   #ImageGrab.grab(bbox = (560,300,1200,950)).save(file_name) #windows
   showinfo(
       title='Saved',
       message='Imaginea a fost salvata cu succes'
   )
def get_x_and_y(event):
    global lasx, lasy
    lasx, lasy = event.x, event.y

def draw_smth(event):
    global lasx, lasy
    canvas.create_line((lasx, lasy, event.x, event.y), 
                      fill='red', 
                      width=2, smooth =1)
    lasx, lasy = event.x, event.y


#%%Functia de afisasre a imaginii 
#def afiseaza_imagine(filepath):
#    global img 
#    img = ImageTk.PhotoImage(Image.open(filepath))
#    label = Label(master, image = img)
#    label.place(x = 240+ 160, y = 200 + 30, width=500, height=500)
def afisare_canvas(filepath)  :  
    global canvas
    global image
    global file
    global locatie 
    locatie = '/Users/mariasavu/Desktop/fisier_proiect/Adnotari'
    canvas = Canvas(master,  height=500, width=500)
   
    image = Image.open(filepath)
    #image = image.resize((500,500), Image.ANTIALIAS)
    
    image = ImageTk.PhotoImage(image)
    canvas.create_image(0,0, image=image, anchor='nw')
    canvas.place(x= 450, y = 230)
   # canvas.bind("<Button-1>", get_x_and_y)
   # canvas.bind("<B1-Motion>", draw_smth)    
    canvas.bind("<Button-1>", on_canvas_click)
    canvas.bind("<B1-Motion>", on_canvas_drag)
    canvas.bind("<ButtonRelease-1>", on_canvas_release)
    im9 = PhotoImage(file = 'save.png')
    button_save =Button(master,text= 'save', command = lambda:save_widget_as_image( locatie +file+'.png'), bg ='skyblue')
    button_save.place(x = 140, y=750,anchor = 'center' )      
    
  

#%%Functia pentru selectia fisierului

#%%

#%%

def handler(event):
    global file 
    global f 
    selected_files = [lbox.get(index) for index in lbox.curselection()]
    if selected_files:
        for file in selected_files:
            showinfo(title='nou', message='S-a selectat fisier ' + file)
            f = py.dcmread(directory + '/' + file)
            tipul_imaginii(directory + '/' + file)
            afisare_informatii(f, mod)
            convert(directory + '/' + file)
            afisare_canvas(filepath_imag)
            lbox.selection_clear(0, tk.END)
            image_seg(directory + '/' + file)
            #master.after(1, lambda: showcontent(event))
    
def select_file():
     global directory
     global filepath_imag
     global lbox 

     filename = fd.askdirectory(
         title='Open a file',
         initialdir='/',
     )
     directory = filename 
    
     flist = os.listdir(directory)
     lbox.delete(0, tk.END)  # Clear the existing list box items

     
    
     for item in flist:
                lbox.insert(tk.END, item)

        
 #%% Afisare informatii 
def afisare_informatii(df,mod):
    global liste
    class tabel :
             
        def __init__(self,master,lst):
                      
            total_rows = len(lst)
            total_columns = len(lst[0])
            
            for c in range(total_rows):
                for j in range(total_columns):
                    l =Label(text=lst[c][j], relief=RIDGE, width=180,background = 'skyblue',foreground = 'blue4',font=('Arial',12,'bold'))
                    l.place(x = 10+ j*190, y = 200 + c*30, width=190, height=25)
            
    if mod == 0:
            liste =[('Nume Pacient',df['PatientName'].value),
                          ('ID Pacient', df['PatientID'].value),
                          ('Data',df['AcquisitionDate'].value),
                          ('Tipul imaginii', df['Modality'].value),
                          ('Distanta: sursa-detecor', df['DistanceSourceToDetector'].value),
                          ('Distanta: sursa-pacient', df['DistanceSourceToPatient'].value),
                          ('Aparatura folosita', df['ManufacturerModelName'].value),
                          ('Rescale Intercept', df['RescaleIntercept'].value),
                          ('Rescale Slope', df['RescaleSlope'].value),('Rezolutie', df['SpatialResolution'].value),('PixelSpacing', df['PixelSpacing'].value)
                         ]
    elif mod == 1:
            liste= [('Nume Pacient',df['PatientName'].value),
                      ('ID Pacient', df['PatientID'].value),
                      ('Tipul imaginii', df['Modality'].value),
                      ('Aparatura folosita', df['Manufacturer'].value),
                      ('Primary Angle', df['PositionerPrimaryAngle'].value),
                      ('Secondery Angle', df['PositionerSecondaryAngle'].value)
                      ] 
    elif mod == 2:
            liste = [('Nume Pacient',df['PatientName'].value),
                      ('ID Pacient', df['PatientID'].value),
                      ('Tipul imaginii', df['Modality'].value),
                      ('Aparatura folosita', df['Manufacturer'].value),
                      ('Interpretarea Fotometrica', df['PhotometricInterpretation'].value),
                      ('Number of frames', df['NumberOfFrames'].value)
                      ] 
        
   
    t = tabel(master,liste) 
       
#%% filtre pentru imagine     
    
    
    

def contrast():
    #global filepath_imag
    global original
    global copie 
    factor = w1.get()
    if bool(original):
       copie = original
       copie.save('copie.png')
       poza = ImageEnhance.Contrast(original)
       original = poza.enhance(factor)
       original.save('schimbare.png')
       #afiseaza_imagine('schimbare.png')
       afisare_canvas('schimbare.png')
    else :
        t = Image.open(filepath_imag)
        copie = t
        poza = ImageEnhance.Contrast(t)
        original = poza.enhance(factor)
        original.save('schimbare.png')
        #afiseaza_imagine('schimbare.png')
        afisare_canvas('schimbare.png')
def luminozitate():
    global original
    global copie
    factor = w2.get()
    
    if bool(original):
        copie = original
        poza =ImageEnhance.Brightness(original)
        original = poza.enhance(factor)
        original.save('schimbare.png')
        #afiseaza_imagine('schimbare.png')
        afisare_canvas('schimbare.png')
    else:
        t = Image.open(filepath_imag)
        copie = t
        poza =ImageEnhance.Brightness(t)
        original = poza.enhance(factor)
        original.save('schimbare.png')
        #afiseaza_imagine('schimbare.png')
        afisare_canvas('schimbare.png')
    

def sharpness():
    
    global original
    global copie
    factor = w3.get()
    if bool(original):
        copie = original
        poza =ImageEnhance.Sharpness(original)
        original = poza.enhance(factor)
        original.save('schimbare.png')
        #afiseaza_imagine('schimbare.png')
        afisare_canvas('schimbare.png')
    else:
        t = Image.open(filepath_imag)
                      
        copie = t
        poza =ImageEnhance.Sharpness(t)
        original = poza.enhance(factor)
        original.save('schimbare.png')
        #afiseaza_imagine('schimbare.png')
        afisare_canvas('schimbare.png')



    
  #%% Functii butoane   
def flip_orizontal():
        global copie
        t = Image.open(filepath_imag)
        copie = t
        original = t.transpose(Image.FLIP_TOP_BOTTOM)
        original.save('schimbare.png')
        afisare_canvas('schimbare.png')
        #afiseaza_imagine('schimbare.png')
        
def flip_vertical():
            global copie
            t = Image.open(filepath_imag)
            copie = t
            original = t.transpose(Image.FLIP_LEFT_RIGHT)
            original.save('schimbare.png')
            afisare_canvas('schimbare.png')
           # afiseaza_imagine('schimbare.png')
            
def revert():
        global original
        global copie
        
        original = Image.open(filepath_imag)
        copie = original
        afisare_canvas(filepath_imag)
        
def back():
        global original
        global copie
        if bool(copie):
         
            copie.save('copie.png')
            #afiseaza_imagine('copie.png') 
            afisare_canvas('copie.png')
            original = copie
        else:
            #afiseaza_imagine(filepath_imag)
            afisare_canvas(filepath_imag)
 #%% Functii de vizualizare a imaginii 
 
def window_image(img, window_center,window_width, intercept, slope, rescale=True):
     img = (img*slope +intercept) #for translation adjustments given in the dicom file. 
     img_min = window_center - window_width//2 #minimum HU level
     img_max = window_center + window_width//2 #maximum HU level
     img[img<img_min] = img_min #set img_min for all HU levels less than minimum HU level
     img[img>img_max] = img_max #set img_max for all HU levels higher than maximum HU level
     if rescale: 
         img = (img - img_min) / (img_max - img_min)*255.0 
     return img
     
def get_first_of_dicom_field_as_int(x):
     #get x[0] as in int is x is a 'pydicom.multival.MultiValue', otherwise get int(x)
     if type(x) == py.multival.MultiValue: return int(x[0])
     else: return int(x)
     
def get_windowing(data):
     dicom_fields = [data[('0028','1050')].value, #window center
                     data[('0028','1051')].value, #window width
                     data[('0028','1052')].value, #intercept
                     data[('0028','1053')].value] #slope
     return [get_first_of_dicom_field_as_int(x) for x in dicom_fields]

def view_images(im, title = '', aug = None, windowing = True):
  
     width = 2
     height = 2
     axs = plt.plot(height, width)
     

     data = py.dcmread(im)
     ajustare = data.pixel_array
     window_center , window_width, intercept, slope = get_windowing(data)
     if windowing:
             output = window_image(image, window_center, window_width, intercept, slope, rescale = False)
     else:
             output = image
             
     fig = plt.imshow(output,cmap=plt.cm.gray)
     plt.axis('off')
     plt.savefig("plot.png", transparent = True,bbox_inches='tight')
     plt.suptitle(title)
     plt.show()
     
dict = {"1000" : 1000, 
            "50": 50, 
            "20": 20, 
            "-1000" :-1000, 
            "0": 0, 
            "-100":100}


def int_print(window_center , window_width=700, intercept=-1024, slope=1):
  
    i = f.pixel_array
    output = window_image(i, window_center, window_width, intercept, slope, rescale=False)
    #plt.rcParams['figure.figsize'] = (9, 9)
    fig = plt.imshow(output, cmap=plt.cm.gray,aspect= 'auto')
    plt.axis('off')
    plt.savefig("plot.png", transparent=True, bbox_inches='tight')
   # plt.show()

def sel():
   global copie 
   selection =  str(var.get())
   label.config(text = 'Valoarea in HU : ' + selection)
   window_center = dict[selection]
   int_print(window_center)
   copie = Image.open('plot.png')
   afisare_canvas('plot.png')
   
 
def afisare_seg():
    afisare_canvas('imagine_segmentata.png')
 
 #%%
# Definirea interfetei 

master = Tk()
#master.geometry('1200x1200+50+50')
master.attributes('-fullscreen', True)
def minimizare_ecran():
    master.attributes('-fullscreen', False)
master.bind("<Escape>", minimizare_ecran())    
#master.configure(background='royalblue')
my_label = Label(master, text = "Dicom Viewer",foreground ='blue4', background= 'skyblue',font=('Arial',16,'bold'),anchor = 'center')
my_label.place(x = 1, y = 1, width = 1600, height= 100)

im7 = PhotoImage(file ='files.png')

my_button2 = Button(master, text = "File",command =select_file, bg='skyblue', image = im7)
my_button2.place(x = 90, y=750, anchor = 'center')

w1 =ttk.Scale(master, from_=-10, to=10,length=200, orient=HORIZONTAL)
w1.place(x = 1200,y = 200)
w2 = ttk.Scale(master, from_=0, to=5, orient=HORIZONTAL)
w2.place(x = 1200,y = 270)           
w3 = ttk.Scale(master, from_=-0, to=3, orient=HORIZONTAL)
w3.place(x = 1200,y = 340)
im4 = PhotoImage(file = 'contrast.png')
button = Button(master, command=contrast, image = im4,bg ='skyblue').place(x =1450,y =210)
im3 = PhotoImage(file = 'luminozitate.png')
button_2 = Button(master,  command=luminozitate,image= im3, bg ='skyblue').place(x =1450,y =280)
im8 = PhotoImage(file = 'sharp.png')
button_3 = Button(master, text='Sharpness', command=sharpness,bg ='skyblue', image = im8).place(x =1450,y =340)

path = './flip-icon-19.jpg'
im2 = Image.open(path)
img2 = im2.resize((25,25))
img2.save("nou.png")
im2 = PhotoImage(file = 'nou.png')
button_flip_orizontal = Button(master,command= flip_orizontal,image = im2, bg = 'skyblue').place(x=1400,y=150)

path1 = './vertical.jpg'
im = Image.open(path1)
img = im.resize((25,25))
img.save("vertical.png")

lbox = Listbox(master, selectmode = tk.MULTIPLE)
lbox.place(x = 30, y = 540 )
lbox.bind("<<ListboxSelect>>", handler)
im1 = PhotoImage(file = 'vertical.png')
button_flip_vertical = Button(master,command= flip_vertical,image = im1, bg='skyblue').place(x=1450,y=150)
im5 = PhotoImage(file = 'rename.png')
button_revert = Button(master, text = 'Revert',command= revert,image = im5, bg ='skyblue').place(x= 1350, y = 150)
im6 = PhotoImage(file = 'back.png')
button_back = Button(master, text = 'Back', command = back,bg ='skyblue',image = im6).place(x=1300, y = 150)
var = IntVar()
R1 = Radiobutton(master, text="Oase", variable=var, value=1000,
                  command=sel)
R1.place(x= 1200,y=400)
R2 = Radiobutton(master, text="Muschi", variable=var, value=50,
                  command=sel)
R2.place( x= 1200, y = 420)

R3 = Radiobutton(master, text="Sange", variable=var, value=20,
                  command=sel)
R3.place( x = 1200, y = 440)
R4 = Radiobutton(master, text="Aer", variable=var, value=-1000,
                  command=sel)
R4.place( x =1200, y= 460)

R5 = Radiobutton(master, text="Apa", variable=var, value=0,
                  command=sel)
R5.place(x= 1200, y=480 )

R6 = Radiobutton(master, text="Grasime", variable=var, value=-100,
                  command=sel)
R6.place(x = 1200, y =500)
label = Label(master)
label.place(x= 1200, y = 600)
seg_button = tk.Button(master, text= 'Afisare segmentare', command = afisare_seg).place(x= 1350, y = 550)
button_draw = tk.Button(master, text="Draw Line", command=draw_spline)
button_draw.place(x= 1350, y = 680)
button_delete = tk.Button(master, text="Delete Line", command=delete_line, state="disabled")
button_delete.place(x= 1350, y = 710)
points = []
line = None
selected_point = None
is_adjusting = False
label_seg_manuala = Label(master, text= "Adnotare manuala")
label_seg_manuala.place(x = 1350, y= 650)
button_adjust = tk.Button(master, text="Adjust Line", command=enable_adjustment, state="disabled")
button_adjust.place(x= 1350, y = 740)
button_save_mask = tk.Button(master, text="save mask", command=save_contour, state="disabled")
button_save_mask.place(x= 1350, y = 780)
entry_file_name = tk.Entry(master)
entry_file_name.place(x=1100, y=780)
mainloop()





#%%

# %%
