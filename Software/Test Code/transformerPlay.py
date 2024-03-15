import math
import os
from tempfile import TemporaryDirectory
from typing import Tuple

import torch
# import torchtext
from torch import nn, Tensor
from torch.nn import TransformerEncoder, TransformerEncoderLayer
from torch.utils.data import dataset

#import pygameTest2
from TransformerModel import TransformerModel


from torchtext.datasets import WikiText2
from torchtext.data.utils import get_tokenizer
from torchtext.vocab import build_vocab_from_iterator

import pygame
from pygame import midi
import mido
import torch
import time
import sys
import glob
import random
import transformerTest
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


#train_iter = WikiText2(split='train')
#tokenizer = get_tokenizer('basic_english')
#vocab = build_vocab_from_iterator(map(tokenizer, train_iter), specials=['<unk>'])

ntokens = 128  # size of vocabulary
emsize = 1024  # embedding dimension
d_hid = 1024  # dimension of the feedforward network model in ``nn.TransformerEncoder``
nlayers = 3  # number of ``nn.TransformerEncoderLayer`` in ``nn.TransformerEncoder``
nhead = 2  # number of heads in ``nn.MultiheadAttention``
dropout = 0.1  # dropout probability
model = TransformerModel(ntokens, emsize, nhead, d_hid, nlayers, dropout).to(device)

def get_file():
    assert(len(sys.argv) > 0)
    files = glob.glob(sys.argv[1])
    assert(len(files) > 0)
    return files[0]

def get_song_name(filename):
    return filename.split(".")[0]

filename = get_file()

def get_model():

    songname = get_song_name(filename)
    model_list = glob.glob(songname + ".model")
    print(model_list)
    if len(model_list) > 0:
        model.load(songname + ".model")
    else:
        transformerTest.main(songname)
        model.load(songname + ".model")
        

# model.load("auldlangsynebot.model")
get_model()


def sampleNote(probarray):
    minnote = 60 #C4
    maxnote = 84 #C6

    normconst = torch.sum(probarray[minnote:maxnote+1])
    p = random.random()
    ind = minnote
    while p > 0 and ind <= maxnote:
        p -= float(probarray[ind]/normconst)
        ind += 1
    return ind-1

def playStuff(model):
    pygame.midi.init()
    assert(pygame.midi.get_init())
    print('test')

    mido.set_backend('mido.backends.rtmidi')
    midi.init()
    otpts = mido.get_output_names()
    assert(len(otpts) > 0)
    outport = mido.open_output(otpts[0])  
    
    nDevices = midi.get_count()
    print(nDevices)
    for devnum in range(nDevices):
        print(midi.get_device_info(devnum))

    myBus = midi.Output(0)
    # compBus = myBus#midi.Output(0)

    # for p in range(60, 73):
    #     myBus.note_on(p, velocity=100, channel=0)
    #     myBus.note_on(p+7, velocity=100, channel=0)

    #     time.sleep(0.5)
    #     myBus.note_off(p, velocity=100, channel=0)
    #     myBus.note_off(p+7, velocity=100, channel=0)


    song = [72, 74, 72, 74, 72, 74]
    while(True):
        
        # output = model(torch.tensor(song))
        # print([song[-1]])
        model.load("auldlangsynebot.model")

        output = model(torch.tensor([72]))

        print(output.size())
        output_flat = output.view(-1, ntokens)
        print(output_flat.size())
        #newnote = int(torch.argmax(output_flat[len(song)-1]))

        #newnote = int(torch.argmax(output[output.size(0)-1][1])) #Pretty sure we're not supposed to flatten, and that from there we're misindexing
        newnote = int(torch.argmax(output[0][0])) #Pretty sure we're not supposed to flatten, and that from there we're misindexing

        #TODO sample from output_flat instead
        #newnote = sampleNote(output_flat[len(song)-1])

        print(newnote)
        
        song = song + [newnote]
        print(song)
        outport.send(mido.Message('note_on', note=newnote, velocity=100, channel=0))
        # myBus.note_on(newnote, velocity=100, channel=0)
        time.sleep(0.5)
        # myBus.note_off(newnote, velocity=100, channel=0)
        # outport.send(mido.Message('note_off', note=newnote, velocity=100, channel=0))

playStuff(model)