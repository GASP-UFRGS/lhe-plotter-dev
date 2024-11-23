from __future__ import division
from subprocess import call
import sys
from math import *
from ROOT import TLorentzVector, TFile, TH1D, TH2D, TCanvas, TGaxis, TLegend, TPaveText, gStyle, THStack, gPad, kTRUE
import numpy as np

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
LUMI    = eval(rootinput['LUMI'])
INNER   = eval(rootinput['INNER'])

# PARTICLES OF INTEREST
IDS     = eval(rootinput['IDS'])

# EVENT SAMPLE INPUT:
Nevt    = eval(rootinput['Nevt']) #FIXME
Nmax    = eval(rootinput['Nmax']) # number of max events to obtain from samples
EVTINPUT= str(int(Nevt/1000))+"k";
SQRTS   = eval(rootinput['SQRTS']) # in GeV
lumi    = float(rootinput['lumi'])

# LABELS:
LABEL = JOB
if cuts: LABEL+="_CUTS"
if INNER: LABEL+='_INNER'
if scale: LABEL+="_SCALED"
if setLog: LABEL+="_LOG"
if filled: LABEL+="_FILLED"
if stacked: LABEL+="_STACKED"
if data: LABEL+="_DATA"

# IMAGE FORMATS TO BE CREATED:
FILE_TYPES = ["png"];

# CREATE INDIVIDUAL DIRS FOR IMAGE TYPES:
for l in range(len(FILE_TYPES)):
	call(["mkdir","-p",LABEL+"-"+FILE_TYPES[l]]);

FILEROOT = TFile.Open(LABEL+".root", "READ")

keys = FILEROOT.GetListOfKeys()

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
DDxipximu    = []

# READING FROM ROOT FILE AND ALLOCATING DATA IN LISTS
for k in keys:
    name = k.GetName().split('_')[2]
    eval(name).append(k.ReadObj())

# THE ARRAYS STORE THE LABELS FOR AXIS AND UNITS:
# 1D
histoslog        = [protpz,proten,protxi,protpt,proteta,ivmprot,mupz,muen,mupt,ivmmu,mueta,phopz,phopt,phoen,phoivm,phoeta,phopaireta,phoY,axen,axpt,axeta,axphoM,axphoPt,axphoY,nuen,nupt,nueta,nuphoM,nuphoPt,nuphoY,invphoM,invphoPt,invphoY]
histoslog_label  = ["protpz","proten",'protxi','protpt','proteta','ivmprot',"mupz","muen","mupt",'ivm_mu','mueta','phopz','phopt','phoen','phoivm','phoeta','phopaireta','phoY','axen','axpt','axeta','axphoM','axphoPt','axphoY','nuen','nupt','nueta','nuphoM','nuphoPt','nuphoY','invphoM','invphoPt','invphoY']
histoslog_axis   = ["p_{z}(p)","E(p)",'#chi(p)','p_{T}(p)','#eta(p)','M(pp)',"p_{z}(#mu)","E(#mu)","p_{T}(#mu)",'M(#mu^{+}#mu^{-})','#eta(#mu^{+}#mu^{-})','p_{z}(#gamma)','p_{T}(#gamma)','E(#gamma)','M(#gamma#gamma)','#eta(#gamma)','#eta(#gamma#gamma)','Y(#gamma)','E(#tilde{a})','p_{T}(#tilde{a})','#eta(#tilde{a})','M(#gamma#tilde{a})','p_{T}(#gamma#tilde{a})','Y(#gamma#tilde{a})','E(#nu)','p_{T}(#nu)','#eta(#nu)','M(#gamma#nu#nu)','p_{T}(#gamma#nu#nu)','Y(#gamma#nu#nu)','M(#gamma + inv)','p_{T}(#gamma + inv)','Y(#gamma + inv)']
histoslog_varx   = ["(GeV)","(GeV)",'','(GeV)','','(GeV)',"(GeV)","(GeV)","(GeV)",'(GeV)','','(GeV)','(GeV)','(GeV)','(GeV)','','','','GeV','GeV','','GeV','GeV','','GeV','GeV','','GeV','GeV','','GeV','GeV','']

# 2D
DDlog         = [DDivmprotmmumu,DDxipximu] 
DDlog_label   = ["2Divmprotmmumu",'2Dxipximu'];
DDlog_xaxis   = ["M(p^{+}p^{-})",'#xi(p^{+})']
DDlog_yaxis   = ["M(#mu^{+}#mu^{-})",'#xi(#mu^{+}#mu^{-})']
DDlog_varx    = ["(GeV)",'']
DDlog_vary    = ["(GeV)",'']

