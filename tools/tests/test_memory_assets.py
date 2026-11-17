"""The sketch pages of the memories: one picture per place, small enough for the APK."""
import os
import unittest

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DIR = os.path.join(ROOT, 'assets', 'erinnerungen')
KEYS = ['lager', 'schrein', 'ruine', 'bachbruecke', 'gluehwuermchen', 'baeche', 'seesteg', 'seehuette',
        'graeber', 'steinbruecke', 'waldteich', 'ritual', 'jizo', 'felstor', 'holzfaeller', 'hoehle',
        'hoehle_innen', 'schlucht', 'aussicht', 'pass', 'bergsee', 'einsiedelei', 'dorfplatz', 'gewaechshaus',
        'gewaechshaus_innen', 'dorfschrein', 'obstwiese', 'muehle', 'bambus', 'fischer', 'teehaus']


class MemoryAssetsTest(unittest.TestCase):
    def test_every_page_has_a_picture(self):
        have = sorted(f[:-4] for f in os.listdir(DIR) if f.endswith('.png'))
        self.assertEqual(have, sorted(KEYS))

    def test_pictures_are_small(self):
        for k in KEYS:
            p = os.path.join(DIR, k + '.png')
            self.assertEqual(Image.open(p).width, 800, k)
            self.assertLess(os.path.getsize(p), 600_000, k)

    def test_paper_is_white_so_the_page_shows_through(self):
        # drawn multiplied onto the book page: paper that is not white darkens it into a box (Philip 0.23.1)
        for k in KEYS:
            im = Image.open(os.path.join(DIR, k + '.png')).convert('RGB')
            paper = max(im.getcolors(1 << 16), key=lambda c: c[0])[1]
            self.assertGreaterEqual(min(paper), 248, (k, paper))


if __name__ == '__main__':
    unittest.main()
