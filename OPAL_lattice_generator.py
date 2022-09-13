___version___='v10.1.0'
"""
Opal lattice ger=nerator 
"""

import sys
import scipy.constants as C
from math import pi,sqrt,sin,cos,radians,degrees,fabs,exp,atan
import scipy.special as SP
import logging, pprint
from enum import IntEnum
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
import warnings
import time
import inspect
import lattice_parser2 as parser
import unittest
from ast import Del
from cProfile import label
from cmath import e
import math
import sys
from colorama import Fore, Style
import scipy.constants as C
from math import sqrt
import elements as ELM
import setutil as util
from lattice_generator import factory
from Ez0 import SFdata
from copy import copy
import pprint, inspect
import yaml
def PRINT_PRETTY(obj):
    file = inspect.stack()[0].filename
    print(F'DEBUG_ON[{file}] ==> ',end="")
    pprint.PrettyPrinter(width=200,compact=True).pprint(obj)
def PASS(obj):
    pass
DEB = dict(OFF=PASS,ON=PRINT_PRETTY)
DEBUG_ON  = DEB.get('ON')
DEBUG_OFF = DEB.get('OFF')

active_field_map = " "
output_base_dir = 'OPAL/generated/'

def call_INTRO(arg):
    file = arg['file']
    file.write("OPTION, PSDUMPFREQ      = 300    ; //  6d data written every 300 time steps (h5).\n")
    file.write("OPTION, STATDUMPFREQ    = 10     ;   // Beam Stats written every 10 time steps (stat).\n")
    file.write("OPTION, AUTOPHASE       = 4      ;        // Autophase is on, and phase of max energy\n")
    file.write("OPTION, VERSION         = 20400  ;  // This indicates that it works with an OPAL version of 2.3\n")
    file.write('Title, string="ALCELI"           ;\n')
    file.write("                          \n\n\n\n\n")

def call_INPUT(arg):
    UEM    = arg['m0c2']
    ATM    = 1.
    Q      = 1.
    ENEDEP = arg['tkIN']/1000  # tkIN [Mev]
    TOF    = 0.

    file = arg['file']
    
    file.write('REAL Edes    = {} ; \n'.format(ENEDEP))
    file.write('REAL gamma   = (Edes+PMASS)/PMASS;\n')    
    file.write('REAL beta    = sqrt(1-(1/gamma^2));\n')
    file.write('REAL P0      = gamma*beta*PMASS;\n')
    file.write('REAL gambet = gamma*beta;\n')

def call_Dist(arg):
    LAW    = 2
    ITWISS = 1
    FH     = arg['frequency']
    IMAX   = arg['nbparticles']
    ALPHAX = arg['alphax']
    BETAX  = arg['betax']
    EMITX  = arg['emitx']
    ALPHAY = arg['alphay']
    BETAY  = arg['betay']
    EMITY  = arg['emity']
    ALPHAZ = arg['alphaz']
    BETAZ  = arg['betaz']
    EMITZ  = arg['emitz']
    m0c2   = arg['m0c2']
    

    
    Spx=util.PARAMS['twiss_x_i'].sigmaV()/sqrt(5)*0.1224e-3
    Sx=util.PARAMS['twiss_x_i'].sigmaH()/sqrt(5)*.001
    Spy=util.PARAMS['twiss_y_i'].sigmaV()/sqrt(5)*0.1224e-3
    Sy=util.PARAMS['twiss_y_i'].sigmaH()/sqrt(5)*.001

  #  Sx      = 0.0007
#    Spx     = 0
  #  Sy      =0.0007
   # Spy     =0
   
    Sz      =0
    Spz     =0
   


    file = arg['file']
    file.write('Dist: DISTRIBUTION,\n')
    file.write('SIGMAX ={},  SIGMAPX = {},           \n'.format(Sx, Spx))
    file.write('SIGMAY ={},  SIGMAPY = {},           \n'.format(Sy, Spy))
    file.write('SIGMAZ ={},  SIGMAPZ = {},           \n'.format(Sz, Spz))
    file.write(' TYPE = GAUSS, INPUTMOUNITS = NONE   ;\n\n\n')

