import os, sys, re

def strptime(s):
    tok = s.strip().split(':')
    if len(tok) == 2:
        tm = int(tok[0])*60
    elif len(tok) == 3:
        tm = int(tok[0])*3600 + int(tok[1])*60
    else:
        print 'Unknown format:', s
        return 0
    sec = float(tok[-1])
    return tm+sec

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
            data.append([strptime(tok[fcol['Start']]), strptime(tok[fcol['End']]), text])
        lid += 1
    data.sort()
    return data

def parse_srt(fname):
    lines = open(fname).read().splitlines()
    data = []
    lid = 0
    fcol = {}
    while lid < len(lines):
        l = lines[lid]
        if l.isdigit():
            lid += 1
            timeline = lines[lid]
            tok = timeline.split('->')
            lid += 1
            content = ''
            while lid < len(lines) and lines[lid].strip():
                content += lines[lid].strip() + ' '
                lid += 1
            data.append([strptime(tok[0]), strptime(tok[1]), content])
        else:
            lid += 1
    return data

def dump_lrc(data, filename, dump_trim_info=True):
    def strftime(t):
        tm=int(t)/60
        ts=t%60
        return '[%d:%.2f]' % (tm, ts)
    fout = open(filename, 'w')
    for d in data:
        if not dump_trim_info and '-- trimmed' in d[2]:
            continue
        fout.write(strftime(d[0]) + ' ' + d[2] + '\n')
    fout.close()

def dump_trim_data(trim_data, filename):
    fout = open(filename, 'w')
    for i, d in enumerate(trim_data):
        fout.write(str(d[0]) + ' ' + str(d[1]) + '\n')

def dump_trim_script(trim_data, filename, audioin, audioout, cmd='ffmpeg'):
    fout = open(filename, 'w')
    fout.write('%s -i "%s" -filter_complex "'%(cmd, audioin))
    fout.write('[0]atrim=start=0:end=%.2f,asetpts=PTS-STARTPTS[a%d]; '\
            %(trim_data[0][0], 0))
    for i in range(len(trim_data)-1):
        fout.write('[0]atrim=start=%.2f:end=%.2f,asetpts=PTS-STARTPTS[a%d]; '\
            %(trim_data[i][1], trim_data[i+1][0], i+1))
    fout.write('[0]atrim=start=%.2f,asetpts=PTS-STARTPTS[a%d]; '\
            %(trim_data[-1][1], len(trim_data)))
    fout.write('%sconcat=n=%d:v=0:a=1[aout]" '\
        %(''.join([('[a%d]'%i) for i in range(len(trim_data)+1)]), len(trim_data)+1))
    fout.write(' -map [aout] -codec:a libmp3lame -qscale:a 5 -strict -2 "%s"\n'\
        %audioout)
    fout.close()

def remove_gaps(data, interval, target_interval=3.0):
    did = 0
    gaps = []
    while did < len(data)-1:
        gap = data[did+1][0] - data[did][1]
        if gap > interval:
            gaps.append([did+1, gap])
        did += 1
    trim_data = []
    for g in gaps[::-1]:
        tstart = data[g[0]-1][1]+target_interval/2
        tend = data[g[0]][0]-target_interval/2
        trim_data.append([tstart, tend])
        msg = ' -- trimmed %.2f sec --' % (tend-tstart)
        data.insert(g[0], [tstart, tend, msg])
        delta = g[1] - target_interval
        for d in data[g[0]+1:]:
            d[0] -= delta
            d[1] -= delta
    return data, trim_data[::-1]

def test():
    data = parse_ass('test.ass')
    # data = parse_srt('test.srt')
    data, trim_data = remove_gaps(data, 5)
    dump_lrc(data, 'output.lrc')

if __name__ == '__main__':
    assert len(sys.argv) == 4, "Args: mp3_dir subtitle_dir(or - if same) output_dir"
    mp3_dir = sys.argv[1]
    sub_dir = mp3_dir if sys.argv[2] == '-' else sys.argv[2]
    out_dir = sys.argv[3]
    mp3_files = [i for i in os.listdir(mp3_dir) if i.endswith('.mp3')]
    mp3_files.sort()
    sub_type = 'ass'
    sub_files = [i for i in os.listdir(sub_dir) if i.endswith('.ass')]
    if len(sub_files) != len(mp3_files):
        sub_type = 'srt'
        sub_files = [i for i in os.listdir(sub_dir) if i.endswith('.srt')]
    assert len(sub_files) == len(mp3_files), "File number mismatch"
    sub_files.sort()
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    for i in range(len(mp3_files)):
        if sub_type == 'ass':
            data = parse_ass(os.path.join(sub_dir, sub_files[i]))
        elif sub_type == 'srt':
            data = parse_srt(os.path.join(sub_dir, sub_files[i]))
        data, trim_data = remove_gaps(data, 5)
        lrc_name = mp3_files[i][:-4] + '.lrc'
        dump_lrc(data, os.path.join(out_dir, lrc_name))
        dump_trim_script(trim_data, 'tmp.bat', \
            os.path.join(mp3_dir, mp3_files[i]), os.path.join(out_dir, mp3_files[i]))
        os.system('tmp.bat')
