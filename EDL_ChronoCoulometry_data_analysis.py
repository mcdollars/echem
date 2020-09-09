import os, re
from EDL_functions import complete_fname, complete_fname_ab, find_pulse, find_mean, plot2y
#import matplotlib.pyplot as plt

electrode = "GC"
electrolyte = "NaF"
concentration = "0.5M"
amp_as_bias = True
txt_folder = "normalized"

if amp_as_bias:
    concentration = concentration + "_ab"

os.chdir("../EDL/" + electrode + "/" + electrolyte + "/" + concentration + "/raw")
cur_path = os.getcwd()
parent_path = os.path.abspath(os.path.join(cur_path, os.pardir))
DAT_LNE1 = re.compile('^\t0\t') #the word at the begining of the line indicating step1 voltage 

index_label = "Index"
t_label = "Time(s)"
Q_label = "Q(C)"
I_label = "I(A)"
V_label = "V(V)"
C_label = "Capacitance(F)"
V_Q = []

output_file_name = electrode + "_" + electrolyte + "_" + concentration

for filename in os.listdir():

    file_path = os.path.join(cur_path, filename)
    f = open(file_path,'r')
    
    data_flag = False
    index = []
    t = []
    Q = []
    V = []
    I = []
    V_Q_dict = {}
    pulse_time = {}
    
    txt_file_name = output_file_name
    bias = 0 #a random input to find the true bias
    
    for line in f:
        
        if amp_as_bias == True:
            txt_file_name, bias = complete_fname_ab(line, txt_file_name, bias)
        else:
            txt_file_name, bias = complete_fname(line, txt_file_name, bias)
        pulse_time = find_pulse(line, pulse_time)
        
        if DAT_LNE1.search(line) or data_flag==True:
            line_list = line.strip().split('\t')
            index.append(int(line_list[0]))
            t.append(float(line_list[1]))
            Q.append(float(line_list[2]))
            V.append(float(line_list[3]))
            I.append(float(line_list[4]))
            data_flag = True
        
    pre_pts = int(pulse_time["pre"]/pulse_time["rate"]) #50
    step1_pts = pre_pts + int(pulse_time["step1"]/pulse_time["rate"]) #100
    step2_pts = step1_pts + int(pulse_time["step2"]/pulse_time["rate"]) #150
    
    I_bg = find_mean(I, 0, pre_pts-1 ) #find the mean value from point 0 to pre_pts-2
    I_R1 = find_mean(I, (step1_pts-5), step1_pts)
    I_R2 = find_mean(I, (step2_pts-5), step2_pts)
    
    I_t = []
    Q_t = []
    Q_t_j = 0
    j_max = len(t)
    
    txt_file_path = os.path.join(parent_path, (txt_folder + "/" + txt_file_name))
    txt_f = open(txt_file_path,'w')
    txt_f.write(index_label + "\t" + t_label + "\t" + Q_label + "\t" + I_label + "\t" + V_label + "\n")
    
    for j in range(0, j_max):
        
        if j<pre_pts:
            I_t_j = I[j] - I_bg
            Q_t_j = 0
        elif j>(pre_pts-1) and j<(step1_pts):
            I_t_j = I[j] - I_R1
            Q_t_j = 0
        else:
            I_t_j = I[j] - I_R2
            Q_t_j = Q_t_j - I_t_j*pulse_time["rate"]
            
        I_t.append( I_t_j )
        Q_t.append( Q_t_j )
        
        
        txt_f.write(str(index[j]) + "\t" + str(t[j]) + "\t" + str(Q_t_j) + "\t" + str(I_t_j) + "\t" + str(V[j]) + "\n")
            
    txt_f.close()
    
    V_Q_dict[V_label] = bias
    V_Q_dict[Q_label] = Q_t[step2_pts-1] - I_t_j*0.005
    V_Q.append(V_Q_dict)
    V_Q.sort(key= lambda d: float(d[V_label]))
    
    f.close()
    
    
Q_file_path = os.path.join(parent_path, (output_file_name + ".txt"))
Q_f = open(Q_file_path,'w')
Q_f.write(V_label + "\t" + Q_label + "\t" + C_label + "\n")

V_b = []
Q_b = []
C_d = []
#C_b = []
#k = 0

for item in V_Q:
    V_b.append(item[V_label])
    Q_b.append(item[Q_label])
#    if item[V_label]<0: #this is for 0.5M only
#        Q_b.append(-1*item[Q_label])
#    else:
#        Q_b.append(item[Q_label])
    
#    if item[V_label] != 0: #calculate capacitance directly
#        C_b_k = item[Q_label]/item[V_label]
#    else:
#        C_b_k = C_b[k-1]
#    C_b.append(C_b_k)
#    k=k+1

k_max = len(V_b)

for k in range(0, k_max):
    if k == 0:
        C_d_k = (Q_b[1]-Q_b[0]) / (V_b[1]-V_b[0])
    elif k == k_max-1:
        C_d_k = (Q_b[k_max-1]-Q_b[k_max-2]) / (V_b[k_max-1]-V_b[k_max-2])
    else:
        C_d_k = (Q_b[k+1]-Q_b[k-1]) / (V_b[k+1]-V_b[k-1])
        
    C_d.append(C_d_k)
    Q_f.write(str(V_b[k]) + "\t" + str(Q_b[k]) + "\t" + str(C_d_k) + "\n")
    

plot2y(V_b, Q_b, C_d, V_label, Q_label, C_label)

Q_f.close()