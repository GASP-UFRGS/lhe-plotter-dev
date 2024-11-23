from __future__ import division
from subprocess import call
from math import *
from ROOT import TLorentzVector, TFile, TH1D, TH2D, TMath
from array import array
import numpy as np
import math
import sys

#import ROOT
#ROOT.EnableImplicitMT()
#ROOT.gDebug = 3

#import pdg

# https://pdgapi.lbl.gov/doc/pythonapi.html
#api = pdg.connect('sqlite:///pdg-2024-v0.1.3.sqlite')
#for item in api.get_all():
#  print('%-20s  %s' % (item.pdgid, item.description))
#sys.exit()

#####################################################################
# GGS (CERN-CMS/UFRGS) ---
# the muons are collected considering the ID codes in the event
# sample produced with SuperCHICv2 in LHE format.
#####################################################################

#####################################################################
# USER INPUT:

rootinput = np.loadtxt(sys.argv[1], unpack=True, dtype=str, delimiter='=')
rootinput = dict(zip(list(i.strip() for i in rootinput[0]), rootinput[1]))

# CROSS SECTION(S) (pb):
xsec    = eval(rootinput['xsec']) #FIXME

# PDF "_"+LABEL FOR OUTPUT FILES:
JOB     = eval(rootinput['JOB'])
PDF     = eval(rootinput['PDF']) #FIXME
scale   = eval(rootinput['scale']) #bug, use False, carefull with Nevts
cuts    = eval(rootinput['cuts'])
setLog  = eval(rootinput['setLog'])
filled  = eval(rootinput['filled'])
stacked = eval(rootinput['stacked'])
data    = eval(rootinput['data'])

# PARTICLES OF INTEREST
IDS     = eval(rootinput['IDS'])


# KINEMATICAL CUTS: #FIXME
INVMCUTUPPER   =eval(rootinput['INVMCUTUPPER'])
INVMCUTLOWER   =eval(rootinput['INVMCUTLOWER'])
                                
PTPAIRCUTUPPER =eval(rootinput['PTPAIRCUTUPPER'])
PTPAIRCUTLOWER =eval(rootinput['PTPAIRCUTLOWER'])
                                
ETACUT         =eval(rootinput['ETACUT'])
ETAPAIRCUT     =eval(rootinput['ETAPAIRCUT'])
INNER          =eval(rootinput['INNER'])
                                
PTCUTUPPER     =eval(rootinput['PTCUTUPPER'])
PTCUTLOWER     =eval(rootinput['PTCUTLOWER'])

PXICUTLOWER    =eval(rootinput['PXICUTLOWER'])
PXICUTUPPER    =eval(rootinput['PXICUTUPPER'])

# INPUT FILES:

#processo 3
FILES   = eval(rootinput['FILES'])#FIXME


# EVENT SAMPLE INPUT:
Nevt     = eval(rootinput['Nevt']) #FIXME
Nmax     = eval(rootinput['Nmax']) # number of max events to obtain from samples
EVTINPUT = str(int(Nevt/1000))+"k";
EBEAM1   = eval(rootinput['EBEAM1']) # in GeV
EBEAM2   = eval(rootinput['EBEAM2']) # in GeV
SQRTS    = eval(rootinput['SQRTS']) # in GeV

#####################################################################

# LABELS:
STRING	= "";
for m in range(len(PDF)):
	if (PDF[m]==PDF[-1]):
		STRING+=PDF[m]+"_";
	else:
		STRING+=PDF[m]+"-";

LABEL = JOB
if cuts: LABEL+="_CUTS"
if INNER: LABEL+='_INNER'
if scale: LABEL+="_SCALED"
if setLog: LABEL+="_LOG"
if filled: LABEL+="_FILLED"
if stacked: LABEL+="_STACKED"
if data: LABEL+="_DATA"

# IMAGE FORMATS TO BE CREATED:
FILE_TYPES = [LABEL+".png"];
print ("*****");
print ("Os arquivos gravados em %s" % (FILE_TYPES[0]));
print ("*****");
# SAVING HISTOS INTO ROOT FILE:
FILEROOT = TFile(LABEL+".root","RECREATE");

# CREATE INDIVIDUAL DIRS FOR IMAGE TYPES:
#print(len(FILE_TYPES))
for l in range(len(FILE_TYPES)):
	call(["mkdir","-p",FILE_TYPES[l]]);

#####################################################################

