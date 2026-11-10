import tempfile
import unittest
from pathlib import Path

from PIL import Image

from app import convert


class ConversionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'input'
        self.output = self.root / 'output'
        self.source.mkdir()

    def test_conversion_and_name_collision(self):
        Image.new('RGBA', (8, 8), (255, 0, 0, 0)).save(self.source / 'photo.png')
        Image.new('RGB', (8, 8), 'blue').save(self.source / 'photo.bmp')

        self.assertEqual(convert(self.source, self.output), (2, 2, 0))
        self.assertEqual(sorted(p.name for p in self.output.iterdir()), ['photo.jpg', 'photo_2.jpg'])
        with Image.open(self.output / 'photo_2.jpg') as image:
            self.assertEqual(image.format, 'JPEG')
            self.assertEqual(image.getpixel((0, 0)), (255, 255, 255))

    def test_delete_rejects_unsupported_files(self):
        Image.new('RGB', (8, 8), 'blue').save(self.source / 'photo.png')
        (self.source / 'notes.txt').write_text('keep', encoding='utf-8')

        with self.assertRaisesRegex(ValueError, '未清空输入文件夹'):
            convert(self.source, self.output, delete=True)
        self.assertTrue((self.source / 'photo.png').exists())
        self.assertTrue((self.source / 'notes.txt').exists())

    def test_delete_after_success(self):
        Image.new('RGB', (8, 8), 'blue').save(self.source / 'photo.png')

        self.assertEqual(convert(self.source, self.output, delete=True), (1, 1, 0))
        self.assertEqual(list(self.source.iterdir()), [])
        self.assertTrue((self.output / 'photo.jpg').is_file())


if __name__ == '__main__':
    unittest.main()