def call_FIELD(arg):
    """
    SF-field table on intervall -cavlen <= z <= +cavlen. 
    Field maximum is at z=0 and normalized to EzPeak Mv/m.   #TODO  z=0?
    """
    
    FH               = arg['freq']
    cavlength        = arg['gap']*100
    attenuation      = 1.
    EzPeak           = arg['EzPeak']
    cavlen_ha        =cavlength *.5   # (m) 1/2 cavity length
    cav_cnt          = arg['cav_cnt']
    sfdata           = arg['sfdata'] 
    
    sfdtable         = sfdata._Ez0_tab_scaled   # normed to EzPeak
    
    table_file_name  = f'OPALEzTab{cav_cnt}' 

    tmp = []
    for p in sfdtable:
        # if p.z < 0. or p.z > cavlen*1.e2: continue  # trimm 1/2-interval to 1/2-cavlen
        if abs(p.z) > (cavlen_ha + 1.e-4) * 1.e2: continue
        tmp.append(p)
    sfdtable         = tmp   
    z0               = sfdtable[0].z
    
    field = [[(p.z - z0)*1.e-2, p.Ez*1.e6] for p in sfdtable]  # z[m], EzPeak[V/m]

    with open(output_base_dir + table_file_name, 'w') as field_table:
        field_table.write('1DDynamic 40\n')
        field_table.write('{} {} {}\n'.format(0,cavlength,len(field)-1))
        field_table.write('{}\n'.format(FH))
        field_table.write('0.0 2.0 199\n')

        for p in field:
            field_table.write('{:10.4}\n'.format(p[1]))
    return table_file_name

def call_ELEMENTS(arg):
        print("\b--------------------------------------test_Lattice_Parser")
        input_file = arg['input_file']
        fileobject = open(input_file,'r')
        wfl = yaml.load(fileobject, Loader=yaml.FullLoader)
        fileobject.close()
        node_cnt, cav_cnt, quad_cnt = 0,0,0
        global active_field_map
        lm   = 0
        seg= wfl['ELEMENTS']
        g=[]
        for IID in seg:
            a  =seg[IID]
            if  a['type']=='D':
               Dr                = a['length']
               Eedg              = 0
               file              = arg['file']

               file.write('{} :     DRIFT,      L={}       ,ELEMEDGE={} ; \n'.format(IID,Dr, Eedg))

            elif a['type']=='QF':
                IID     = IID
                XL      = a['length']
                BQ      = a["B'"]
                RG      = a['aperture']
                Eedg    = 0
                file    = arg['file']

                file.write('{} :    Quadrupole, L={} ,K1={} ,ELEMEDGE={} ; \n'.format(IID,XL, BQ, Eedg))
                
            elif a['type']=='QD':
                IID=IID
                XL      = a['length']
                BQ      = -a["B'"]
                RG      = a['aperture']
                Eedg    =  0
                file    = arg['file']
                file.write('{}:     Quadrupole, L={} ,K1={} ,ELEMEDGE={} ; \n'.format(IID,XL, BQ, Eedg))
                
                
            elif a['type']=='RFG':
                
                IID=IID
                phiSoll     = a['PhiSync']
                freq        = arg['frequency']*1e-6
                gap         = a['gap']
                RG          = a['aperture']
                EzPeak      = a['EzPeak']
                sfdata      = SFdata(a['SFdata'],EzPeak,gap*100)
                
                cav_cnt     += 1 
                gap_dic=dict(
                   phiSoll       = phiSoll,
                   freq          = freq,
                   gap           = gap,  
                   EzPeak        = a['EzPeak'],
                   sfdata        = sfdata,
                   cav_cnt       = cav_cnt

                )

                
                Eedg    =  0
                node_cnt += 1
                cav_cnt += 1 
                
                name_E =call_FIELD(gap_dic)   
                
                file    = arg['file']
                file.write('{}:     RFCavity, L={} ,VOLT={} ,ELEMEDGE={} ,TYPE = "STANDING", FMAPFN = "{}",FREQ = {}, LAG = ({}*Pi)/180.0; \n'.format(IID,gap, EzPeak, Eedg,name_E,freq,phiSoll))
        file.write('\n\n\n')

                
      
    
def call_Beam(arg):
    LAW    = 2
    ITWISS = 1
    FH     = arg['frequency']
    IMAX   = arg['nbparticles']
    ALPHAX = arg['alphax']
    BETAX  = arg['betax']
    EMITX  = arg['emitx']
    ALPHAY = arg['alphay']
    BETAY  = arg['betay']
    EMITY  = arg['emity']
    ALPHAZ = arg['alphaz']
    BETAZ  = arg['betaz']
    EMITZ  = arg['emitz']
    m0c2   = arg['m0c2']
    
   
    file = arg['file']
    file.write('BEAM1: BEAM, PARTICLE = PROTON, pc = P0, NPART = 5000 ,\n')
    file.write('BFREQ ={},  BCURRENT = {},   CHARGE = 1;         \n\n\n'.format(FH*.000001, 100e-9))
    
    file.write('FS_SC:  Fieldsolver, FSTYPE = FFT,  MX = 16, MY = 16, MT = 16,PARFFTX = False,  PARFFTY = False, \n')
    file.write('PARFFTT = True,BCFFTX = open, BCFFTY = open,BCFFTT = open,BBOXINCR = 4,   GREENSF = INTEGRATED; \n\n\n')       
             
   




