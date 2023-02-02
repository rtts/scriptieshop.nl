#!/usr/bin/env python3
import sys
import subprocess

def count_file(file):
    colors = get_colors(file)
    return (colors.count(False), colors.count(True))

def get_colors(file):
    try:
        result = run_ghostscript(file)
    except:
        return []

    colors = []
    for page in result.split('\n'):
        if page:
            try:
                coverage = page.split()
                cyan = float(coverage[0])
                magenta = float(coverage[1])
                yellow = float(coverage[2])
                black = float(coverage[3])
                if cyan == magenta == yellow == black: # this is a black and white page in 99% of cases...
                    colors.append(False)
                elif cyan or magenta or yellow:
                    colors.append(True)
                else:
                    colors.append(False)
            except: # in case Ghostscript spewed errors to stdout...
                pass
    return colors

def run_ghostscript(file):
    result = subprocess.run(
        ['gs',
         '-dSAFER',
         '-dNOPAUSE',
         '-dBATCH',
         '-q',
         '-o-',
         '-sDEVICE=inkcov',
         file],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return str(result.stdout, 'utf-8')

if __name__ == '__main__':
    (bw, fc) = count_file(sys.argv[1])
    print ("{} black and white pages, {} color pages".format(bw, fc))
