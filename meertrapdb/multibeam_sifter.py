import sys
import numpy as np
import argparse


parser = argparse.ArgumentParser(description='Multibeam candidate sorting code.')
parser.add_argument('file',type=str,nargs=1)
parser.add_argument('-dm',type=float,nargs=1,default=[0.02],help='Fractional DM tolerance. Default: 0.02')
parser.add_argument('-mjd',type=int,nargs=1,default=[7],help='MJD is rounded off after this many decimals. Default: 7')
options= parser.parse_args()

ndtype=[('a',int),('b',float),('c',float),('d',float),('e',float),('f',int),('g','S12'),('h','S12'),('i','S23'),('j','object')]
names = ["N", "MJD", "DM", "WIDTH", "SNR", "BEAM", "RAJ", "DECJ", "FILFILE", "JPEG"]
cand_file = open(options.file[0])
candidates = np.genfromtxt(cand_file, names=names, dtype=ndtype)

candidates['MJD'] = np.around(candidates['MJD'], decimals=options.mjd[0])
candidates_sorted = np.sort(candidates, order=['MJD', 'DM', 'SNR'])
unique_cands=[]
cand_iter = np.nditer(candidates_sorted, flags=['f_index','refs_ok'], order='C')
match_line = candidates_sorted[0]
num_matches=[]
match_cnt=-1

while not cand_iter.finished:
    '''Iterate first to match the first line'''
    if (candidates_sorted[cand_iter.index][1] == match_line[1]) and ((candidates_sorted[cand_iter.index][2] - match_line[2]) / candidates_sorted[cand_iter.index][2] < options.dm[0]):
        match_cnt+=1
        if (candidates_sorted[cand_iter.index][4] > match_line[4]):
            match_line = candidates_sorted[cand_iter.index]
    else:
        unique_cands.append(match_line)
        match_line=candidates_sorted[cand_iter.index]
        num_matches.append(match_cnt)
        match_cnt=0
    cand_iter.iternext()


with open ("unique_cands.txt","w") as f:
    for i in range(len(unique_cands)):
	unique_cands[i] = '	'.join(str(x) for x in unique_cands[i])
    	f.write(unique_cands[i] + "	" + str(num_matches[i])+"\n")