# FETCHING NUMBER OF FILES
NUMFILES = len(histoslog[0])

# Starting Drawing step:

# SETTING THE NUMBER OF DIGITS ON AXIS
#TGaxis.SetMaxDigits(2)

# Defining the top label in the plots:
plotlabel = TPaveText(0.50,0.91,0.84,0.95,"NDC");
plotlabel.SetTextAlign(33);
plotlabel.SetTextColor(1);
plotlabel.SetFillColor(0);
plotlabel.SetBorderSize(0);
plotlabel.SetTextSize(0.035);
plotlabel.SetTextFont(42);
plotlabel.AddText("MadGraphv5 #bullet #sqrt{s}="+f'{SQRTS/(10**3):{".1f" if SQRTS < 10000 else ".0f"}}'+" TeV #bullet "+EVTINPUT+" evt");

# Legend:
leg = TLegend(0.55,0.72,0.75,0.87);
leg.SetTextSize(0.035);
leg.SetFillColorAlpha(0,0);
leg.SetBorderSize(0);

# Setting pads:
gStyle.SetOptStat(0);
gStyle.SetPadTickY(1);
gStyle.SetPadTickX(1);
gStyle.SetOptTitle(0);
gStyle.SetLegendBorderSize(0);

# Canvas
canvas = TCanvas("plots","Plots",0,0,700,860);

for i in range(len(histoslog)):
    globals()["hs_histoslog"+str(i)] = THStack("hs","");

# Starting loop over histograms in the arrays for each set:

# 1: 1D log-scaled plots:
canvas.SetLeftMargin(0.2);
canvas.SetBottomMargin(0.11);
canvas.SetRightMargin(0.18);
if setLog: gPad.SetLogy(1);
else: gPad.SetLogy(0);
legs=0;
for l in range(len(histoslog)):
    if 13 not in IDS and -13 not in IDS and 'mu' in histoslog_label[l]:
        continue
    if 2212 not in IDS and 'prot' in histoslog_label[l]:
        continue
    if 22 not in IDS and 'pho' in histoslog_label[l]:
        continue

    for m in range(NUMFILES):
            if LUMI:
                histoslog[l][m].Scale(xsec[m]/Nevt*lumi*histoslog[l][m].GetBinWidth(1))
            if scale:
                    histoslog[l][m].Scale(xsec[m]/Nevt*histoslog[l][m].GetBinWidth(1));
            histoslog[l][m].SetLineColor(m+1);
            if (m == 4): histoslog[l][m].SetLineColor(m+2);
            if filled:
                    histoslog[l][m].SetFillColor(m+1);
                    if (m == 4): histoslog[l][m].SetFillColor(m+2);
            histoslog[l][m].SetLineWidth(3);
            histoslog[l][m].SetLineStyle(1);
            globals()["hs_histoslog"+str(l)].Add(histoslog[l][m]);
            leg.AddEntry(histoslog[l][m]," "+PDF[m],"f");
            if data:
                if m == 0:
                        datapoints = histoslog[l][m].Clone();
                        dataonly = histoslog[l][m].Clone();
                else:
                        datapoints.Add(histoslog[l][m]);
                        dataonly.Add(histoslog[l][m]);
                        datapoints.SetFillStyle(0);
                        datapoints.SetLineWidth(0);
                        datapoints.SetLineStyle(0);
                        datapoints.SetMarkerStyle(20);
    if stacked:
            globals()["hs_histoslog"+str(l)].Draw("");
    else:
            globals()["hs_histoslog"+str(l)].Draw("nostack hist");
    if scale:
            globals()["hs_histoslog"+str(l)].GetYaxis().SetTitle("d#sigma/d"+str(histoslog_axis[l])+str(histoslog_varx[l])+" (pb)");
    else:
            globals()["hs_histoslog"+str(l)].GetYaxis().SetTitle("Events");
    if LUMI:
            globals()["hs_histoslog"+str(l)].GetYaxis().SetTitle("Yield")
    globals()["hs_histoslog"+str(l)].GetXaxis().SetTitle(str(histoslog_axis[l])+" "+str(histoslog_varx[l]));
    globals()["hs_histoslog"+str(l)].GetXaxis().SetTitleFont(42);
    globals()["hs_histoslog"+str(l)].GetYaxis().SetTitleFont(42);
    globals()["hs_histoslog"+str(l)].GetXaxis().SetTitleSize(0.05);
    globals()["hs_histoslog"+str(l)].GetYaxis().SetTitleSize(0.05);
    globals()["hs_histoslog"+str(l)].GetXaxis().SetLabelFont(42);
    globals()["hs_histoslog"+str(l)].GetYaxis().SetLabelFont(42);
    globals()["hs_histoslog"+str(l)].GetXaxis().SetTitleOffset(1.);
    globals()["hs_histoslog"+str(l)].GetYaxis().SetTitleOffset(1.6);
    globals()["hs_histoslog"+str(l)].GetXaxis().SetLabelSize(0.04);
    globals()["hs_histoslog"+str(l)].GetYaxis().SetLabelSize(0.04);
    globals()["hs_histoslog"+str(l)].GetXaxis().SetDecimals(True);
    globals()["hs_histoslog"+str(l)].GetXaxis().SetNdivisions(505, optim=kTRUE)
    if data:
            datapoints.Draw("E2,SAME");
            leg.AddEntry(datapoints,"data","p");
    leg.Draw("SAME");
    plotlabel.Draw("SAME");
    for k in range(len(FILE_TYPES)):
        canvas.Print(LABEL+"-"+FILE_TYPES[k]+"/"+JOB+"_"+EVTINPUT+"evt_"+histoslog_label[l]+"."+FILE_TYPES[k]);
    leg.Clear();
    if data:
        dataonly.SetLineStyle(2);
        dataonly.SetFillColor(0);
        dataonly.SaveAs(LABEL+"-"+FILE_TYPES[k]+"/"+JOB+"_"+EVTINPUT+"evt_"+histoslog_label[l]+".root");
