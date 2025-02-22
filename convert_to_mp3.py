import io
import wave
import lameenc

def convert_to_mp3(audio_content: bytes) -> bytes:
    with wave.open(io.BytesIO(audio_content), 'rb') as wf:
        params = wf.getparams()
        frames = wf.readframes(wf.getnframes())

    encoder = lameenc.Encoder()
    encoder.silence()
    encoder.set_bit_rate(64)
    encoder.set_quality(7)  # 2 best, 7 fast
    encoder.set_in_sample_rate(params.framerate)
    encoder.set_channels(params.nchannels)
    encoded = encoder.encode(frames) + encoder.flush()
    return encoded
