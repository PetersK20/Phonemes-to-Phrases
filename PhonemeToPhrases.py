# Here is what you could do. You will need the wave (standard library) and numpy modules.

import wave
import numpy as np
from os import  path
from pocketsphinx.pocketsphinx import *
import soundfile as sf
import pyrubberband as pyrb
from pydub import AudioSegment

# set up directory for pocketsphinx and data directory
MODELDIR = "C:/Users/Kyle Peters/PycharmProjects/Music Analyzer/venv/Lib/site-packages/pocketsphinx/model/"
DATADIR = "C:/Users/Kyle Peters/Desktop/"

# Create a decoder with certain model
config = Decoder.default_config()
config.set_string('-hmm', path.join(MODELDIR, 'en-us'))
config.set_string('-allphone', path.join(MODELDIR, 'en-us-phone.lm.bin'))
config.set_float('-lw', 2.0)
config.set_float('-beam', 1e-10)
config.set_float('-pbeam', 1e-10)



# set the audio file for phoneme detection here
stream = open(path.join(DATADIR, 'go.wav'), 'rb')

# Create phoneme detector object
decoder = Decoder(config)
decoder.start_utt()

# detects phonemes and their start/end time
while True:
    buf = stream.read(1024)
    if buf:
        decoder.process_raw(buf, False, False)
    else:
        break
decoder.end_utt()

# create an array for the phonemes
phonemeList = [seg.word for seg in decoder.seg()]

# create an array for the duration
duration_frame = np.subtract([seg.end_frame * 10 for seg in decoder.seg()], [seg.start_frame * 10 for seg in decoder.seg()])
print(duration_frame)

phonemeList = ["SIL", "G", "OW"]
data = []
outfile = "C:/Users/Kyle Peters/Desktop/Output File.wav"
componentCount = 0
for index in range(0, len(phonemeList)):
    phoneme = phonemeList[index]

    # SIL is when there is silence at the beginning and +SPN+ is when there is silence at the end
    if phoneme == "SIL" or phoneme == "+SPN+":
        componentCount += 1
        wavFile = wave.open(DATADIR + "SIL.wav", 'rb')
        # number of samples per second
        framesPerSecond = wavFile.getframerate()
        framesPerMiliSec = framesPerSecond / 1000
        framesPerPhoneme = int(framesPerMiliSec * duration_frame[index])
        data.append([phoneme, wavFile.getparams(), wavFile.readframes(framesPerPhoneme)])
    else:
        # add two because a silence is also added after the phoneme
        componentCount += 2
        # get duration of phoneme
        phonemeDuration = duration_frame[index]
        # get phoneme file duration with pydub
        fileTempDuration = AudioSegment.from_wav(DATADIR + phonemeList[index] + " Phoneme Mod.wav")
        currentDuration = len(fileTempDuration)

        # caluculate how fast to play the file
        tempo = currentDuration / phonemeDuration

        # get phoneme file in a style that rubber band can use
        wavFileRB, samplingRate = sf.read(DATADIR + phonemeList[index] + " Phoneme Mod.wav")

        # apply the tempo to the wav file
        wavFileRBStretched = pyrb.time_stretch(wavFileRB, samplingRate, tempo)

        # save the file
        sf.write("tempFile.wav", wavFileRBStretched, samplerate=16000)
        wavTemp = wave.open('tempFile.wav', 'rb')
        dataTemp = wavTemp.readframes(wavTemp.getnframes())

        # reopen the file with the pyDub library
        wavFilePydub = AudioSegment.from_wav("tempFile.wav")
        # is it the last phoneme, if so, add a fade out and fade in, if not just add a fade in
        if index == (len(phonemeList)-1):
            wavFilePydubFade = wavFilePydub.fade_in(duration_frame[index]).fade_out(duration_frame[index])
        else:
            wavFilePydubFade = wavFilePydub.fade_in(duration_frame[index])
        # save the file then reopen it using the wave module in order to add the date to the data array
        wavFilePydubFade.export("tempFile.wav", format="wav")
        wavFile = wave.open("tempFile.wav", 'rb')
        data.append([phoneme, wavFile.getparams(), wavFile.readframes(wavTemp.getnframes())])

        # add 4 millisecond silence using the wav library
        # get the silence
        wavFile = wave.open(DATADIR + "SIL.wav", 'rb')
        # calculate the frames per second then per millisecond then per phoneme (per 4 seconds in this case)
        framesPerSecond = wavFile.getframerate()
        framesPerMiliSec = framesPerSecond / 1000
        framesPerPhoneme = int(framesPerMiliSec * 4)
        # append data to the data array
        data.append([phoneme, wavFile.getparams(), wavFile.readframes(framesPerPhoneme)])

    wavFile.close()

output = wave.open(outfile, 'wb')
output.setparams(data[0][1])
for i in range(componentCount):
    output.writeframes(data[i][2])
output.close()









