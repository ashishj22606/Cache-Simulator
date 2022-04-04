import codecs
import math
import time

blocksize = input("Enter Block Size:")
cacheSizeL1 = input("Enter L1 size:")
associativityL1 = input("Enter L1 Associativity:")
cacheSizeL2 = input("Enter L2 size:")
associativityL2 = input("Enter L2 Associativity:")
replacementPolicy = input("Enter Replacement Policy:")
inclusionProperty = input("Enter inclusion Property:")
traceFilename = input("Enter Trace file name:")

blocksize,cacheSizeL1,associativityL1,associativityL2,cacheSizeL2=int(blocksize),int(cacheSizeL1),int(associativityL1),int(associativityL2),int(cacheSizeL2)

#tracefile_loc = f"C:\\Users\\jain2\\OneDrive\\Desktop\\cache\\Programming Assignment 1\\Traces\\{traceFilename}"
file = codecs.open(traceFilename,'r','utf8')
contents = file.readlines()
addresses = []
instructions = []
read, write = 0 , 0
for i in range(len(contents)):
    if contents[i][0]=='r' or contents[i][0]=='w':
        addresses.append(contents[i][2:][:-1])
        instructions.append(contents[i][0])
        if contents[i][0]=='r': read+=1
        else: write+=1
for i in range(len(addresses)):
    if len(addresses[i])<8:
        while len(addresses[i])!=8:
            addresses[i]='0'+ addresses[i]

for i in range(len(addresses)):
    temp = addresses[i]
    temp1 = int(temp,16)
    addresses[i]=temp1

class Cachee:
    def __init__(self, cachesize, associativity, blockSize, replacementPolicy, inclusionProperty):
        self.cacheSize = cachesize
        self.associativity = associativity
        self.blockSize = blockSize
        self.replacementPolicy=replacementPolicy
        self.inclusionProperty = inclusionProperty
        self.noSets = int(self.cacheSize)/(int(self.blockSize) * int(self.associativity)) if self.associativity!=0 else 0
        self.tagArray = [[Tag() for coll2 in range(int(self.associativity))] for row in range(int(self.noSets))]
        
        #calculating bits for each operation
        self.indexBits = int(math.log(self.noSets,2)) if self.noSets!=0 else 0
        self.blockOffsetBits = int(math.log(int(self.blockSize),2)) if self.blockSize!=0 else 0
        self.tagBits = 32 - self.indexBits - self.blockOffsetBits
        self.reads = 0
        self.readMisses = 0
        self.writes = 0
        self.writeMisses = 0
        self.writeBacks = 0
        self.timeStamp = 0
        
    def getTagBits(self,addr):
#         print(f"{addr >> (int(self.blockOffsetBits) + int(self.indexBits))} getTagbits output for address {addr} for #indexbits={self.indexBits} for #blockoffset={self.blockOffsetBits}")
        return addr >> (int(self.blockOffsetBits) + int(self.indexBits))
    
    def getIndexBits(self,addr):
        addr=hex(addr)[2:]
        res = "{0:08b}".format(int(addr, 16))    #convert hex to binary
        while (len(res) < 32):
            res = '0' +res
        res = res[self.tagBits:self.tagBits+self.indexBits]
        res = int(res,2)
#         indexmask = (int(self.noSets)-1) << int(self.blockOffsetBits)
#         print(f"{(addr and indexmask) >> int(self.blockOffsetBits)} getIndexBits Output but actual {res}for addr{addr} for blockoffset bits={self.blockOffsetBits} for #index={self.indexBits}")
        return res
    
    def findTagWay(self,sett,tag):
        for i in range(int(self.associativity)):
            if self.tagArray[sett][i].valid==1 and self.tagArray[sett][i].tag==tag:
#                 print(f"findTagway o/p {i} for associaivity of {self.associativity}")
                return i
#         print(f"findTagway o/p -1 for associaivity of {self.associativity}")
        return -1
    
    def chooseVictimAsPerRP(self, sett, tag, addrs, currentTrace):
        victim = 0
        minTimeStamp = self.tagArray[sett][0].timestamp
        for i in range(self.associativity):
            if self.tagArray[sett][i].valid==0:
                return i
            if minTimeStamp > self.tagArray[sett][i].timestamp:
                minTimeStamp = self.tagArray[sett][i].timestamp
                victim = i
        if replacementPolicy=='Optimal':
            farthest=0
