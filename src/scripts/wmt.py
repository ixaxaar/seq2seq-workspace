#!/usr/bin/env python3

import argparse

from util import *

import torch.nn as nn
import torch as T
from torch.autograd import Variable as var
import numpy as np


def index_corpus(name, where, which):
    l = Lang(name)
    with open(where + '/' + which) as i:
        for line in i:
            l.index(normalize(line))
    l.save(where + '/' + name + '.lang')
    return l


def processWMT(which, where, src, targ, shard_size=10000, vectorize_gpu=None):
    nr_shard = 0
    src_lang = Lang(src)
    targ_lang = Lang(targ)
    sentence_pairs = []

    if vectorize_gpu:
        log.info('Creating source corpus dictionary...')
        src_lang = index_corpus(src, where, which + '.' + src)
        log.info('Creating target corpus dictionary...')
        targ_lang = index_corpus(targ, where, which + '.' + targ)
        log.info('Loading shards...')

        with open(where + '/' + which + '.' + src) as source:
            with open(where + '/' + which + '.' + targ) as target:
                done = False
                while not done:

                    log.info('Processing shard ' + str(nr_shard))
                    for i in range(shard_size):
                        s = normalize(source.readline())
                        t = normalize(target.readline())
                        sentence_pairs.append([s, t])
                        if s == '':
                            done = True

                    idxs, s, t, s_lens, t_lens = \
                        pack_batch(sentence_pairs, src_lang,
                                   targ_lang, vectorize_gpu)
                    packed = {
                        'indexes': idxs,
                        'source': s,
                        'target': t,
                        'source_lengths': s_lens,
                        'target_lengths': t_lens
                    }
                    with open(where + '/sentence-pairs-' + src + '-' + targ + '-shard-' + str(nr_shard) + '.t7', 'wb') as pairs:
                        T.save(packed, pairs)
                    sentence_pairs = []
                    nr_shard += 1
    else:
        with open(where + '/' + which + '.' + src) as source:
            with open(where + '/' + which + '.' + targ) as target:
                done = False
                while not done:

                    log.info('Processing shard ' + str(nr_shard))
                    for i in range(shard_size):
                        s = normalize(source.readline())
                        t = normalize(target.readline())
                        src_lang.index(s)
                        targ_lang.index(t)
                        sentence_pairs.append([s, t])
                        if s == '':
                            done = True

                    # Save the shard
                    with open(where + '/sentence-pairs-' + src + '-' + targ + '-shard-' + str(nr_shard) + '.pickle', 'wb') as pairs:
                        pickle.dump(sentence_pairs, pairs,
                                    pickle.HIGHEST_PROTOCOL)
                    sentence_pairs = []
                    nr_shard += 1

        # Save the dictionaries
        src_lang.save(where + '/' + src + '-lang-' + which + '.dict')
        targ_lang.save(where + '/' + targ + '-lang-' + which + '.dict')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='''
      Language distionary creator
      Creates a frequency-counted dictionary from a corpus
    ''')
    parser.add_argument('-where', required=True,
                        help='Path where the source and target corpuses are')
    parser.add_argument('-name', required=True,
                        help='Name of the files (e.g. `train` for `train.en` and `train.de`)')
    parser.add_argument('-src', required=True,
                        help='2-letter code of source language')
    parser.add_argument('-targ', required=True,
                        help='2-letter code of target language')
    parser.add_argument('-shard_size', required=False,
                        help='Size of each shard', type=int)
    parser.add_argument('-vectorize_gpu', required=False, type=int,
                        help='Should we vectorize the inputs? If so which gpu?')
    opts = parser.parse_args()

    processWMT(opts.name, opts.where, opts.src,
               opts.targ, opts.shard_size, opts.vectorize_gpu)
