import re
import os
from collections import Counter

# first find list of files in /var/log.radar
log_files = [str(f) if str(f).endswith(".log") else None for f in os.listdir("/var/log/radar")]
initial_anchors = []
revisited_anchors = []
duplicates = []

# Reg ex'es
duplicate_re = r'(?<=Transformer publishing DUPLICATE: Some\()\w+-\w+-\w+-\w+-\w+'
anchor_re = r'(?<=of anchor: Some\()\w+-\w+-\w+-\w+-\w+'

initial_anchor_re = r'(?<=publishing INITIAL anchor: Some\(Event\()\w+-\w+-\w+-\w+-\w+'
duplicates_re = r'(?<=with duplicates Vector\()(\w+-\w+-\w+-\w+-\w+,?)+' # note: need to parse this by comma

punctuator_duplicate_re = r'(?<=DUPLICATE FROM PUNCTUATOR: Some\()\w+-\w+-\w+-\w+-\w+'
punctuator_anchor_re = r'(?<=Punctuator publishing anchor: Some\(Event\()\w+-\w+-\w+-\w+-\w+'

for _f in log_files:
    with open("/var/log/radar/{}".format(_f), "r") as this_file:
        for line in this_file:
            anchor_res = re.search(anchor_re, line)
            if anchor_res:
                revisited_anchors.append(anchor_res.group(0))

            initial_anchor_res = re.search(initial_anchor_re, line)
            if initial_anchor_res:
                initial_anchors.append(initial_anchor_res.group(0))

            punctuator_anchor_res = re.search(punctuator_anchor_re, line)
            if punctuator_anchor_res:
                initial_anchors.append(punctuator_anchor_res.group(0))

            gathered_anchors = set([punctuator_anchor_res.group(0) if punctuator_anchor_res else None,
                                   initial_anchor_res.group(0) if initial_anchor_res else None,
                                   anchor_res.group(0) if anchor_res else None])

            duplicate_res = re.search(duplicate_re, line)
            if duplicate_res and duplicate_res.group(0) not in gathered_anchors:
                duplicates.append(duplicate_res.group(0))

            punctuator_duplicate_res = re.search(punctuator_duplicate_re, line)
            if punctuator_duplicate_res and punctuator_duplicate_res.group(0) not in gathered_anchors:
                duplicates.append(punctuator_duplicate_res.group(0))

            duplicates_res = re.search(duplicates_re, line)
            if duplicates_res:
                for dupe in duplicates_res.group(0).split(','):
                    if dupe not in gathered_anchors:
                        duplicates.append(dupe)

print "Anchors Republished as duplicates:"
for item in set(initial_anchors).union(set(revisited_anchors)).intersection(set(duplicates)):
    print item

print "Anchors Published Twice:"
anchors_twice = [i for i in Counter(initial_anchors).iteritems() if i[1] > 1]
for item in anchors_twice:
    print item
print "Count: {}".format(len(anchors_twice))

print "Duplicates Published Twice:"
dupes_twice = [i for i in Counter(duplicates).iteritems() if i[1] > 1]
for item in dupes_twice:
    print item
print "Count: {}".format(len(dupes_twice))

print "Anchors with Duplicates and Never Initially Published:"
for item in [i for i in revisited_anchors if i not in set(initial_anchors)]:
    print item

print "Anchor Count: {}".format(len(initial_anchors))
print "Anchor Revisited Count: {}".format(len(revisited_anchors))
print "Duplicates Count: {}".format(len(duplicates))