def call_ALCELI(arg):
    file = arg['file']
    m=int
    limits = [1., 5., 1., 5., 1., 1., 20., 1.]
    node_cnt, cav_cnt, quad_cnt = 0,0,0
    global active_field_map
    lm   = 0
    count=1
    length=0
    gap=cavlen=0
    for node in lattice.seq:
        
        if isinstance(node, (ELM.QF, ELM.QD,ELM.RFG,ELM.D)):
            lab=node.label
            element = util.ELEMENTS[node.label]
            DEBUG_OFF(element)

             
            if element['type'] == "DKD": 
                pass
            else:
            
                file.write('elmn{} : "{}" , ElEMEDGE={};\n'.format(count,lab,length))
                if isinstance(node, ELM.RFG):
                    m     = node.gap
                else:
                    m     = node.length
                count=count+1
                length=length+m
                gap=cavlen=0
            continue
        else:
            pass
        
    k    =1
    i    =1
    tap  =[]

    file.write('LEC: Line=(\n')
    for  node in lattice.seq:

        lab          = node.label
        element      = util.ELEMENTS[node.label]
        DEBUG_OFF(element)

             
        if element['type'] == "DKD": 
                pass
        else: 
            
            tap.append(i)
            i   = i+1
    for n in tap:
        if k   != i-1:
            file.write('elmn{},'.format(k)) 
            k   = k+1
    file.write('elmn{});\n\n\n\n'.format(k))   




def call_RUN(arg):
    leng=0
    for node in lattice.seq:
        
        leng=node.length+leng
    file = arg['file']
    file.write('TRACK, LINE = LEC, BEAM = BEAM1, MAXSTEPS = 19000, DT = 1.0e-11, ZSTOP={};   //  ZSTOP=beamlin lenght\n'.format(leng+1))
     
   
    file.write('RUN, METHOD = "PARALLEL-T", BEAM = BEAM1, FIELDSOLVER = FS_SC, DISTRIBUTION = Dist;\n')
    file.write('ENDTRACK;\n')   
    file.write('Quit;\n')          

    file.close()

if __name__ == '__main__':
    # lattice
    input_file="simuIN.yml"
    lattice = factory(input_file)
    util.waccept(lattice.first_gap)
    
    # Parameters: these are hardcoded to a specific value.
    particles           = 3000
    tof_time_adjustment = 0 
    attenuation_factor  = 1.0
    c                   = C.c
    pi                  = C.pi    
    m0c2                = C.value('proton mass energy equivalent in MeV')
  
    
   
    alphax    = util.PARAMS['alfax_i']
    betax     = util.PARAMS['betax_i']      #  
    emitx     = util.PARAMS['emitx_i']*1E06 # 
    alphay    = util.PARAMS['alfay_i']
    betay     = util.PARAMS['betay_i']
    
    emity     = util.PARAMS['emity_i']*1E06 # 
    emitw     = util.PARAMS['emitw']        # 
    tkIN      = util.PARAMS['injection_energy'] # MeV
    freq      = lattice.first_gap.freq
    conv      = util.WConverter(tkIN,freq)
    alphaz    = 0.
    # alphaz    = -0.21
    emitz     = 180.e3/pi*m0c2*emitw # deg*keV - 
   
    try:
        phi0 = math.degrees(conv.zToDphi(util.PARAMS['z0']))  # deg: z --> phase
        betaz = phi0 ** 2 / emitz  # deg/keV -
    except KeyError:
        betaz = 1.
 
    file = open(output_base_dir+"opALCELI.in", "w")
    

    OPAL_params = dict(
        file      = file,
        input_file= input_file,
        lattice   = lattice,
        frequency = freq,    #TODO comes from each node?
        alphax    = alphax,
        betax     = betax,
        emitx     = emitx,
        alphay    = alphay,
        betay     = betay,
        emity     = emity,
        alphaz    = alphaz,
        betaz     = betaz,
        emitz     = emitz,
        m0c2      = m0c2,
        tkIN      = tkIN,
        
        # dphase     = dphase,   #TODO comes from each node?
        nbparticles = particles,
       

      
    )
    
    call_INTRO(OPAL_params)
    call_INPUT(OPAL_params)
    call_ELEMENTS(OPAL_params)
    call_Dist(OPAL_params)
    
    
 

    call_ALCELI(OPAL_params)

    call_Beam(OPAL_params)
    
    call_RUN(OPAL_params)
    print('Reminder: '+Fore.RED+"You need a valid input-file for simu.py. Did you run simu.py first?")
    print(Style.RESET_ALL+'Generated new input files: '+file.name)