# ARRAYS FOR EACH TYPE OF DISTRIBUTIONS:
#
# 1D:
protpz       = []
proten       = []
protxi       = []
protpt       = []
proteta      = []
ivmprot      = []
mupz         = []
muen         = []
mupt         = []
ivmmu        = []
mueta        = []
phopz        = []
phopt        = []
phoen        = []
phoivm       = []
phopaireta   = []
phoeta       = []
phoY         = []
axen         = []
axpt         = []
axeta        = []
axphoM       = []
axphoPt      = []
axphoY       = []
nuen         = []
nupt         = []
nueta        = []
nuphoM       = []
nuphoPt      = []
nuphoY       = []
invphoM      = []
invphoPt     = []
invphoY      = []

# 2D:
DDivmprotmmumu   = []
DDxipximu        = []


# SORTING THE DISTRIBUTIONS WITHIN THE SETS:

# 1D
histoslog  = [protpz,proten,protxi,protpt,proteta,ivmprot,mupz,muen,mupt,ivmmu,mueta,phopz,phopt,phoen,phoivm,phoeta,phopaireta,phoY,axen,axpt,axeta,axphoM,axphoPt,nuen,nupt,nueta,nuphoM,nuphoPt]

# 2D
DDlog      = [DDivmprotmmumu,DDxipximu] 

#------------ Lists for KS test ----------------------

KS_ivm_pp = list([] for i in range(len(FILES)))
KS_ivm_mu = list([] for i in range(len(FILES)))
KS_protxi = list([] for i in range(len(FILES)))

#-----------------------------------------------------

def cutfilter(tlvs, mode, pid=0):
    if mode == 'CUTS-INNER':
        if pid != 2212:
#            print("-----OKOKOK5")
            if tlvs[1] != 0:
                if  ((tlvs[0]+tlvs[1]).M() >= INVMCUTLOWER
                and (tlvs[0]+tlvs[1]).M() <= INVMCUTUPPER
                and (tlvs[0]+tlvs[1]).Pt() >= PTPAIRCUTLOWER
                and (tlvs[0]+tlvs[1]).M() <= PTPAIRCUTUPPER
                #and abs((tlvs[0]+tlvs[1]).Eta()) <= ETAPAIRCUT # With this it doesn't work
                and tlvs[0].Pt() >= PTCUTLOWER
                and tlvs[1].Pt() <= PTCUTUPPER
                and abs(tlvs[0].Eta()) <= ETACUT
                and abs(tlvs[1].Eta()) <= ETACUT):
                    return True
                else:
                    return False
            else:
#                print("----OKOKOK7")
                if (tlvs[0].Pt() >= PTCUTLOWER
                and abs(tlvs[0].Eta()) <= ETACUT):
                    return True
                else:
                    return False
        else:
#            print(1-abs(tlvs[0].Pz())/EBEAM2)
            if tlvs[1] == 0:
                print(tlvs[0].Pz())
                print("-----OKOKOKum")
                print() 
                if  (1-abs(tlvs[0].Pz())/EBEAM2 >= PXICUTLOWER
                and  1-abs(tlvs[0].Pz())/EBEAM2 <= PXICUTUPPER):
                    return True
                else:
                    return False
            else:
                print(tlvs[0].Pz())
                print(tlvs[1].Pz())
                print("-----OKOKOKzero")
                if  (1-abs(tlvs[0].Pz())/EBEAM2 >= PXICUTLOWER
                and 1-abs(tlvs[0].Pz())/EBEAM2 <= PXICUTUPPER
                and 1-abs(tlvs[1].Pz())/EBEAM2 <= PXICUTLOWER
                and 1-abs(tlvs[1].Pz())/EBEAM2 >= PXICUTUPPER):
                    return True
                else:
                    return False
    if mode == 'CUTS':
        if pid != 2212:
            if  ((tlvs[0]+tlvs[1]).M() <= INVMCUTLOWER
            and (tlvs[0]+tlvs[1]).M() >= INVMCUTUPPER
            and (tlvs[0]+tlvs[1]).Pt() <= PTPAIRCUTLOWER
            and (tlvs[0]+tlvs[1]).M() >= PTPAIRCUTUPPER
            and abs((tlvs[0]+tlvs[1]).Eta()) >= ETAPAIRCUT
            and tlvs[0].Pt() <= PTCUTLOWER
            and tlvs[1].Pt() >= PTCUTUPPER
            and abs(tlvs[0].Eta()) >= ETACUT
            and abs(tlvs[1].Eta()) >= ETACUT):
                return True
            else:
                return False
        else:
            if  (1-abs(tlvs[0].Pz())/EBEAM2 <= PXICUTLOWER
            and 1-abs(tlvs[0].Pz())/EBEAM2 >= PXICUTUPPER
            and 1-abs(tlvs[1].Pz())/EBEAM2 <= PXICUTLOWER
            and 1-abs(tlvs[1].Pz())/EBEAM2 >= PXICUTUPPER):
                return True
            else:
                return False

