"""Sounds must be what they claim to be: no deep thump in a splash (Philip, 0.8.1: "a dull knock like a
heartbeat, once", walking by the water)."""
import os
import shutil
import subprocess
import unittest

import numpy as np

AUDIO = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'audio')
SR = 22050


def decode(name):
    cmd = ['ffmpeg', '-loglevel', 'error', '-i', os.path.join(AUDIO, name + '.ogg'), '-ac', '1', '-ar', str(SR),
           '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).astype(float)


def share_below(x, hz):
    spec = np.abs(np.fft.rfft(x)) ** 2
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    return spec[f < hz].sum() / spec.sum()


class Sounds(unittest.TestCase):
    @unittest.skipUnless(shutil.which('ffmpeg'), 'ffmpeg needed to read the .ogg files')
    def test_wading_steps_splash_they_do_not_thump(self):
        # phone 0.8.1: now and then "a dull knock like a heartbeat" while walking by the water: two of the ten
        # wading steps were 45 % energy between 80 and 200 Hz (a thud from the recording, not a splash)
        for i in range(10):
            x = decode(f'schritt_waten_{i:02d}')
            deep = share_below(x, 200.0)
            self.assertLess(deep, 0.12, f'schritt_waten_{i:02d}: {deep:.0%} below 200 Hz (a thud)')
            rms = float(np.sqrt(np.mean(x ** 2)))
            self.assertGreater(rms, 0.02, f'schritt_waten_{i:02d} too quiet: {rms:.3f}')


if __name__ == '__main__':
    unittest.main()
