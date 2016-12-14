from __future__ import print_function
import sqlite3
import xlrd
import xlwt
import socket
import re
import threading
import time 
import datetime
import sys
from Queue import Queue
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from MRMFB import M_RMFB
from Find_lmd import M_RM_lmd
from Find_lmd import M_FB_lmd
import Morder as MO
import Mpara as MP
import Mcheck as MC
import MCheckPara as MCP
import MPlaceOrder as MPO


def DataAnalysis(paper, exchange, price2, volumne2):
    print('run data analysis')
    Citt = 0    #0-don't have this share, 1- have bought this share
    Cdata = 0   #0-can't  find control data, won't run buy or sell activity, 1-get control data
    Cmethod = 0  #0-select by program, 1-RM model, 2-FB model
    Clevel = 0  #1 - 4, 1 is most important 
    Ctype = 0 #1 is normal buying, 2 is shorting selling
    today1 = datetime.date.today()
    if today1.weekday() == 0:
        lastday = today1 - datetime.timedelta(days=3)
    else:
        lastday = today1 - datetime.timedelta(days=1)
    
    time2 = time.time()
    time2 = time.localtime(time2)
    time1 = time.asctime(time2) 


    hour1 = time2.tm_hour        
    min1 = time2.tm_min
    sec1 = time2.tm_sec
    
    firstTrade = 0
    if exchange == 'ST' or exchange == 'OSE':
        if hour1 == 9 and min1 < 30:
            firstTrade = 1
        else:
            firstTrade = 0
    else:
        if hour1 == 15 and min1 < 59:
            firstTrade = 1
        else:
            firstTrade = 0