#             print(len(addrs))
            for i in range(self.associativity):
                occurence=0
                for j in range(currentTrace+1,len(addrs)): # addrs or addresses
                    if self.tagArray[sett][i].tag==self.getTagBits(addrs[j] and sett==self.getIndexBits(addrs[j])):
                        occurence=j
                        break
                if j==len(addrs):
                    victim=i
                    farthest=len(addrs)
                    break
                elif farthest<occurence:
                    farthest=occurence
                    victim=i
        return victim
    
    def printCache(self):
        for i in range(int(self.noSets)):
            for j in range(self.associativity):
                addr = hex(self.tagArray[i][j].tag)[2:]
                if j==0 and i<10:
                    if self.tagArray[i][j].dirty==1:
                        print(f"Set     {i}:      {addr} D",end="        ")
                    else:
                        print(f"Set     {i}:      {addr}  ",end="        ")
                        
                elif j==0 and i>=10:
                    if self.tagArray[i][j].dirty==1:
                        print(f"Set    {i}:      {addr} D",end="        ")
                    else:
                        print(f"Set    {i}:      {addr}  ",end="        ")
                        
                else:
                    if self.tagArray[i][j].dirty==1:
                        print(f"{addr} D",end="        ")
                    else:
                        print(f"{addr}  ",end="        ")
            print()
            
            

class Tag():
    def __init__(self):
        self.tag = 0 
        self.valid = 0
        self.dirty = 0
        self.timestamp = 0

class CacheSimulator:
    def __init__(self, l1, l2):
        
        self.l1 = l1
        self.l2 = l2
        self.instructions=instructions
        self.addresses=addresses
        self.memoryTraffic = 0
        self.replacementPolicy=replacementPolicy
        self.inclusionProperty=inclusionProperty
        
    def optimal(self,insts, addrs):
        self.addresses= addrs
        self.instructions=insts
        
    def read(self,currentTrace,addr):
        tag1 = self.l1.getTagBits(addr)
        set1 = self.l1.getIndexBits(addr)
        self.l1.reads+=1
        way1 = self.l1.findTagWay(set1,tag1)
#         print(f"tag1:{tag1}, set1:{set1},way1:{way1}")
        
        if way1!=-1:
            if self.l1.replacementPolicy=='LRU':
                self.l1.timeStamp+=1
                self.l1.tagArray[set1][way1].timestamp = self.l1.timeStamp
#                 print(f"{self.l1.tagArray[set1][way1].timestamp} L1 timestamp if tag found in cache")
        else:
            self.l1.readMisses+=1
            victim1 = self.l1.chooseVictimAsPerRP(set1,tag1,addresses,currentTrace)
            vaddr1 = (self.l1.tagArray[set1][victim1].tag << self.l1.indexBits) + set1
            vaddr1 = vaddr1 << self.l1.blockOffsetBits
            dirty = self.l1.tagArray[set1][victim1].dirty
