from samplesclass import sample
from printcolor import printc
import pickle
import ROOT 
from ROOT import TFile, TTree
import ROOT
from array import array
from BetterConfigParser import BetterConfigParser
import sys

class HistoMaker:
    def __init__(self, path, config, optionsList,rescale=1,which_weightF='weightF'):
        self.path = path
        self.config = config
        self.optionsList = optionsList
        self.rescale = rescale
        self.which_weightF=which_weightF



    def getScale(self,job,subsample=-1):
        anaTag=self.config.get('Analysis','tag')
        input = TFile.Open(self.path+'/'+job.getpath())
        CountWithPU = input.Get("CountWithPU")
        CountWithPU2011B = input.Get("CountWithPU2011B")
        #print lumi*xsecs[i]/hist.GetBinContent(1)
        
        if subsample>-1:
            xsec=float(job.xsec[subsample])
            sf=float(job.sf[subsample])
        else:
            xsec=float(job.xsec)
            sf=float(job.sf)
        
        
        theScale = 1.
        if anaTag == '7TeV':
            theScale = float(job.lumi)*xsec*sf/(0.46502*CountWithPU.GetBinContent(1)+0.53498*CountWithPU2011B.GetBinContent(1))*self.rescale/float(job.split)
        elif anaTag == '8TeV':
            theScale = float(job.lumi)*xsec*sf/(CountWithPU.GetBinContent(1))*self.rescale/float(job.split)
        return theScale 


    def getHistoFromTree(self,job,subsample=-1):
        
        hTreeList=[]
        groupList=[]

        output=TFile.Open(self.path+'/tmp_%s.root'%job.name,'recreate')
        if job.type != 'DATA':
        
            if type(self.optionsList[0][7])==str:
                cutcut=self.config.get('Cuts',self.optionsList[0][7])
            elif type(self.optionsList[0][7])==list:
                cutcut=self.config.get('Cuts',self.optionsList[0][7][0])
                cutcut=cutcut.replace(self.optionsList[0][7][1],self.optionsList[0][7][2])
                print cutcut
            if subsample>-1:
                treeCut='%s & %s & EventForTraining == 0'%(cutcut,job.subcuts[subsample])        
            else:
                treeCut='%s & EventForTraining == 0'%(cutcut)

        elif job.type == 'DATA':
            cutcut=self.config.get('Cuts',self.optionsList[0][8])
            treeCut='%s'%(cutcut)
        input = TFile.Open(self.path+'/'+job.getpath(),'read')
        Tree = input.Get(job.tree)
        weightF=self.config.get('Weights',self.which_weightF)
        if job.type != 'DATA':
            #if Tree.GetEntries():
            output.cd()
            CuttedTree=Tree.CopyTree(treeCut)
        elif job.type == 'DATA':
        
            output.cd()
            CuttedTree=Tree.CopyTree(treeCut)

        for options in self.optionsList:

            if subsample>-1:
                name=job.subnames[subsample]
                group=job.group[subsample]
            else:
                name=job.name
                group=job.group


            treeVar=options[0]
            name=options[1]
            nBins=int(options[3])
            xMin=float(options[4])
            xMax=float(options[5])

            if job.type != 'DATA':
                if CuttedTree.GetEntries():
                    output.cd() 
                    CuttedTree.Draw('%s>>%s(%s,%s,%s)' %(treeVar,name,nBins,xMin,xMax), weightF, "goff,e")
                    full=True
                else:
                    full=False
            elif job.type == 'DATA':
            
                if options[11] == 'blind':
                    output.cd()
                    CuttedTree.Draw('%s>>%s(%s,%s,%s)' %(treeVar,name,nBins,xMin,xMax),treeVar+'<0', "goff,e")
                else:
                    output.cd()
                    CuttedTree.Draw('%s>>%s(%s,%s,%s)' %(treeVar,name,nBins,xMin,xMax),'1', "goff,e")
                full = True
            if full:
                hTree = ROOT.gDirectory.Get(name)
            else:
                output.cd()
                hTree = ROOT.TH1F('%s'%name,'%s'%name,nBins,xMin,xMax)
                hTree.Sumw2()

            if job.type != 'DATA':
                ScaleFactor = self.getScale(job,subsample)
                if ScaleFactor != 0:
                    hTree.Scale(ScaleFactor)
                    
            #print '\t-->import %s\t Integral: %s'%(job.name,hTree.Integral())
            hTree.SetDirectory(0)
            input.Close()
            hTreeList.append(hTree)
            groupList.append(group)
            
        return hTreeList, groupList
        

######################
def orderandadd(histos,typs,setup):
#ORDER AND ADD TOGETHER
    ordnung=[]
    ordnungtyp=[]
    num=[0]*len(setup)
    for i in range(0,len(setup)):
        for j in range(0,len(histos)):
            if typs[j] in setup[i]:
                num[i]+=1
                ordnung.append(histos[j])
                ordnungtyp.append(typs[j])
    del histos
    del typs
    histos=ordnung
    typs=ordnungtyp
    print typs
    for k in range(0,len(num)):
        for m in range(0,num[k]):
            if m > 0:
                #add
                histos[k].Add(histos[k+1],1)
                printc('magenta','','\t--> added %s to %s'%(typs[k],typs[k+1]))
                del histos[k+1]
                del typs[k+1]
    del histos[len(setup):]
    del typs[len(setup):]
    return histos, typs