# END loop over plots in log scale

# 2: 2D plot in log-scale:
canvas.SetLeftMargin(0.15);
canvas.SetBottomMargin(0.11);
canvas.SetRightMargin(0.23);
canvas.SetFrameFillColor(887);
gPad.SetLogy(0);
for l in range(len(DDlog)):
    if 13 not in IDS and -13 not in IDS and 2212 not in IDS or 'mu' in DDlog_label[l] or 'prot' in DDlog_label[l]:
        continue

    for m in range(NUMFILES):
        if (scale):
            DDlog[l][m].Scale(xsec[m]/Nevt*DDlog[l][m].GetXaxis().GetBinWidth(1));
            DDlog[l][m].Draw("COLZ");
            leg.AddEntry(DDlog[l][m]," "+PDF[m],"f");
        plotlabel.Draw("SAME");
        DDlog[l][m].Draw("COLZ")
        DDlog[l][m].GetXaxis().SetTitleOffset(1.);
        DDlog[l][m].GetYaxis().SetTitleOffset(1.2);
        DDlog[l][m].GetZaxis().SetTitleOffset(1.55);
        DDlog[l][m].GetXaxis().SetTitleFont(42);
        DDlog[l][m].GetYaxis().SetTitleFont(42);
        DDlog[l][m].GetXaxis().SetLabelFont(42);
        DDlog[l][m].GetYaxis().SetLabelFont(42);
        DDlog[l][m].GetXaxis().SetTitleSize(0.05);
        DDlog[l][m].GetYaxis().SetTitleSize(0.05);
        DDlog[l][m].GetZaxis().SetTitleSize(0.05);
        DDlog[l][m].GetXaxis().SetLabelSize(0.04);
        DDlog[l][m].GetYaxis().SetLabelSize(0.04);
        DDlog[l][m].GetZaxis().SetLabelSize(0.04);
        if (scale):
            DDlog[l][m].GetZaxis().SetTitle("d#sigma/d"+str(DDlog_xaxis[l])+"d"+str(DDlog_yaxis[l]));
        else:
            DDlog[l][m].GetZaxis().SetTitle("Events");
        DDlog[l][m].GetYaxis().SetTitle(DDlog_yaxis[l]+" "+DDlog_vary[l]+"");
        DDlog[l][m].GetXaxis().SetTitle(DDlog_xaxis[l]+" "+DDlog_varx[l]+"");
        DDlog[l][m].GetXaxis().SetDecimals(True);
        for k in range(len(FILE_TYPES)):
            canvas.Print(LABEL+"-"+FILE_TYPES[k]+"/"+JOB+"_"+EVTINPUT+"evt_"+DDlog_label[l]+'_'+PDF[m]+"."+FILE_TYPES[k]);
        leg.Clear();
# END loop over DDD Lego plots in log scale --

#####################################################################
#
# C'ESTI FINI
#
#####################################################################