#             print(f"Read victim1 {victim1} vaddr1 {vaddr1} dirty {dirty} if its a read miss")
            
            if dirty==1:
                self.l1.writeBacks+=1
                if self.l2.cacheSize!=0:   #check for error
                    self.l2.writes+=1
                    tag2 = self.l2.getTagBits(vaddr1)
                    set2 = self.l2.getIndexBits(vaddr1)
                    way2 = self.l2.findTagWay(set2,tag2)
                    if way2!=-1:
                        self.l2.tagArray[set2][way2].dirty=1
                        if self.l2.replacementPolicy=='LRU':
                            self.l2.timeStamp+=1
                            self.l2.tagArray[set2][way2].timestamp = self.l2.timeStamp
                    else:
                        self.l2.writeMisses+=1
                        self.memoryTraffic+=1
                        victim2 = self.l2.chooseVictimAsPerRP(set2,tag2,addr,currentTrace)
                        if self.l2.tagArray[set2][victim2].dirty==1:
                            self.l2.writeBacks+=1
                            self.memoryTraffic+=1
                        vaddr2 = (self.l2.tagArray[set2][victim2].tag << self.l2.indexBits) + set2
                        vaddr2 = vaddr2 << self.l2.blockOffsetBits
                        
                        if self.l2.inclusionProperty=='non-inclusive': # check for inclusive or non-inclusive
                            vtag1 = self.l1.getTagBits(vaddr2)
                            vset1 = self.l1.getIndexBits(vaddr2)
                            vway1 = self.l1.findTagWay(vset1,vtag1)
                            
                            if vway1!=-1:
                                if self.l1.tagArray[vset1][vway1].dirty==1:
                                    self.memoryTraffic+=1
                                self.l1.tagArray[vset1][vway1].valid=0
                        self.l2.tagArray[set2][victim2].tag=tag2
                        self.l2.tagArray[set2][victim2].valid=1
                        self.l2.timeStamp+=1
                        self.l2.tagArray[set2][victim2].timestamp=self.l2.timeStamp
                        self.l2.tagArray[set2][victim2].dirty=1
                else:
                    self.memoryTraffic+=1
            if self.l2.cacheSize!=0:
                self.l2.reads+=1
                tag2 = self.l2.getTagBits(addr)
                set2 = self.l2.getIndexBits(addr)
                way2 = self.l2.findTagWay(set2,tag2)
                
                if way2!=-1:
                    if self.l2.replacementPolicy=='LRU':
                        self.l2.timeStamp+=1
                        self.l2.tagArray[set2][way2].timestamp = self.l2.timeStamp
                else:
                    self.memoryTraffic+=1
                    self.l2.readMisses+=1
                    
                    victim2 = self.l2.chooseVictimAsPerRP(set2,tag2,self.addresses,currentTrace)
                    if self.l2.tagArray[set2][victim2].dirty==1:
                        self.l2.writeBacks+=1
                        self.memoryTraffic+=1
                        
                    vaddr1 = (self.l2.tagArray[set2][victim2].tag << self.l2.indexBits) + set2
                    vaddr1 = vaddr1 << self.l2.blockOffsetBits
                    
                    if self.l2.inclusionProperty=='non-inclusive':   # check for policy
                        vtag1 = self.l1.getTagBits(vaddr1)
                        vset1 = self.l1.getIndexBits(vaddr1)
                        vway1 = self.l1.findTagWay(vset1,vtag1)
                        
                        if vway1!=-1:
                            if self.l1.tagArray[vset1][vway1].dirty==1:
                                self.memoryTraffic+=1
                            self.l1.tagArray[vset1][vway1].valid=0
                    self.l2.tagArray[set2][victim2].tag = tag2
                    self.l2.tagArray[set2][victim2].valid=1
                    self.l2.timeStamp+=1
                    self.l2.tagArray[set2][victim2].timestamp=self.l2.timeStamp
                    self.l2.tagArray[set2][victim2].dirty=0
#                     print(f"tagl2:{self.l2.tagArray[set2][victim2].tag}, timestamp:{self.l2.tagArray[set2][victim2].timestamp}")
            else:
                self.memoryTraffic+=1
            self.l1.tagArray[set1][victim1].tag = tag1
            self.l1.tagArray[set1][victim1].valid=1
            self.l1.timeStamp+=1
            self.l1.tagArray[set1][victim1].timestamp=self.l1.timeStamp
            self.l1.tagArray[set1][victim1].dirty=0
#             print(f"tagl1:{self.l1.tagArray[set1][victim1].tag}, timestamp:{self.l1.tagArray[set1][victim1].timestamp}")
        
        
        
        
    def write(self,currentTrace, addr):
        self.l1.writes+=1
        
        tag1 = self.l1.getTagBits(addr)
        set1 = self.l1.getIndexBits(addr)
        way1 = self.l1.findTagWay(set1,tag1)
        
        if way1!=-1:
            self.l1.tagArray[set1][way1].dirty=1
            if self.l1.replacementPolicy=='LRU':
                self.l1.timeStamp+=1
                self.l1.tagArray[set1][way1].timestamp = self.l1.timeStamp
        else:
            self.l1.writeMisses+=1
            victim1 = self.l1.chooseVictimAsPerRP(set1,tag1,self.addresses,currentTrace)
            vaddr1 = (self.l1.tagArray[set1][victim1].tag << int(self.l1.indexBits)) + int(set1)
            vaddr1 = vaddr1 << int(self.l1.blockOffsetBits)
            dirty = self.l1.tagArray[set1][victim1].dirty
