import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.io as scio
import os
import shutil
from scipy.integrate import trapz
from scipy import interpolate
import datetime as dt
import csv
import zipfile
import seaborn as sns
import copy
import pyGPs
from sklearn.svm import SVR
from datetime import datetime
from natsort import ns, natsorted
# In[ Extract capacity and charging data]
def find_samples_in_file(file):
    cha = file
    cha.reset_index(drop=True, inplace=True)
    cha_time = []
    for i in range(len(cha)):
        cha_time.append(str(cha['record_time'][i]))
    cha_time = pd.to_datetime(np.array(cha_time))
    cha_time = pd.DataFrame(cha_time)
    
    aaa = cha_time.iloc[1:]
    aaa.reset_index(drop=True, inplace=True)
    bbb = cha_time.iloc[:-1]
    bbb.reset_index(drop=True, inplace=True)
    time_delta = (aaa - bbb)
    interval = dt.timedelta(seconds=10)
    
    rest_index = []
    for i in range(len(time_delta)):
        # i = 1
        if time_delta.iloc[i,0] > interval:
            rest_index.append(i)
    
    cha_list = []
    cha_list.append(cha.iloc[:rest_index[0]])
    for i in range(len(rest_index)-1):
        cha_cut = cha.iloc[rest_index[i]+1:rest_index[i+1]]
        cha_list.append(cha_cut)
    cha_list.append(cha.iloc[rest_index[-1]+1:])
    
    Ca_list = []
    cha_list_out = []
    for j in range(len(cha_list)):
        # j = 10
        cha_cut = cha_list[j]
        cha_cut.reset_index(drop=True, inplace=True)
        if len(cha_cut)<100:
            continue
        dif_soc = cha_cut['soc'][1:] - cha_cut['soc'][:-1]
        if np.sum(dif_soc>2) or np.sum(dif_soc<-0.1):
            continue
        time = []
        for i in range(len(cha_cut)):
            # i = 1
            time.append(str(cha_cut['record_time'][i]))
        time = np.array(time)
        time = pd.to_datetime(time)
        
        current = cha_cut['charge_current']
        soc = cha_cut['soc']
        Tmax= np.mean(cha_cut['max_temperature'])
        Tmin= np.mean(cha_cut['min_temperature'])
        # tem = cha_cut['vehoutsidetemp']
        label_Ca = real_capacity_cal(time,current,soc)
        if label_Ca==0:
            continue
        Ca_list.append([time[0],time[len(time)-1],soc[0],soc[len(time)-1],label_Ca,Tmax,Tmin])
        cha_list_out.append(cha_cut)
        
    return Ca_list,cha_list_out
def real_capacity_cal(time_data,current,SOC_data):
    if np.sum(np.isnan(current.tolist()))>len(current)*0.1:
        return []
    if np.sum(np.isnan(current.tolist())):
        for n in range(len(current)):
            if np.isnan(current[n]):
                current[n]=current[n-1]
    time_sec=np.zeros(len(current))
    for j in range(len(current)):
        time_temp = time_data[j] - time_data[0]
        time_sec[j]=time_temp.total_seconds()
    accumulated_Q=trapz(current,time_sec)/3600*(-1)
    delta_SOC=SOC_data[len(SOC_data)-1]-SOC_data[0]
    if delta_SOC==0:
        return 0
    label_Ca = accumulated_Q/delta_SOC*100
    return label_Ca
def func(file_path):
    src_path = file_path    
    file = pd.read_csv(src_path)
    file.columns = ['number','record_time','soc','pack_voltage','charge_current','max_cell_voltage',
                    'min_cell_voltage','max_temperature','min_temperature','available_energy','available_capacity']
    file = file.sort_values(by='record_time')
    file.reset_index(drop=True, inplace=True)
    # file=file.dropna(axis=0,how='any') #exclude 'nan' data
    ca_list,cha_data_list = find_samples_in_file(file)
    return ca_list,cha_data_list #return Ca and charging data for every vehicle  
if __name__ == '__main__':
    main_path='..\\vehicles\\'
    dird=os.listdir(main_path)
    dird=natsorted(dird,alg=ns.PATH)
    data_list=[]
    for veh in range(len(dird)):
    # for veh in range(1):    
        try:
            print(veh,' vehicle_num:',dird[veh])
            file_path = main_path+dird[veh]
            data_list.append(func(file_path))
        except:
            print(veh,' ',dird[veh],'error')
# In[ Plot Capacity curves ]  
from matplotlib import rcParams
params={'font.family':'serif',
        'font.serif':'Times New Roman',
        'font.style':'normal',
        'font.weight':'normal', #or 'blod'
        'font.size':12,#or large,small
        }
rcParams.update(params)
plt.figure(figsize=(16,16),dpi=600)
plt.subplots_adjust(left=None, bottom=None, right=None, top=None,
        wspace=0.30, hspace=0.45)
for j in range(len(data_list)):
    veh_data = data_list[j]
    ca_list = veh_data[0]
    cha_list = veh_data[1]
    veh_df = pd.DataFrame(data=ca_list,columns=['time_s','time_e','SOC_s','SOC_e','charge_capacity','Tmax','Tmin'])
    plt.subplot(4,5,j+1)
    plt.plot(veh_df.iloc[:,0],veh_df.iloc[:,4],'o')
    plt.ylabel('Capacity (Ah)')
    plt.xlabel('Date')
    plt.ylim([90,150])
    plt.title('#'+str(j+1),x=0.1,y=0.1)
    plt.xticks(rotation=90)
plt.show() 
# In[ Plot Capacity curves after stastical analysis]
from datetime import datetime
plt.figure(figsize=(16,16),dpi=600)
plt.subplots_adjust(left=None, bottom=None, right=None, top=None,
    wspace=0.30, hspace=0.45)
for j in range(len(data_list)):
    veh_data = data_list[j]
    ca_list = veh_data[0]
    cha_list = veh_data[1]
    veh_df = pd.DataFrame(data=ca_list,columns=['time_s','time_e','SOC_s','SOC_e','charge_capacity','Tmax','Tmin'])
    veh_df.reset_index(drop=True, inplace=True)
    cnt=0
    time_index=[]
    time_index.append(veh_df.time_e[0])
    veh_name=cha_list[0].values[0,0]
    veh_df.reset_index(drop=True, inplace=True)
    cnt=0
    time_index=[]
    time_index.append(veh_df.time_e[0])
    ca_month=[]
    ca_temp=[]
    for i in range(len(veh_df)):
        if(veh_df.time_e[i].year==time_index[cnt].year)and(veh_df.time_e[i].month==time_index[cnt].month):
            ca_temp.append(veh_df.charge_capacity[i])
        else:
            ca_month.append(ca_temp)
            cnt=cnt+1
            time_index.append(veh_df.time_e[i])
            ca_temp=[]
            ca_temp.append(veh_df.charge_capacity[i])
    ca_month.append(ca_temp)
    print(j)
    veh_ca1 = [np.mean(p) for p in ca_month] 
    veh_ca2 = [np.median(p) for p in ca_month] 
    plt.subplot(4,5,j+1)
    plt.plot(time_index,veh_ca1)
    plt.plot(time_index,veh_ca2,'-.')
    # plt.title(dird[i].split('M')[-1])
    plt.title('#'+str(j+1),x=0.1,y=0.1)
    plt.xticks(rotation=90)
    plt.yticks(np.arange(110,135,6))
    plt.ylabel('Capacity (Ah)')
    plt.xlabel('Date')
    plt.legend(['Mean','Median'],loc=1)
plt.show()