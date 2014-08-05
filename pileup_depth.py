#!/usr/bin/env python

import bisect
class RangeSet:
  def __init__(self, rangelist = []):
    self.normalized_list = []
    for range in rangelist:
      self.insert(range[0],range[1])

  def __contains__(self, value):
    return bisect.bisect(self.normalized_list, value) % 2

  def inside_range(self, value):
    i = bisect.bisect(self.normalized_list, value)
    return (self.normalized_list[i-1],
            self.normalized_list[i])

  def insert(self, start, end):
    if start == end:
      return
    elif start > end:
      start, end = end, start

    startIndex = bisect.bisect(self.normalized_list, start)
    endIndex = bisect.bisect(self.normalized_list, end)
    insortingValues = []
    if start not in self:
      insortingValues.append(start)
    if end not in self:
      insortingValues.append(end)
    del self.normalized_list[startIndex: endIndex]
    for value in insortingValues:
      bisect.insort(self.normalized_list, value)

  def getWidth(self):
    res = 0
    count = 0
    for l in self.normalized_list[1::2]:
      res += l - self.normalized_list[count]
      count += 2
    return res


def create_range_set(segment_file):
  pos_d = {}
  for s in segment_file:
    cols = s.split()
    if cols[0] != "chrom":
      if pos_d.has_key(cols[0]):
        pos_d[cols[0]].insert(int(cols[1]),int(cols[2]))
      else:
        o = RangeSet([(int(cols[1]), int(cols[2]))])
        pos_d[cols[0]] = o
  return pos_d

def count_read_num(pileup_file, range_set):
  d = {}
  for s in pileup_file:
    cols = s.split()
    chr = cols[0]
    pos = int(cols[1])
    depth = int(cols[3])
    if pos in range_set.get(chr,[]):
      if not d.has_key(chr):
        d[chr] = {}
      range = range_set[chr].inside_range(pos)
      d[chr][range] = d[chr].get(range, 0) + depth
  return d

if __name__ == "__main__":
  import argparse
  import sys
  parser = argparse.ArgumentParser()
  parser.add_argument("segment_file",
                      type=argparse.FileType("r"))
  parser.add_argument("pileup_files", 
                      type=argparse.FileType("r"),
                      default=sys.stdin,
                      nargs="*")
  parser.add_argument("-o", "--output", type=argparse.FileType("w"),
                      default=sys.stdout)
  args = parser.parse_args()

  range_set = create_range_set(args.segment_file)
  
  counts = []
  for f in args.pileup_files:
    counts.append(count_read_num(f, range_set))
  
  args.segment_file.seek(0)
  d = {}
  for s in args.segment_file:
    l = s.split()
    chr = l[0]
    begin = int(l[1])
    end = int(l[2])
    if not d.has_key(chr):
      d[chr] = []
    d[chr].append((begin,end))
  
  for key in sorted(d.keys()):
    for t in d[key]:
      print >> args.output, "\t".join([key, str(t[0]), str(t[1])] + 
                       [ str(c.get(key,{}).get(t,0)) for c in counts])