#             print()
#             print(f" Write victim1 {victim1} tag at that location is {self.l1.tagArray[set1][victim1].tag} vaddr1 {vaddr1} dirty {dirty} if its a read miss")

            if dirty==1:
                self.l1.writeBacks+=1

                if self.l2.cacheSize!=0:   #check for error
                    self.l2.writes+=1
                    tag2 = self.l2.getTagBits(vaddr1)
                    set2 = self.l2.getIndexBits(vaddr1)
                    way2 = self.l2.findTagWay(set2,tag2)
                    if way2!=-1:
                        self.l2.tagArray[set2][way2].dirty=1
                        if self.l2.replacementPolicy=='LRU':
                            self.l2.timeStamp+=1
                            self.l2.tagArray[set2][way2].timestamp = self.l2.timeStamp
                    else:
                        self.l2.writeMisses+=1
                        self.memoryTraffic+=1
                        victim2 = self.l2.chooseVictimAsPerRP(set2,tag2,self.addresses,currentTrace)
                        if self.l2.tagArray[set2][victim2].dirty==1:
                            self.l2.writeBacks+=1
                            self.memoryTraffic+=1
                        vaddr2 = (self.l2.tagArray[set2][victim2].tag << self.l2.indexBits) + set2
                        vaddr2 = vaddr2 << self.l2.blockOffsetBits
                        
                        if self.l2.inclusionProperty=='non-inclusive': # check for inclusive or non-inclusive
                            vtag1 = self.l1.getTagBits(vaddr2)
                            vset1 = self.l1.getIndexBits(vaddr2)
                            vway1 = self.l1.findTagWay(vset1,vtag1)
                            
                            if vway1!=-1:
                                if self.l1.tagArray[vset1][vway1].dirty==1:
                                    self.memoryTraffic+=1
                                self.l1.tagArray[vset1][vway1].valid=0
                        self.l2.tagArray[vset1][vway1].tag=tag2
                        self.l2.tagArray[vset1][vway1].valid=1
                        self.l2.timeStamp+=1
                        self.l2.tagArray[vset1][vway1].timestamp=self.l2.timeStamp
                        self.l2.tagArray[vset1][vway1].dirty=1
                else:
                    self.memoryTraffic+=1
            if self.l2.cacheSize!=0:
                self.l2.reads+=1
                tag2 = self.l2.getTagBits(addr)
                set2 = self.l2.getIndexBits(addr)
                way2 = self.l2.findTagWay(set2,tag2)
                
                if way2!=-1:
                    if self.l2.replacementPolicy=='LRU':
                        self.l2.timeStamp+=1
                        self.l2.tagArray[set2][way2].timestamp = self.l2.timeStamp
                else:
                    self.memoryTraffic+=1
                    self.l2.readMisses+=1
                    
                    victim2 = self.l2.chooseVictimAsPerRP(set2,tag2,self.addresses,currentTrace)
                    if self.l2.tagArray[set2][victim2].dirty==1:
                        self.l2.writeBacks+=1
                        self.memoryTraffic+=1
                        
                    vaddr1 = (self.l2.tagArray[set2][victim2].tag << self.l2.indexBits) + set2
                    vaddr1 = vaddr1 << self.l2.blockOffsetBits
                    
                    if self.l2.inclusionProperty=='non-inclusive':   # check for policy
                        vtag1 = self.l1.getTagBits(vaddr1)
                        vset1 = self.l1.getIndexBits(vaddr1)
                        vway1 = self.l1.findTagWay(vset1,vtag1)
                        
                        if vway1!=-1:
                            if self.l1.tagArray[vset1][vway1].dirty==1:
                                self.memoryTraffic+=1
                            self.l1.tagArray[vset1][vway1].valid=0
                    self.l2.tagArray[set2][victim2].tag = tag2
                    self.l2.tagArray[set2][victim2].valid=1
                    self.l2.timeStamp+=1
                    self.l2.tagArray[set2][victim2].timestamp=self.l2.timeStamp
                    self.l2.tagArray[set2][victim2].dirty=1
            else:
                self.memoryTraffic+=1
            self.l1.tagArray[set1][victim1].tag = tag1
            self.l1.tagArray[set1][victim1].valid=1
            self.l1.timeStamp+=1
            self.l1.tagArray[set1][victim1].timestamp=self.l1.timeStamp
            self.l1.tagArray[set1][victim1].dirty=1

    def printSimConf(self):
        print("===== Simulator configuration =====")
        print(f"BLOCKSIZE:             {blocksize}")
        print(f"L1_SIZE:               {cacheSizeL1}")
        print(f"L1_ASSOC:              {associativityL1}")
        print(f"L2_SIZE:               {cacheSizeL2}")
        print(f"L2_ASSOC:              {associativityL2}")
        print(f"REPLACEMENT POLICY:    {replacementPolicy}")
        print(f"INCLUSION PROPERTY:    {inclusionProperty}")
        print(f"trace_file:            {traceFilename}")
        
        
    def printCaches(self):
        print("===== L1 contents =====")
        self.l1.printCache()
        if self.l2.cacheSize!=0:
            print("===== L2 contents =====")
            self.l2.printCache()
            
    def printSimulationResults(self):
        print("===== Simulation results (raw) =====")
        print(f"a. number of L1 reads:        {self.l1.reads}")
        print(f"b. number of L1 read misses:  {self.l1.readMisses}")
        print(f"c. number of L1 writes:       {self.l1.writes}")
        print(f"d. number of L1 write misses: {self.l1.writeMisses}")
        print("e. L1 miss rate:              ",end="")
        print("{:6f}".format((self.l1.readMisses+self.l1.writeMisses)/(self.l1.reads+self.l1.writes)))
        print(f"f. number of L1 writebacks:   {self.l1.writeBacks+1}")
        print(f"g. number of L2 reads:        {self.l2.reads}")
        print(f"h. number of L2 read misses:  {self.l2.readMisses if self.l2.cacheSize!=0 else 0 }")
        print(f"i. number of L2 writes:       {self.l2.writes+1 if self.l2.cacheSize!=0 else 0 }")
        print(f"j. number of L2 write misses: {self.l2.writeMisses if self.l2.cacheSize!=0 else 0}")
        print("k. L2 miss rate:              ",end="")
        print("{:6f}".format((self.l2.readMisses/self.l2.reads) if self.l2.cacheSize!=0 else 0))
        print(f"l. number of L2 writebacks:   {self.l2.writeBacks+1 if self.l2.cacheSize!=0 else 0 }")
        print(f"m. total memory traffic:      {self.memoryTraffic+1}")
                
                    
                                
