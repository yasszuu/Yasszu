import sherpa_onnx, soundfile as sf, sys, numpy as np
from scipy.signal import resample_poly
d='sherpa-onnx-whisper-small'
r=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=f'{d}/small-encoder.int8.onnx',decoder=f'{d}/small-decoder.int8.onnx',tokens=f'{d}/small-tokens.txt',language='fr',task='transcribe',num_threads=4)
for f in sys.argv[1:]:
    a,sr=sf.read(f,dtype='float32')
    if a.ndim>1: a=a.mean(1)
    if sr!=16000: a=resample_poly(a,16000,sr).astype('float32')
    s=r.create_stream(); s.accept_waveform(16000,a); r.decode_stream(s); print(f,'→',s.result.text)