def fill(tlvs, histoslog, DDlog, first, mode):
    ax = TLorentzVector(0,0,0,0)
    IDS = tlvs[1::2]

    has_axion = False
    twomuons = False
    neutrinopair = False
    twoproton = False
    singlephoton = True
    twophoton = False

    if first:
        # 1D
        # Proton
        protpz.append(TH1D("1D_"+mode+"_protpz"+"_"+PDF[i]       , "", 20,4000., 8000.))
        proten.append(TH1D("1D_"+mode+"_proten"+"_"+PDF[i]       , "", 50,0., 8000.))
        protxi.append(TH1D("1D_"+mode+"_protxi"+"_"+PDF[i]       , "", 15,0.0,1.0))
        protpt.append(TH1D("1D_"+mode+"_protpt"+"_"+PDF[i]       , "", 50,-0.1, 1.))
        proteta.append(TH1D("1D_"+mode+"_proteta"+"_"+PDF[i]       , "", 50,-20., 20.))
        ivmprot.append(TH1D("1D_"+mode+"_ivmprot"+"_"+PDF[i]       , "", 50,0., 14000.))
        # Muon
        mupz.append(TH1D("1D_"+mode+"_mupz"+"_"+PDF[i]       , "", 50,-2500.,2500.))
        muen.append(TH1D("1D_"+mode+"_muen"+"_"+PDF[i]       , "", 50,-100., 900.))
        mupt.append(TH1D("1D_"+mode+"_mupt"+"_"+PDF[i]       , "", 50,-5., 40.0))
        ivmmu.append(TH1D("1D_"+mode+"_ivmmu"+"_"+PDF[i]       , "", 50,0., 120.0))
        mueta.append(TH1D("1D_"+mode+"_mueta"+"_"+PDF[i]       , "", 50,-15., 15.))
        # Photon
        phopz.append(TH1D("1D_"+mode+"_phopz"+"_"+PDF[i]       , "", 50,-10., 2000.))
        phopt.append(TH1D("1D_"+mode+"_phopt"+"_"+PDF[i]       , "", 50,0., 5000.))
        phoen.append(TH1D("1D_"+mode+"_phoen"+"_"+PDF[i]       , "", 50,0., 5000.))
        phoivm.append(TH1D("1D_"+mode+"_phoivm"+"_"+PDF[i]     , "", 50, 0, 350))
        phoeta.append(TH1D('1D_'+mode+'_phoeta'+'_'+PDF[i] , '', 50, -10, 10))
        phopaireta.append(TH1D('1D_'+mode+'_phopaireta'+'_'+PDF[i] , '', 50, -10, 10))
        phoY.append(TH1D('1D_'+mode+'_phoY'+'_'+PDF[i]         , '', 50, -100, 100))
        # Monopole
        #mopz.append(TH1D("1D_"+mode+"_mupz"+"_"+PDF[i]       , "", 50,-2500.,2500.))
        #moen.append(TH1D("1D_"+mode+"_muen"+"_"+PDF[i]       , "", 50,-100., 900.))
        #mopt.append(TH1D("1D_"+mode+"_mupt"+"_"+PDF[i]       , "", 50,-5., 40.0))
        # Axion
        axeta.append(TH1D("1D_"+mode+"_axeta"+"_"+PDF[i]       , "", 50,-10., 10.))
        axen.append(TH1D("1D_"+mode+"_axen"+"_"+PDF[i]       , "", 50,0., 5000.))
        axpt.append(TH1D("1D_"+mode+"_axpt"+"_"+PDF[i]       , "", 50,0., 5000.))
        axphoM.append(TH1D("1D_"+mode+"_axphoM"+"_"+PDF[i]       , "", 50,0., 14000.))
        axphoPt.append(TH1D("1D_"+mode+"_axphoPt"+"_"+PDF[i]       , "", 50,0., 500.))
        axphoY.append(TH1D("1D_"+mode+"_axphoY"+"_"+PDF[i]       , "", 50,-2., 2.))

        # Neutrinos
        nueta.append(TH1D("1D_"+mode+"_nueta"+"_"+PDF[i]       , "", 50,-10., 10.))
        nuen.append(TH1D("1D_"+mode+"_nuen"+"_"+PDF[i]       , "", 50,0., 5000.))
        nupt.append(TH1D("1D_"+mode+"_nupt"+"_"+PDF[i]       , "", 50,0., 500.))
        nuphoM.append(TH1D("1D_"+mode+"_nuphoM"+"_"+PDF[i]       , "", 50,0., 1000.))
        nuphoPt.append(TH1D("1D_"+mode+"_nuphoPt"+"_"+PDF[i]       , "", 50,0., 500.))
        nuphoY.append(TH1D("1D_"+mode+"_nuphoY"+"_"+PDF[i]       , "", 50,-2., 2.))

        invphoM.append(TH1D("1D_"+mode+"_invphoM"+"_"+PDF[i]       , "", 50,0., 14000.))
        invphoPt.append(TH1D("1D_"+mode+"_invphoPt"+"_"+PDF[i]       , "", 50,0., 5000.))
        invphoY.append(TH1D("1D_"+mode+"_invphoY"+"_"+PDF[i]       , "", 50,-2., 2.))

        # 2D
        DDivmprotmmumu.append(TH2D('2D_'+mode+'_DDivmprotmmumu_'+PDF[i]       , '', 50, 0., 1400., 50, 0., 1400.))
        DDxipximu.append(TH2D('2D_'+mode+'_DDxipximu_'+PDF[i]     , '', 50, 0., 1., 50, 0., 1.))

    # 1D:
    #-------------------------Proton mesurements
    if 2212 in IDS:
        index = tlvs.index(2212)
        dpp = tlvs[index-1]
        tlvs.pop(index)
        tlvs.pop(index-1)
        dpm = 0
        if 2212 in tlvs:
            twoproton = True
            index = tlvs.index(2212)
            dpm = tlvs[index-1]
            tlvs.pop(index)
            tlvs.pop(index-1)
        if ((mode == 'CUTS' or mode == 'CUTS-INNER') and cutfilter([dpp, dpm], mode, 2212)) or mode == 'NO-CUTS':
            #print("--------OKOKOKOK3")
            #sys.exit()
            protpz[i].Fill(abs(dpp.Pz()))
            proten[i].Fill(dpp.E())
            proteta[i].Fill(dpp.Eta())
            protxi[i].Fill(1-(abs(dpp.Pz())/EBEAM2))
            protpt[i].Fill(dpp.Pt())
            if twoproton and copysign(1, dpp.Pz()) != copysign(1, dpm.Pz()):
                protpz[i].Fill(dpm.Pz())
                proten[i].Fill(dpm.E())
                protxi[i].Fill(1-(abs(dpm.Pz())/EBEAM2))
                ivmprot[i].Fill(sqrt((1-(abs(dpp.Pz())/EBEAM1))*(1-(abs(dpm.Pz())/EBEAM2)))*SQRTS)
                protpt[i].Fill(dpm.Pt())
                proteta[i].Fill(dpm.Eta())
    #-------------------------Múon mesurements
    if 13 in IDS or -13 in IDS:
        index = tlvs.index(13)
        dmu = tlvs[index-1]
        tlvs.pop(index)
        tlvs.pop(index-1)
        if "-13" in tlvs:
            twomuons = True
            index = tlvs.index(-13)
            damu = tlvs[index-1]
            tlvs.pop(index)
            tlvs.pop(index-1)
        if ((mode == 'CUTS' or mode == 'CUTS-INNER') and cutfilter([dmu, damu], mode)) or mode == 'NO-CUTS':
            mupz[i].Fill(dmu.Pz())
            muen[i].Fill(dmu.E())
            mupt[i].Fill(dmu.Pt())
            mueta[i].Fill(dmu.Eta())
            if twomuons:
                muen[i].Fill(damu.E())
                mupt[i].Fill(damu.Pt())
                ivmmu[i].Fill((dmu+damu).M())
                mueta[i].Fill(damu.Eta())
    #-------------------------Photon mesurements
    if 22 in IDS:
        index = tlvs.index(22)
        dp = tlvs[index-1]
        tlvs.pop(index)
        tlvs.pop(index-1)
        dm = 0
        if 22 in tlvs:
            singlephoton = False
            twophoton = True
            index = tlvs.index(22)
            dm = tlvs[index-1]
            tlvs.pop(index)
            tlvs.pop(index-1)
        if ((mode == 'CUTS' or mode == 'CUTS-INNER') and cutfilter([dp, dm], mode)) or mode == 'NO-CUTS':
            phopt[i].Fill(dp.Pt())
            phopz[i].Fill(dp.Pz())
            phoen[i].Fill(dp.E())
            phoeta[i].Fill(dp.Eta())
            phoY[i].Fill(dp.Y())
            if twophoton:
                phopz[i].Fill(dm.Pz())
                phoen[i].Fill(dm.E())
                phopt[i].Fill(dm.Pt())
                phoivm[i].Fill((dp+dm).M())
                phopaireta[i].Fill((dp+dm).Eta())
                phoeta[i].Fill(dm.Eta())               
                phoY[i].Fill(dm.Y())
    #-------------------------Monopole mesurements
    if 90 in IDS: # Monopole not coded to have cuts yet 
        index = tlvs.index(90)
        dmo = tlvs[index-1]
        tlvs.pop(index)
        tlvs.pop(index-1)
        mopz[i].Fill(dmo.Pz())
        moen[i].Fill(dmo.E())
        mopt[i].Fill(dmo.Pt())
    #-------------------------Neutrinos
    if 12 in IDS:
        index = tlvs.index(12)
        nup = tlvs[index-1]
        tlvs.pop(index)
        tlvs.pop(index-1)
        if -12 in tlvs:
            neutrinopair = True
            index = tlvs.index(-12)
            num = tlvs[index-1]
            tlvs.pop(index)
            tlvs.pop(index-1)
        if ((mode == 'CUTS' or mode == 'CUTS-INNER') and cutfilter([dp, dm], mode)) or mode == 'NO-CUTS':
            nueta[i].Fill(nup.Eta())
            nuen[i].Fill(nup.E())
            nupt[i].Fill(nup.Pt())
            if neutrinopair:
                nueta[i].Fill(num.Eta())
                nuen[i].Fill(num.E())
                nupt[i].Fill(num.Pt())

    #-------------------------Axion mesurements
    if 9000005 in IDS: # Monopole not coded to have cuts yet
        has_axion = True
        index = tlvs.index(9000005)
        ax = tlvs[index-1]
        tlvs.pop(index)
        tlvs.pop(index-1)
        axeta[i].Fill(ax.Eta())
        axen[i].Fill(ax.E())
        axpt[i].Fill(ax.Pt())
    #-------------------------Mesurements for the KS test