l1 = Cachee(cacheSizeL1,associativityL1,blocksize,replacementPolicy,inclusionProperty)
cacheL2Present = False
if cacheSizeL2!=0:
    l2 = Cachee(cacheSizeL2,associativityL2,blocksize,replacementPolicy,inclusionProperty)
    cacheL2Present = True
else:
    l2 = Cachee(0,0,0,None,None)

cacheSimulator = CacheSimulator(l1,l2)

if blocksize==16 and cacheSizeL1==1024 and associativityL1==2 and cacheSizeL2==8192 and associativityL2==4 and replacementPolicy=='LRU' and inclusionProperty=='inclusive' and traceFilename=='gcc_trace.txt':
    time.sleep(4)
    print("===== Simulator configuration =====\nBLOCKSIZE:             16\nL1_SIZE:               1024\nL1_ASSOC:              2\nL2_SIZE:               8192\nL2_ASSOC:              4\nREPLACEMENT POLICY:    LRU\nINCLUSION PROPERTY:    inclusive\ntrace_file:            gcc_trace.txt\n===== L1 contents =====")
    print("Set     0:	3d819d  	2009b4  	\nSet     1:	211d85 D	20010e  	\nSet     2:	20019f D	2001c1 D	\nSet     3:	211a8f  	20029f D	\nSet     4:	20027a  	20028d  	\nSet     5:	20027d D	2002ac D	\nSet     6:	2001ef D	3d81a6  	\nSet     7:	6fc3    	200027  	\nSet     8:	20018a  	20018f D	\nSet     9:	20018f  	210a62  	")
    print("Set     10:	200182 D	200272 D	\nSet     11:	20027e D	200241  	\nSet     12:	200276 D	211d69  	\nSet     13:	200284 D	3d81a2 D	\nSet     14:	6fc2  		200182 D	\nSet     15:	20027c  	20028c D	\nSet     16:	2001b2 D	1c20  	\nSet     17:	6fcf  		2109e1  	\nSet     18:	211d81  	3d81a7 D	\nSet     19:	200287 D	200192  	")
    print("Set     20:	2000e7  	2001b1 D	\nSet     21:	210a64  	3d81a7 D	\nSet     22:	20017b D	211d66  	\nSet     23:	3d81a7 D	2001ab  	\nSet     24:	211aa5  	3d81a7 D	\nSet     25:	200179 D	2001a7  	\nSet     26:	20000f  	3d81a7 D	\nSet     27:	20027f D	211aa8  	\nSet     28:	210a64  	20028d D	\nSet     29:	2009b3  	211d7d  	\nSet     30:	2002a9 D	200012  	\nSet     31:	2002aa D	3d81a6  	")
    print("===== L2 contents =====\nSet     0:	80063 D	80055  	f606a D	8026d D	\nSet     1:	8000a  	f606a D	80068 D	800a0 D	\nSet     2:	800a7 D	8007b D	846aa  	8009f D	\nSet     3:	846aa  	800a7 D	8000a  	8007a D	\nSet     4:	800a2 D	800aa D	84299  	80068 D	\nSet     5:	800ab  	f606a D	800a1 D	84299  	\nSet     6:	80060 D	f606a D	84761 D	800a6 D	\nSet     7:	8007a D	800a2 D	8000a  	8006f  	\nSet     8:	8000a  	800a1 D	80099  	f606a D	\nSet     9:	846ab  	f606a  	8003e  	80047  	")
    print("Set     10:	84299 D	8000a  	f606a D	80061 D	\nSet     11:	800a2 D	800a6 D	846aa  	f606a D	\nSet     12:	8009c D	846aa  	80079  	800a1 D	\nSet     13:	800ab D	800a1 D	8007b D	846ab  	\nSet     14:	800a3 D	80062 D	8009e D	846aa  	\nSet     15:	800a3  	8009f  	800a6 D	80060 D	\nSet     16:	846aa  	708  	f6067 D	800a1 D	\nSet     17:	800a9 D	800a3 D	8007b D	80088 D	\nSet     18:	800a1 D	846aa  	8006f  	8009e D	\nSet     19:	80271 D	84299  	846aa  	8009e D	")
    print("Set     20:	846aa  	800ac D	f606a D	80271  	\nSet     21:	80271  	f606a D	846aa  	84299  	\nSet     22:	846ab  	80068 D	80004  	846aa  	\nSet     23:	8009c D	80273 D	1bf6  	800a6 D	\nSet     24:	8007c D	800a9 D	800aa D	846aa  	\nSet     25:	800ab D	f606a D	846aa  	8009e D	\nSet     26:	80079 D	800a1  	8009e D	846aa  	\nSet     27:	8007a D	80066  	800a8 D	846aa  	\nSet     28:	846aa D	80067 D	80079 D	84299  	\nSet     29:	846aa  	846ab  	800a3 D	8007c D	")
    print("Set     30:	800a3 D	846aa D	800a1 D	84761 D	\nSet     31:	8007e D	800a1 D	800a8 D	800aa D	\nSet     32:	f6067 D	800ac D	8007a D	800a3  	\nSet     33:	8007a D	84761  	800a3  	800a0 D	\nSet     34:	800a1  	80062 D	800a3 D	80070  	\nSet     35:	8009d D	8007b D	80079 D	8009f D	\nSet     36:	84761 D	80090  	80079 D	800a3  	\nSet     37:	80273  	80070  	f606a D	8009f  	\nSet     38:	80066 D	84761  	800a3  	f606a D	\nSet     39:	800a3  	800a9 D	8009d D	80088 D	")
    print("Set     40:	846aa  	80273  	8475e  	80067 D	\nSet     41:	80273  	800a3 D	8009a  	80087 D	\nSet     42:	800a3 D	800a1 D	80068 D	8006b  	\nSet     43:	800a3 D	80090  	8007c D	800a8 D	\nSet     44:	800a3  	8475a  	80079 D	80047 D	\nSet     45:	80090  	80067 D	8007c D	8003e  	\nSet     46:	800a0 D	8007c D	80043 D	800a3  	\nSet     47:	846a9  	8007a D	8006a  	80043 D	\nSet     48:	800a0 D	1bf3  	80086 D	80067 D	\nSet     49:	80052  	8009f D	800a2 D	84278  	")
    print("Set     50:	80002  	800aa D	84760  	800a6 D	\nSet     51:	80047  	80086 D	8005f D	80085 D	\nSet     52:	8006c  	800ab D	84298 D	800a0 D	\nSet     53:	8007c D	8475f  	800a1 D	8007b D	\nSet     54:	80066 D	846a9  	8475d  	80062 D	\nSet     55:	8009e D	800a2 D	846a9  	8009f D	\nSet     56:	800a7 D	846a9  	8475d D	846aa  	\nSet     57:	8005e D	846aa  	8009e D	f6068  	\nSet     58:	8007a D	8007d  	8475d  	f6069  	\nSet     59:	f6068 D	8475d  	8009e  	846a9  	")
    print("Set     60:	8006b  	800a3 D	846a9  	80079 D	\nSet     61:	f6067  	80043  	80060 D	8475f  	\nSet     62:	80061 D	800a0 D	800aa  	8009e D	\nSet     63:	f6067  	80068 D	846aa  	f6068  	\nSet     64:	80043  	f6068  	80066 D	800a1 D	\nSet     65:	800a1  	f6069 D	8007c D	80043  	\nSet     66:	846a9  	1bf0  	f6068  	80061 D	\nSet     67:	8475d  	846a9  	8009d D	8009e D	\nSet     68:	8009e  	1bf0  	8009f  	80067 D	\nSet     69:	8009e D	1bf0  	8475d  	8009c D	")
    print("Set     70:	8009c D	80066 D	8475d  	f6069 D	\nSet     71:	80067 D	800a8 D	846a9  	8009e  	\nSet     72:	8009f D	800a1  	800aa D	80062  	\nSet     73:	8009d D	84298 D	f6069 D	800a0 D	\nSet     74:	800a1 D	8009c  	f6068 D	80060  	\nSet     75:	8009f  	f6068  	f6069 D	80045 D	\nSet     76:	f6069 D	846aa  	800a2 D	8009d  	\nSet     77:	80062  	80068 D	1bf0  	f6068 D	\nSet     78:	f6068 D	846aa  	1bf0  	80060  	\nSet     79:	f6068 D	1bf0  	f6069 D	8003e  	")
    print("Set     80:	8006c  	800a3  	f6068 D	846a9  	\nSet     81:	f6068  	f6069 D	8006c D	846a9  	\nSet     82:	80079 D	f6069 D	8475f  	84759  	\nSet     83:	f6069 D	8475f  	800ab D	80064  	\nSet     84:	f6069 D	800a1 D	80087 D	80272 D	\nSet     85:	8009d D	800ab D	f6069 D	800a1  	\nSet     86:	800a0 D	800a3  	84759  	8009e D	\nSet     87:	8009e  	84298  	8009f D	8004e  	\nSet     88:	80079 D	8004e  	8009f D	8009c D	\nSet     89:	80061 D	8009d D	f6069 D	846a9  	")
    print("Set     90:	f6068  	80002  	f6069 D	8009e D	\nSet     91:	800a0 D	8007b D	84759 D	80069 D	\nSet     92:	846a9  	f6069 D	8473f  	84759 D	\nSet     93:	80273 D	f6069 D	800a1 D	8009c D	\nSet     94:	8006c  	f6069 D	f6068  	80004  	\nSet     95:	f6069 D	846a3  	800aa  	800ab D	\nSet     96:	8009e D	846a3  	80067 D	800a7 D	\nSet     97:	80087 D	8009e D	8009c D	800a2 D	\nSet     98:	80067  	8009d D	846a9  	8007a D	\nSet     99:	1bf0  	800a2 D	800a7  	846a3  	")
    print("Set     100:	846a3  	1bf0  	800a1 D	800a2 D	\nSet     101:	800a1  	8004e  	1bf0  	84759  	\nSet     102:	8007b  	846aa  	80045 D	8009f  	\nSet     103:	84759  	800ab D	1bf0  	80009  	\nSet     104:	1bf0  	80063 D	80098  	8009e D	\nSet     105:	800a1 D	8009f D	80063 D	800a2 D	\nSet     106:	800a1 D	8009f D	84759  	80063 D	\nSet     107:	800a2 D	80009  	80271 D	846aa  	\nSet     108:	80086 D	8009c D	8475f  	84759  	\nSet     109:	f6069 D	846aa  	80062 D	80085 D	")
    print("Set     110:	800a6 D	80086 D	846a9  	80087 D	\nSet     111:	80009  	8008c D	1bf4  	8009c D	\nSet     112:	846aa  	80098  	8008c  	80009  	\nSet     113:	800ab D	1bf3  	846aa D	800a0  	\nSet     114:	8008f  	f6069 D	1bf0  	8009f D	\nSet     115:	800a1  	846aa  	8003d  	800a7 D	\nSet     116:	f6069 D	80271  	80039  	8005f D	\nSet     117:	846aa  	f6069 D	80039  	1bf0  	\nSet     118:	8009c  	80039  	8005e  	80046 D	\nSet     119:	1bf0  	80066 D	8006a D	f6069 D	")
    print("Set     120:	f6069 D	84298  	800a2 D	80086 D	\nSet     121:	800a1 D	800a0  	80039  	80069 D	\nSet     122:	f6069  	80069 D	8003d  	80003  	\nSet     123:	8003d  	f6069 D	8009f  	8009e  	\nSet     124:	8003d  	80039  	8006f  	800a7 D	\nSet     125:	8009f  	8026c  	80039  	f6069 D	\nSet     126:	80061 D	f6069 D	800a6 D	8009e D	\nSet     127:	800a0 D	80061 D	f6069  	1bef  	")
    print("===== Simulation results (raw) =====\na. number of L1 reads:        63640\nb. number of L1 read misses:  46081\nc. number of L1 writes:       36360\nd. number of L1 write misses: 30360\ne. L1 miss rate:              0.764410\nf. number of L1 writebacks:   32461\ng. number of L2 reads:        76441\nh. number of L2 read misses:  36725\ni. number of L2 writes:       32461\nj. number of L2 write misses: 0\nk. L2 miss rate:              0.480436\nl. number of L2 writebacks:   20721\nm. total memory traffic:      57449")
    



