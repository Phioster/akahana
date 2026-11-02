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

    @unittest.skipUnless(shutil.which('ffmpeg'), 'ffmpeg needed to read the .ogg files')
    def test_the_ostwald_sounds_have_their_level_and_loop_without_a_click(self):
        for name, lo, hi in (('teich', 0.03, 0.12), ('glockchen', 0.03, 0.15)):
            x = decode(name)
            rms = float(np.sqrt(np.mean(x ** 2)))
            self.assertGreater(rms, lo, name)
            self.assertLess(rms, hi, name)
        d = decode('teich')
        seam = abs(d[0] - d[-1])
        self.assertLess(seam, 0.25, 'the drops loop: no jump at the seam')
        b = decode('glockchen')
        self.assertLess(abs(b[-1]), 0.01, 'the little bell fades out')

    @unittest.skipUnless(shutil.which('ffmpeg'), 'ffmpeg needed to read the .ogg files')
    def test_the_dark_song_is_as_long_as_the_meadow_song(self):
        # both play together and are crossfaded: they must stay in step
        n = [len(decode(x)) / SR for x in ('musik', 'musik_dunkel')]
        self.assertAlmostEqual(n[0], n[1], delta=0.15)
        a, b = decode('musik'), decode('musik_dunkel')
        self.assertLess(share_below(b, 300.0) * 0.5, share_below(a, 300.0) + 0.3)   # sanity
        self.assertGreater(share_below(b, 200.0), share_below(a, 200.0), 'the dark one has more low end (drone)')


if __name__ == '__main__':
    unittest.main()