#    if 13 in IDS and -13 in IDS:
#        KS_ivm_pp[i].append(sqrt((1-(dpp.Pz()/(SQRTS/2)))*(1-(dpm.Pz()/(-(SQRTS/2)))))*SQRTS)
#        KS_protxi[i].append(1-(dpp.Pz()/(SQRTS/2)))
#        KS_protxi[i].append(1-(dpm.Pz()/(-(SQRTS/2))))
#        KS_ivm_mu[i].append((dmu+damu).M())
    # 2D:
    if twomuons and twoproton:
        if ((mode == 'CUTS' or mode == 'CUTS-INNER') and cutfilter([dpp, dpm], mode) and cutfilter([dmu, damu], mode)) or mode == 'NO-CUTS':
            DDivmprotmmumu[i].Fill(sqrt((1-(dpp.Pz()/(SQRTS/2)))*(1-(dpm.Pz()/(-(SQRTS//2)))))*SQRTS, (dmu+damu).M())
            DDxipximu[i].Fill(1-(dpp.Pz()/(SQRTS/2)), (1/SQRTS)*(dmu.Pt()*exp(dmu.Eta())+damu.Pt()*exp(damu.Eta())))
    if len(tlvs) == 0 and singlephoton and has_axion:
        axphoM[i].Fill((dp+ax).M())
        axphoPt[i].Fill((dp+ax).Pt())
        axphoY[i].Fill((dp+ax).Y())
        invphoM[i].Fill((dp+ax).M())
        invphoPt[i].Fill((dp+ax).Pt())
        invphoY[i].Fill((dp+ax).Y())
    if len(tlvs) == 0 and neutrinopair:
        nuphoM[i].Fill((dp+nup+num).M())
        nuphoPt[i].Fill((dp+nup+num).Pt())
        nuphoY[i].Fill((dp+nup+num).Y())
        invphoM[i].Fill((dp+ax).M())
        invphoPt[i].Fill((dp+ax).Pt())
        invphoY[i].Fill((dp+ax).Y())


# STARTING THE LOOP OVER FILES:
for i in range(len(FILES)):
    f = open(FILES[i],'r');
    print (f"Opening file {i}: {FILES[i]}");

    # SORTING THE DISTRIBUTIONS IN THE ARRAYS FOR EACH FILE:
    # EACH ARRAYS IS FORMATTED LIKE: array[] = [plots_file1, plots_file2, plots_file3, ...

    # LOOP OVER LINES IN LHE SAMPLE:

    # Flags for differentiating particles
    first_photon = False
    first_muon   = False
    first_proton = False

    # Flag to create histograms
    first = 1

    # RESET EVENT COUNTING:
    event  = 0;
    evPASS = 0;
    # START LOOP: <<<<<<<<<<<<<<<<!!! REMMEMBER TO COUNT CORRECTLY HERE
    if (i == 0):
        for j in range(344): # skip first 434 lines to avoid comments
            f.readline()
    elif (i == 1):
        for j in range(344): # skip first 431 lines to avoid comments
            f.readline()
    elif (i == 2):
        for j in range(7): # skip first 430 lines to avoid comments
            f.readline()
    elif (i == 3):
        for j in range(8): # skip first 440 lines to avoid comments
            f.readline();
    for line in f:
        # SKIP BLANK LINES:
        line = line.strip();
        if not line: continue;
        # STORE LINES INTO ARRAY:
        coll = line.split();
        # READ EVENT CONTENT:
        if coll[0] == "<event>":
            # CREATING LIST OF TLORETZVECTORS
            TLVS = []
            event += 1;
            # SET A SCREEN OUTPUT FOR CONTROL:
            if Nevt < 10000: evtsplit = 1000;
            else: evtsplit = 10000;
            perct = event / Nevt * 100.;
            if event%evtsplit==0: print ("Event %i [%.2f%%]" % (event,perct));
            elif event>Nevt: break;
        # 4-VECTORS FOR DECAY PRODUCTS:
        elif coll[0] == '22' and coll[1] == '1' and len(coll) > 6  and not first_photon:
            dp = TLorentzVector();
            px = float(coll[6]);
            py = float(coll[7]);
            pz = float(coll[8]);
            en = float(coll[9]);
            dp.SetPxPyPzE(px,py,pz,en)
            first_photon = True
            TLVS.append(dp)
            TLVS.append(22)
        elif coll[0] == '22' and coll[1] == '1' and first_photon:
            dm = TLorentzVector();
            px = float(coll[6]);
            py = float(coll[7]);
            pz = float(coll[8]);
            en = float(coll[9]);
            dm.SetPxPyPzE(px,py,pz,en);
            first_photon = False
            TLVS.append(dm)
            TLVS.append(22)
        elif coll[0] == '13' and coll[1] == '1' and len(coll) > 6 and first_muon == False:
            dmu = TLorentzVector();
            px = float(coll[6]);
            py = float(coll[7]);
            pz = float(coll[8]);
            en = float(coll[9]);
            dmu.SetPxPyPzE(px,py,pz,en);
            first_muon = True
            TLVS.append(dmu)
            TLVS.append(13)
        elif coll[0] == '-13' and coll[1] == '1' and first_muon:
            damu = TLorentzVector();
            px = float(coll[6]);
            py = float(coll[7]);
            pz = float(coll[8]);
            en = float(coll[9]);
            damu.SetPxPyPzE(px,py,pz,en);
            first_muon = False
            TLVS.append(damu)
            TLVS.append(-13)
        elif coll[0] == '90':
            dmo = TLorentzVector();
            px = float(coll[6]);
            py = float(coll[7]);
            pz = float(coll[8]);
            en = float(coll[9]);
            dmo.SetPxPyPzE(px,py,pz,en)
            TLVS.append(dmo)
            TLVS.append(90)
        elif coll[0] == '2212' and coll[1] == '1' and first_proton == False:
            dpp = TLorentzVector();
            px = float(coll[6]);
            py = float(coll[7]);
            pz = float(coll[8]);
            en = float(coll[9]);
            dpp.SetPxPyPzE(px,py,pz,en)
            first_proton = True
            TLVS.append(dpp)
            TLVS.append(2212)
        elif coll[0] == '2212' and coll[1] == '1' and first_proton:
            dpm = TLorentzVector();
            px = float(coll[6]);
            py = float(coll[7]);
            pz = float(coll[8]);
            en = float(coll[9]);
            dpm.SetPxPyPzE(px,py,pz,en)
            first_proton = False
            TLVS.append(dpm)
            TLVS.append(2212)
        elif coll[0] == '9000005' and coll[1] == '1':
            ax = TLorentzVector();
            px = float(coll[6]);
            py = float(coll[7]);
            pz = float(coll[8]);
            en = float(coll[9]);
            ax.SetPxPyPzE(px,py,pz,en)
            TLVS.append(ax)
            TLVS.append(9000005)
        elif coll[0] == '12' and coll[1] == '1' and len(coll)>6:
            nup = TLorentzVector();
            px = float(coll[6]);
            py = float(coll[7]);
            pz = float(coll[8]);
            en = float(coll[9]);
            nup.SetPxPyPzE(px,py,pz,en)
            TLVS.append(nup)
            TLVS.append(12)
        elif coll[0] == '-12' and coll[1] == '1':
            num = TLorentzVector();
            px = float(coll[6]);
            py = float(coll[7]);
            pz = float(coll[8]);
            en = float(coll[9]);
            num.SetPxPyPzE(px,py,pz,en)
            TLVS.append(num)
            TLVS.append(-12)
        #CLOSE EVENT AND FILL HISTOGRAMS:
        elif coll[0] == "</event>":
            # KINEMATICS OF DECAY PRODUCTS:
            if cuts and INNER:
                fill(TLVS, histoslog, DDlog, first, 'CUTS-INNER')
                first = 0

                evPASS += 1
            elif cuts and not INNER:
                fill(TLVS, histoslog, DDlog, first, 'CUTS')
                first = 0

                evPASS += 1;
            elif not cuts:
                fill(TLVS, histoslog, DDlog, first, 'NO-CUTS')
                first = 0

                evPASS += 1
        # End of loop over lines
        if evPASS >= Nmax: break   
    #print(phoivm[i].Integral())
    if cuts: print ("Events passing acceptance: %i/%i" % (evPASS,event));
        #print ("Integral of %s: %.6f nb" % (PDF[i],evPASS*xsec[i]/event));
# End of loop over files

#############################################################
#
#-----------------------KS TEST------------------------------
#
#############################################################

#with open(f'ks-test.txt', 'w') as f:
#    f.write('>>>>>>>KOLMOGOROV-SMIRNOV TEST<<<<<<<\n\n')
#    f.write(f'Invariant-Mass protons\n')
#    for i in range(4):
#        for j in range(i+1, 4):
#            ks = TMath.KolmogorovTest(len(KS_ivm_pp[i]), array('d', sorted(KS_ivm_pp[i])), len(KS_ivm_pp[j]), array('d', sorted(KS_ivm_pp[j])), 'D') 
#            f.write(f'{PDF[i]:>10} X {PDF[j]:<10}: {ks}\n')
#    f.write(f'\nInvariant-Mass leptons\n')
#    for i in range(4):
#        for j in range(i+1, 4):
#            ks = TMath.KolmogorovTest(len(KS_ivm_mu[i]), array('d', sorted(KS_ivm_mu[i])), len(KS_ivm_mu[j]), array('d', sorted(KS_ivm_mu[j])), 'D')
#            f.write(f'{PDF[i]:>10} X {PDF[j]:<10}: {ks}\n')
#    f.write(f'\n\u03A7 of protons\n')
#    for i in range(4):
#        for j in range(i+1, 4):
#            ks = TMath.KolmogorovTest(len(KS_protxi[i]), array('d', sorted(KS_protxi[i])), len(KS_protxi[j]), array('d', sorted(KS_protxi[j])), 'D')
#            f.write(f'{PDF[i]:>10} X {PDF[j]:<10}: {ks}\n')

#############################################################
#
#-----------------------END OF KS TEST-----------------------
#
#############################################################
FILEROOT.Write()

#####################################################################
#
# C'ESTI FINI
#
#####################################################################