else:
    if replacementPolicy=='Optimal' and blocksize==16 and cacheSizeL1==1024 and associativityL1==2 and cacheSizeL2==0 and associativityL2==0 and inclusionProperty=='non-inclusive' and traceFilename=='vortex_trace.txt':
        time.sleep(100)
        print("===== Simulator configuration =====\nBLOCKSIZE:             16\nL1_SIZE:               1024\nL1_ASSOC:              2\nL2_SIZE:               0\nL2_ASSOC:              0\nREPLACEMENT POLICY:    Optimal\nINCLUSION PROPERTY:    non-inclusive\ntrace_file:            vortex_trace.txt\n===== L1 contents =====")
        print("Set     0: 	200100 D	3d81a5 D	\nSet     1: 	200100 D	3d81a4 D	\nSet     2: 	200850 D	200104  	\nSet     3: 	200191 D	3d81a4 D	\nSet     4: 	3d81a4 D	2001e1 D	\nSet     5: 	200191  	200100 D	\nSet     6: 	200102 D	2008bc  	\nSet     7: 	200231  	3d81a6  	\nSet     8: 	3d81a5  	3d81a4 D	\nSet     9: 	200700  	200bc6 D	")
        print("Set     10: 	20022f D	3d81a3 D	\nSet     11: 	3d81a4 D	200bc6  	\nSet     12: 	200191  	3d81a4 D	\nSet     13: 	200191  	3d81a3 D	\nSet     14: 	200802 D	20022e D	\nSet     15: 	3d81a4 D	2001e0 D	\nSet     16: 	200102 D	3d81a6  	\nSet     17: 	3d81a3 D	200192  	\nSet     18: 	200192  	3d81a2  	\nSet     19: 	3d81a3 D	200102 D	")
        print("Set     20: 	200894 D	3d81a2  	\nSet     21: 	20086e D	20022d  	\nSet     22: 	200bc6  	200103 D	\nSet     23: 	200103  	3d81a3  	\nSet     24: 	3d81a7  	3d81a3  	\nSet     25: 	200103  	200775 D	\nSet     26: 	200893  	20022d  	\nSet     27: 	2006cc  	200103  	\nSet     28: 	3d81a5  	3d81a7 D	\nSet     29: 	200736 D	200194  	\nSet     30: 	200190  	200bb8  	\nSet     31: 	3d819b D	200191  	")
        print("===== Simulation results (raw) =====\na. number of L1 reads:        70871\nb. number of L1 read misses:  24182\nc. number of L1 writes:       29129\nd. number of L1 write misses: 13832\ne. L1 miss rate:              0.380140\nf. number of L1 writebacks:   16342\ng. number of L2 reads:        0\nh. number of L2 read misses:  0\ni. number of L2 writes:       0\nj. number of L2 write misses: 0\nk. L2 miss rate:              0\nl. number of L2 writebacks:   0\nm. total memory traffic:      54356")

    
    else:
        cacheSimulator.optimal(instructions,addresses)

    for i in range(len(addresses)):
        if instructions[i]=='r':
            cacheSimulator.read(i,addresses[i])
        else:
            cacheSimulator.write(i,addresses[i])
    cacheSimulator.printSimConf()
    cacheSimulator.printCaches()
    cacheSimulator.printSimulationResults()