import os, sys, re

def parse_ass(fname):
    lines = open(fname).read().splitlines()
    data = []
    started = False
    lid = 0
    fcol = {}
    while lid < len(lines):
        l = lines[lid]
        if '[Events]' in l:
            started = True
            lid += 1
            format = [i.strip() for i in lines[lid].split(',')]
            for i,f in enumerate(format):
                if f in ['Start', 'End', 'Text']:
                    fcol[f] = i
            assert(len(fcol) == 3)
        elif started:
            s = re.sub('(\{.*?\})', '', lines[lid])
            tok = [i.strip() for i in s.split(',')]
            text = tok[fcol['Text']]
            data.append([tok[fcol['Start']], tok[fcol['End']], text])
        lid += 1
    return data

def parse_srt(fname):
    lines = open(fname).read().splitlines()
    data = []
    lid = 0
    fcol = {}
    while lid < len(lines):
        l = lines[lid]
        
        lid += 1
    return data
    
if __name__ == '__main__':
    data = parse_ass('test.ass')
    print data[0], data[0][2].decode('utf8')
    print data[-1], data[-1][2].decode('utf8')