#    MP.controlPara()
    try:
        Camount = MP.control1.ix[paper,'Limit']
        Citt = MP.control1.ix[paper,'Citt']
        Cmethod = MP.control1.ix[paper,'Cmethod']
        Cquantity = MP.control1.ix[paper,'Quantity']
        Cquantity = int(Cquantity)
        Cnumber = MP.control1.ix[paper,'number']
        Ctype = MP.control1.ix[paper,'Ctype']
        Cdata = 1
  
    except Exception as e:
        print( 'cant find the control data!')
        with open('Errorlog.txt','a') as f:
            print(time1,paper,'Control data read error!','Reason: ', e, file = f) 
        Cdata = 0
    print(Camount, Citt, Cmethod, Cnumber, Ctype)
    lmdRM_name1 = 'lmdRM'+'-'+exchange+'.csv'
    lmdFB_name1 = 'lmdFB'+'-'+exchange+'.csv'
    lmdRM_name2 = 'lmdRM'+'-'+exchange+'_S.csv'
    lmdFB_name2 = 'lmdFB'+'-'+exchange+'_S.csv'
    
    if Ctype == 1:
        lmdRM_name = lmdRM_name1
        lmdFB_name = lmdFB_name1
    elif Ctype == 2:
        lmdRM_name = lmdRM_name2
        lmdFB_name = lmdFB_name2
    else:
        lmdRM_name = lmdRM_name1  ##defaut using normal file
        lmdFB_name = lmdFB_name1
        with open('Errorlog.txt','a') as f:
            print(time1,paper,'Ctype = ', Ctype,' Ctype read error', file = f)
    
    database_str = 'HistoryPrice.db'
    conn = sqlite3.connect(database_str)
    c = conn.cursor()

    c.execute('SELECT PAPER , PRICE, VOLUMNE FROM HISTORY WHERE PAPER = ?', (paper,)); 
    a1 = c.fetchall()
    num_p = len(a1)
    a2 = pd.DataFrame(a1)
    pric = a2[1]
    volu = a2[2]
    price3= price2*1.01  #price3 for assume buy quantity
    if price2 == 0:
        price2 = pric[len(pric)-1]
    
    price2 = {num_p: price2}
    volumne2 = {num_p: volumne2}
    price2 = pd.DataFrame.from_dict(price2,orient='index')
    volumne2 = pd.DataFrame.from_dict(volumne2,orient='index')
    pric = pric.append(price2)
    volu = volu.append(volumne2)
    n1 = 1
    n2 = volu.shape[0]
    try:
        t2 = M_RM_lmd(lmdRM_name,paper)
        lmd1 = t2[0]
        rmax1 = t2[1]
        t3 = M_FB_lmd(lmdFB_name,paper)
        lmd2 = t3[0]
        rmax2 = t3[1]
        t1 = M_RMFB(paper, pric, volu, lmd1,lmd2)
    except Exception as e:
        with open('Errorlog.txt','a') as f:
            print(time1,paper,'lmd read error','Reason:',e, file = f)
    #with open('Errorlog.txt','a') as f:
    #        print(Cmethod,rmax1, rmax2, file = f)
    avmdp1 = t1[0]
    avmdn1 = t1[1]
    avmood1 = t1[2]
    aadnp2 = t1[3]
    aadnn2 = t1[4]
    aaupn2 = t1[5]
    aaupp2 = t1[6]
    az2 = t1[7]  

    string4 = 'E'
    string5 = 'E'
    string6 = 'E'
    string8 = 'E'
    percent = 0.04

    if Cnumber > 0 and Cdata == 1: 
        if Ctype == 1:
            if Cmethod == 1:
                if avmood1[n2-2] >= 0 and avmood1[n2-1]>0 and Citt==0.0:
                    if MCP.checkPara(paper, today1) == 0:
                        (avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, lastday)
                        if avmood1_2 <= 0:                    
                            quantity = int(Camount/price3)
                            idt1 = 'B'
                            short = 'normal'
                            Onumber = '01'                
                            MPO.placeOrder(paper, exchange, idt1, quantity, short, Cnumber, Onumber, Citt)
		    else:
                        (avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, today1)
                        if avmood1_2 <= 0:                    
                            quantity = int(Camount/price3)
                            idt1 = 'B'
                            short = 'normal'
                            Onumber = '10'                
                            MPO.placeOrder(paper, exchange, idt1, quantity, short, Cnumber, Onumber, Citt) 
                
                elif avmood1[n2-2] < 0 and avmood1[n2-1]<0 and Citt==1.0:
                    if MCP.checkPara(paper, today1) == 0:
                        (avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, lastday)
                        if avmood1_2 > 0:
                            idt1 = 'S'
                            short = 'normal'
                            Onumber = '01'                               
                            MO.list_acc()
                            try:
                                Cquantity = MP.control1.ix[paper,'Quantity']
                                Cquantity = int(Cquantity)
				MPO.placeOrder(paper, exchange, idt1, Cquantity, short, Cnumber, Onumber, Citt)                        
                            except Exception as e:
                                print( 'cant find the control data!')
                                with open('Errorlog.txt','a') as f:
                                    print(time1,paper,'Control data read error!','Reason: ', e, file = f)                                                                                         
                    else:
                        (avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, today1)
                        if avmood1_2 > 0:
                            idt1 = 'S'
                            short = 'normal'
                            Onumber = '10'                               
                            MO.list_acc()
                            try:
                                Cquantity = MP.control1.ix[paper,'Quantity']
                                Cquantity = int(Cquantity)
                                MPO.placeOrder(paper, exchange, idt1, Cquantity, short, Cnumber, Onumber, Citt)								
                            except Exception as e:
                                print( 'cant find the control data!')
                                with open('Errorlog.txt','a') as f:
                                    print(time1,paper,'Control data read error!','Reason: ', e, file = f)                          
                elif avmood1[n2-2] <= 0 and avmood1[n2-1]>0 and Citt==0.0:
                    quantity = int(Camount/price3)
                    idt1 = 'B'
                    short = 'normal'
                    Onumber = '1'                
                    MPO.placeOrder(paper, exchange, idt1, quantity, short, Cnumber, Onumber, Citt)
        
                elif avmood1[n2-2] >0 and avmood1[n2-1]<=0 and Citt==1.0:
                    idt1 = 'S'
                    short = 'normal'
                    Onumber = '1' 
                    MO.list_acc()               
                    try:
                        Cquantity = MP.control1.ix[paper,'Quantity']
                        Cquantity = int(Cquantity)
                        MPO.placeOrder(paper, exchange, idt1, Cquantity, short, Cnumber, Onumber, Citt)								
                    except Exception as e:
                        print( 'cant find the control data!')
                        with open('Errorlog.txt','a') as f:
                            print(time1,paper,'Control data read error!','Reason: ', e, file = f)
            elif Cmethod == 2:
                if aadnp2[n2-2] > 0 and aadnp2[n2-1]>0 and aaupn2[n2-1] == 0 and Citt==0:
                    if MCP.checkPara(paper, today1) == 0:
                        (avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, lastday)
			if aadnp2_1 == 0 or aaupn2_1 < 0:
			    quantity = int(Camount/price3)
                            idt1 = 'B'
                            short = 'normal'
                            Onumber = '02'                
                            MPO.placeOrder(paper, exchange, idt1, quantity, short, Cnumber, Onumber, Citt)
		    else:
			(avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, today1)
			if aadnp2_1 == 0 or aaupn2_1 < 0:
			    quantity = int(Camount/price3)
                            idt1 = 'B'
                            short = 'normal'
                            Onumber = '20'                
                            MPO.placeOrder(paper, exchange, idt1, quantity, short, Cnumber, Onumber, Citt)
              
                elif aadnp2[n2-2] == 0 and aadnp2[n2-1]>0 and aaupn2[n2-1] == 0 and Citt==0:
                    quantity = int(Camount/price3)
                    idt1 = 'B'
                    short = 'normal'
                    Onumber = '2'                
                    MPO.placeOrder(paper, exchange, idt1, quantity, short, Cnumber, Onumber, Citt)                        
                    
                elif aadnp2[n2-1] == 0 and Citt==1.0:
		    if MCP.checkPara(paper, today1) == 0:
                        (avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, lastday)
			if aadnp2_1 > 0:
                            idt1 = 'S'
			    short = 'normal'
			    Onumber = '02'  
			    MO.list_acc()
			    try:
				Cquantity = MP.control1.ix[paper,'Quantity']
				Cquantity = int(Cquantity) 
				MPO.placeOrder(paper, exchange, idt1, Cquantity, short, Cnumber, Onumber, Citt)						
			    except Exception as e:
				print( 'cant find the control data!')
				with open('Errorlog.txt','a') as f:
				    print(time1,paper,'Control data read error!','Reason: ', e, file = f) 
		    else:
			(avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, today1)
			if aadnp2_1 > 0:
			    idt1 = 'S'
			    short = 'normal'
			    Onumber = '2'  
			    MO.list_acc()
			    try:
				Cquantity = MP.control1.ix[paper,'Quantity']
				Cquantity = int(Cquantity) 
				MPO.placeOrder(paper, exchange, idt1, Cquantity, short, Cnumber, Onumber, Citt)						
			    except Exception as e:
				print( 'cant find the control data!')
				with open('Errorlog.txt','a') as f:
				    print(time1,paper,'Control data read error!','Reason: ', e, file = f)
            elif(Cmethod == 0 and rmax1 >= rmax2):   
                if avmood1[n2-2] >= 0 and avmood1[n2-1]>0 and Citt==0:
                    if MCP.checkPara(paper, today1) == 0:
                        (avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, lastday)
                        if avmood1_2 <= 0:                        
                            quantity = int(Camount/price3)
                            idt1 = 'B'
                            short = 'normal'
                            Onumber = '03'                
                            MPO.placeOrder(paper, exchange, idt1, quantity, short, Cnumber, Onumber, Citt)
		    else:
                        (avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, today1)
                        if avmood1_2 <= 0:                    
                            quantity = int(Camount/price3)
                            idt1 = 'B'
                            short = 'normal'
                            Onumber = '30'                
                            MPO.placeOrder(paper, exchange, idt1, quantity, short, Cnumber, Onumber, Citt)
                elif avmood1[n2-2] < 0 and avmood1[n2-1]<0 and Citt==1.0:
                    if MCP.checkPara(paper, today1) == 0:
                        (avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, lastday)
                        if avmood1_2 > 0:
                            idt1 = 'S'
                            short = 'normal'
                            Onumber = '03' 
                            MO.list_acc()
                            try:
                                Cquantity = MP.control1.ix[paper,'Quantity']
                                Cquantity = int(Cquantity) 
                                MPO.placeOrder(paper, exchange, idt1, Cquantity, short, Cnumber, Onumber, Citt)								
                            except Exception as e:
                                print( 'cant find the control data!')
                                with open('Errorlog.txt','a') as f:
                                    print(time1,paper,'Control data read error!','Reason: ', e, file = f)           
		    else:
                        (avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, today1)
                        if avmood1_2 > 0:
                            idt1 = 'S'
                            short = 'normal'
                            Onumber = '30'                               
                            MO.list_acc()
                            try:
                                Cquantity = MP.control1.ix[paper,'Quantity']
                                Cquantity = int(Cquantity) 
                                MPO.placeOrder(paper, exchange, idt1, Cquantity, short, Cnumber, Onumber, Citt)								
                            except Exception as e:
                                print( 'cant find the control data!')
                                with open('Errorlog.txt','a') as f:
                                    print(time1,paper,'Control data read error!','Reason: ', e, file = f)         
    
                elif avmood1[n2-2] <=0 and avmood1[n2-1]>0 and Citt==0.0:
                    quantity = int(Camount/price3)
                    idt1 = 'B'
                    short = 'normal'
                    Onumber = '3'                
                    MPO.placeOrder(paper, exchange, idt1, quantity, short, Cnumber, Onumber, Citt)   
   
                elif avmood1[n2-2] >0 and avmood1[n2-1]<=0 and Citt==1.0:
                    idt1 = 'S'
                    short = 'normal'
                    Onumber = '3'    
                    MO.list_acc()
                    try:

                        Cquantity = MP.control1.ix[paper,'Quantity']
                        Cquantity = int(Cquantity)
                        MPO.placeOrder(paper, exchange, idt1, Cquantity, short, Cnumber, Onumber, Citt)
                    except Exception as e:
                        print( 'cant find the control data!')
                        with open('Errorlog.txt','a') as f:
                            print(time1,paper,'Control data read error!','Reason: ', e, file = f)             
 
            elif(Cmethod == 0 and rmax1 < rmax2):   
                if aadnp2[n2-2]>0 and aadnp2[n2-1]>0 and aaupn2[n2-1] == 0 and Citt==0:
                    if MCP.checkPara(paper, today1) == 0:
                        (avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, lastday)
			if aadnp2_1 == 0 or aaupn2_1 < 0:
			    quantity = int(Camount/price3)
			    idt1 = 'B'
                            short = 'normal'
                            Onumber = '04'                
                            MPO.placeOrder(paper, exchange, idt1, quantity, short, Cnumber, Onumber, Citt)  	
                    else:
			(avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, today1)
			if aadnp2_1 == 0 or aaupn2_1 < 0:
			    quantity = int(Camount/price3)
                            idt1 = 'B'
                            short = 'normal'
                            Onumber = '40'                
                            MPO.placeOrder(paper, exchange, idt1, quantity, short, Cnumber, Onumber, Citt)            
                elif aadnp2[n2-2] == 0 and aadnp2[n2-1]>0 and aaupn2[n2-1] ==0 and Citt==0.0:

                    quantity = int(Camount/price3)
                    idt1 = 'B'
                    short = 'normal'
                    Onumber = '4'                
                    MPO.placeOrder(paper, exchange, idt1, quantity, short, Cnumber, Onumber, Citt)   

                elif aadnp2[n2-1] ==0 and Citt==1.0:
                    if MCP.checkPara(paper, today1) == 0:
                        (avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, lastday)
			if aadnp2_1 > 0:
                            idt1 = 'S'
			    short = 'normal'
			    Onumber = '04'  
			    MO.list_acc()
			    try:
				Cquantity = MP.control1.ix[paper,'Quantity']
				Cquantity = int(Cquantity) 
			        MPO.placeOrder(paper, exchange, idt1, Cquantity, short, Cnumber, Onumber, Citt)						
			    except Exception as e:
				print( 'cant find the control data!')
			        with open('Errorlog.txt','a') as f:
				    print(time1,paper,'Control data read error!','Reason: ', e, file = f) 
		    else:
			(avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, today1)
			if aadnp2_1 > 0:
			    idt1 = 'S'
			    short = 'normal'
			    Onumber = '40'  
			    MO.list_acc()
			    try:
				Cquantity = MP.control1.ix[paper,'Quantity']
				Cquantity = int(Cquantity) 
				MPO.placeOrder(paper, exchange, idt1, Cquantity, short, Cnumber, Onumber, Citt)						
			    except Exception as e:
				print( 'cant find the control data!')
				with open('Errorlog.txt','a') as f:
				    print(time1,paper,'Control data read error!','Reason: ', e, file = f)            
                        
        elif Ctype == 2:
            if Cmethod == 1:
                if avmood1[n2-2] < 0 and avmood1[n2-1]<0 and Citt==0.0:
                    if MCP.checkPara(paper, today1) == 0:
                        (avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, lastday)
                        if avmood1_2 > 0:
                            quantity = int(Camount/price3)
                            idt1 = 'S'
                            short = 'Short'
                            Onumber = '01'                
                            MPO.placeOrder(paper, exchange, idt1, quantity, short, Cnumber, Onumber, Citt) 
                    else:
                        (avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, today1)
                        if avmood1_2 > 0:
                            quantity = int(Camount/price3)
                            idt1 = 'S'
                            short = 'Short'
                            Onumber = '10'                
                            MPO.placeOrder(paper, exchange, idt1, quantity, short, Cnumber, Onumber, Citt)                   
                if avmood1[n2-2] >= 0 and avmood1[n2-1]>0 and Citt==1.0:
                    if MCP.checkPara(paper, today1) == 0:
                        (avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, lastday)
                        if avmood1_2 <= 0:
                            idt1 = 'B'
                            short = 'short'
                            Onumber = '01' 
                            MO.list_acc()
                            try:

                                Cquantity = MP.control1.ix[paper,'BroShare']
                                Cquantity = int(Cquantity)
                                MPO.placeOrder(paper, exchange, idt1, Cquantity, short, Cnumber, Onumber, Citt)
                            except Exception as e:
                                print( 'cant find the control data!')
                                with open('Errorlog.txt','a') as f:
                                    print(time1,paper,'Control data read error!','Reason: ', e, file = f)                
                             
                    else:
                        (avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, today1)
                        if avmood1_2 <= 0:                    
                            idt1 = 'B'
                            short = 'short'
                            Onumber = '10' 
                            MO.list_acc()
                            try:
                                Cquantity = MP.control1.ix[paper,'BroShare']
                                Cquantity = int(Cquantity)
                                MPO.placeOrder(paper, exchange, idt1, Cquantity, short, Cnumber, Onumber, Citt)
                            except Exception as e:
                                print( 'cant find the control data!')
                                with open('Errorlog.txt','a') as f:
                                    print(time1,paper,'Control data read error!','Reason: ', e, file = f)    
                if avmood1[n2-2] > 0 and avmood1[n2-1]<=0 and Citt==0.0:
                    quantity = int(Camount/price3)
                    idt1 = 'S'
                    short = 'Short'
                    Onumber = '1'                
                    MPO.placeOrder(paper, exchange, idt1, quantity, short, Cnumber, Onumber, Citt) 
                        
                if avmood1[n2-2] <=0 and avmood1[n2-1]>0 and Citt==1.0:
                    idt1 = 'B'
                    short = 'Short'
                    Onumber = '1'  
                    MO.list_acc()
                    try:
                        Cquantity = MP.control1.ix[paper,'BroShare']
                        Cquantity = int(Cquantity)
                        MPO.placeOrder(paper, exchange, idt1, Cquantity, short, Cnumber, Onumber, Citt) 
                    except Exception as e:
                        print( 'cant find the control data!')
                        with open('Errorlog.txt','a') as f:
                            print(time1,paper,'Control data read error!','Reason: ', e, file = f)
            elif Cmethod == 2:
                if aadnp2[n2-2]>0 and aadnp2[n2-1]>0 and aaupn2[n2-1] == 0 and Citt==1:				
                    if MCP.checkPara(paper, today1) == 0:
                        (avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, lastday)
		        if aadnp2_1 == 0 or aaupn2_1 < 0:
                            idt1 = 'B'
                            short = 'Short'
                            Onumber = '02'  
                            MO.list_acc()
                            try:
                                Cquantity = MP.control1.ix[paper,'BroShare']
                                Cquantity = int(Cquantity)
                                MPO.placeOrder(paper, exchange, idt1, Cquantity, short, Cnumber, Onumber, Citt) 
                            except Exception as e:
                                print( 'cant find the control data!')
                                with open('Errorlog.txt','a') as f:
                                    print(time1,paper,'Control data read error!','Reason: ', e, file = f)               
                            
                    else:
			(avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, today1)
			if aadnp2_1 == 0 or aaupn2_1 < 0:
			    idt1 = 'B'
                            short = 'Short'
                            Onumber = '20'  
                            MO.list_acc()
                            try:
                                Cquantity = MP.control1.ix[paper,'BroShare']
                                Cquantity = int(Cquantity)
                                MPO.placeOrder(paper, exchange, idt1, Cquantity, short, Cnumber, Onumber, Citt) 
                            except Exception as e:
                                print( 'cant find the control data!')
                                with open('Errorlog.txt','a') as f:
                                    print(time1,paper,'Control data read error!','Reason: ', e, file = f) 

                elif aadnp2[n2-2] == 0 and aadnp2[n2-1]>0 and aaupn2[n2-1] == 0 and Citt==1:
                    idt1 = 'B'
                    short = 'Short'
                    Onumber = '2' 
                    MO.list_acc()
                    try:
                        Cquantity = MP.control1.ix[paper,'BroShare']
                        Cquantity = int(Cquantity)
                        MPO.placeOrder(paper, exchange, idt1, Cquantity, short, Cnumber, Onumber, Citt)
                    except Exception as e:
                        print( 'cant find the control data!')
                        with open('Errorlog.txt','a') as f:
                            print(time1,paper,'Control data read error!','Reason: ', e, file = f)                
                elif aadnp2[n2-1] == 0 and Citt==0.0:
		    if MCP.checkPara(paper, today1) == 0:
                        (avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, lastday)
			if aadnp2_1 > 0:
			    quantity = int(Camount/price3)
			    idt1 = 'S'
			    short = 'Short'
			    Onumber = '02'                
			    MPO.placeOrder(paper, exchange, idt1, quantity, short, Cnumber, Onumber, Citt) 
		    else:
			(avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, today1)
			if aadnp2_1 > 0:
			    quantity = int(Camount/price3)
			    idt1 = 'S'
			    short = 'Short'
			    Onumber = '20'                
			    MPO.placeOrder(paper, exchange, idt1, quantity, short, Cnumber, Onumber, Citt) 
            elif(Cmethod == 0 and rmax1 >= rmax2): 
                if avmood1[n2-2] < 0 and avmood1[n2-1]<0 and Citt==0.0:
                    if MCP.checkPara(paper, today1) == 0:
                        (avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, lastday)
                        if avmood1_2 > 0:
                            quantity = int(Camount/price3)
                            idt1 = 'S'
                            short = 'Short'
                            Onumber = '03'                
                            MPO.placeOrder(paper, exchange, idt1, quantity, short, Cnumber, Onumber, Citt) 
                    else:
                        (avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, today1)
                        if avmood1_2 > 0:
                            quantity = int(Camount/price3)
                            idt1 = 'S'
                            short = 'Short'
                            Onumber = '30'                
                            MPO.placeOrder(paper, exchange, idt1, quantity, short, Cnumber, Onumber, Citt)                 
                if avmood1[n2-2] >= 0 and avmood1[n2-1]>0 and Citt==1.0:
                    if MCP.checkPara(paper, today1) == 0:
                        (avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, lastday)
                        if avmood1_2 <= 0:
                            idt1 = 'B'
                            short = 'Short'
                            Onumber = '03'  
                            MO.list_acc()
                            try:
                                Cquantity = MP.control1.ix[paper,'BroShare']
                                Cquantity = int(Cquantity)
				MPO.placeOrder(paper, exchange, idt1, Cquantity, short, Cnumber, Onumber, Citt)                         
                            except Exception as e:
                                print( 'cant find the control data!')
                                with open('Errorlog.txt','a') as f:
                                    print(time1,paper,'Control data read error!','Reason: ', e, file = f)               
                            
                    else:
                        (avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, today1)
                        if avmood1_2 <= 0:                    
                            idt1 = 'B'
                            short = 'short'
                            Onumber = '30' 
                            MO.list_acc()
                            try:
                                Cquantity = MP.control1.ix[paper,'BroShare']
                                Cquantity = int(Cquantity)
                                MPO.placeOrder(paper, exchange, idt1, Cquantity, short, Cnumber, Onumber, Citt)
                            except Exception as e:
                                print( 'cant find the control data!')
                                with open('Errorlog.txt','a') as f:
                                    print(time1,paper,'Control data read error!','Reason: ', e, file = f)   
                if avmood1[n2-2] > 0 and avmood1[n2-1]<=0 and Citt==0.0:
                    quantity = int(Camount/price3)
                    idt1 = 'S'
                    short = 'Short'
                    Onumber = '3'                
                    MPO.placeOrder(paper, exchange, idt1, quantity, short, Cnumber, Onumber, Citt) 

                if avmood1[n2-2] <= 0 and avmood1[n2-1]>0 and Citt==1.0:			
                    idt1 = 'B'
                    short = 'Short'
                    Onumber = '3' 
                    MO.list_acc()
                    try:
                        Cquantity = MP.control1.ix[paper,'BroShare']
                        Cquantity = int(Cquantity)
			MPO.placeOrder(paper, exchange, idt1, Cquantity, short, Cnumber, Onumber, Citt) 
                    except Exception as e:
                        print( 'cant find the control data!')
                        with open('Errorlog.txt','a') as f:
                            print(time1,paper,'Control data read error!','Reason: ', e, file = f)
            elif(Cmethod == 0 and rmax1 < rmax2): 
                if aadnp2[n2-2]>0 and aadnp2[n2-1]>0 and aaupn2[n2-1] == 0 and Citt==1:				

                    if MCP.checkPara(paper, today1) == 0:
                        (avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, lastday)
		        if aadnp2_1 == 0 or aaupn2_1 < 0:
                            idt1 = 'B'
                            short = 'Short'
                            Onumber = '04'  
                            MO.list_acc()
                            try:
                                Cquantity = MP.control1.ix[paper,'BroShare']
                                Cquantity = int(Cquantity)
                                MPO.placeOrder(paper, exchange, idt1, Cquantity, short, Cnumber, Onumber, Citt)
                            except Exception as e:
                                print( 'cant find the control data!')
                                with open('Errorlog.txt','a') as f:
                                    print(time1,paper,'Control data read error!','Reason: ', e, file = f)               
                    else:
			(avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, today1)
			if aadnp2_1 == 0 or aaupn2_1 < 0:
			    idt1 = 'B'
                            short = 'Short'
                            Onumber = '40'  
                            MO.list_acc()
                            try:
                                Cquantity = MP.control1.ix[paper,'BroShare']
                                Cquantity = int(Cquantity)
                                MPO.placeOrder(paper, exchange, idt1, Cquantity, short, Cnumber, Onumber, Citt) 
                            except Exception as e:
                                print( 'cant find the control data!')
                                with open('Errorlog.txt','a') as f:
                                    print(time1,paper,'Control data read error!','Reason: ', e, file = f)         
                if aadnp2[n2-2] == 0 and aadnp2[n2-1]>0 and aaupn2[n2-1] == 0 and Citt==1:
                    idt1 = 'B'
                    short = 'Short'
                    Onumber = '4'  
                    MO.list_acc()
                    try:
                        Cquantity = MP.control1.ix[paper,'BroShare']
                        Cquantity = int(Cquantity)
			MPO.placeOrder(paper, exchange, idt1, Cquantity, short, Cnumber, Onumber, Citt)
                    except Exception as e:
                        print( 'cant find the control data!')
                        with open('Errorlog.txt','a') as f:
                            print(time1,paper,'Control data read error!','Reason: ', e, file = f)               
                     
                if aadnp2[n2-1] == 0 and Citt==0.0:
                    if MCP.checkPara(paper, today1) == 0:
                        (avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, lastday)
			if aadnp2_1 > 0:
			    quantity = int(Camount/price3)
			    idt1 = 'S'
			    short = 'Short'
			    Onumber = '04'                
			    MPO.placeOrder(paper, exchange, idt1, quantity, short, Cnumber, Onumber, Citt) 
		    else:
		        (avmood1_2, avmood1_1, aadnp2_2, aadnp2_1, aaupn2_1) = MCP.checkPara(paper, today1)
			if aadnp2_1 > 0:
			    quantity = int(Camount/price3)
			    idt1 = 'S'
			    short = 'Short'
			    Onumber = '40'                
			    MPO.placeOrder(paper, exchange, idt1, quantity, short, Cnumber, Onumber, Citt)
    		
		
    file_name1 = 'TraRe'+str(today1)+'.txt'  
         
    fo = open(file_name1,'a')
    string1 =time1 + paper+':  '+ 'rmax1='+ str('{:4.2f}'.format(rmax1))+ 'rmax2='+ str('{:4.2f}'.format(rmax2))+ 'Citt='+str(Citt)
    string2 = 'avmood1[n2-2]=' +str('{:6.4f}'.format(avmood1[n2-2])) +' avmood1[n2-1]=' +str('{:6.4f}'.format(avmood1[n2-1]))
    string3 = 'aadnp2[n2-2]=' +str('{:6.4f}'.format(aadnp2[n2-2]))+'aadnp2[n2-1]=' +str('{:6.4f}'.format(aadnp2[n2-1]))+'aaupn2[n2-1]=' +str('{:6.4f}'.format(aaupn2[n2-1]))   
    fo.write(string1)
    fo.write(string2)
    fo.write(string3)
    fo.write('\n')

        
    fo.close()
    c.execute("INSERT INTO ParaRecord(PAPER,DAY,TIME,RMAX1,RMAX2,CITT,AVMOOD1_2,AVMOOD1_1, \
               AADNP2_2, AADNP2_1, AAUPN2_1) VALUES(?,?,?,?,?,?,?,?,?,?,?)", \
                    (paper,today1,time1, rmax1,rmax2,Citt,avmood1[n2-2], avmood1[n2-1], \
                    aadnp2[n2-2],aadnp2[n2-1],aaupn2[n2-1]))
    
    conn.commit()
    conn.close()
    
     
