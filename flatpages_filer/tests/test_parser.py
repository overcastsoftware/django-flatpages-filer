from django.test import TestCase
from django.core.files import File as DjangoFile
import os
from filer.models.imagemodels import Image
from filer.models.filemodels import File
from filer.tests.helpers import (create_superuser, create_image)

from flatpages_filer.markdown_parser import parse
from flatpages_filer.utils import load_path_attr
from flatpages_filer.settings import PARSER


def create_filer_image(filename, image_name, owner):
    file_obj = DjangoFile(open(filename), name=image_name)
    image = Image.objects.create(owner=owner,
                                 original_filename=image_name,
                                 file=file_obj)
    return image


class TestParser(TestCase):
    def setUp(self):
        self.superuser = create_superuser()
        self.client.login(username='admin', password='secret')
        self.img = create_image()
        self.image_name = 'test_file.jpg'
        self.filename = self.image_name
        self.img.save(self.filename, 'JPEG')
        self.filer_image = create_filer_image(filename=self.filename,
                                              image_name=self.image_name,
                                              owner=self.superuser)

    def tearDown(self):
        self.client.logout()
        os.remove(self.filename)
        for f in File.objects.all():
            f.delete()

    def test_default_parser(self):

        img_id = self.filer_image.pk
        md_content = """
##This Is the title

- this is a list item
- this is a second list item

![This is my alt text][{}]

[This is my alt text][{}]
        """
        html_out = parse(md_content.format(img_id, img_id))
        self.assertEqual(html_out.split('\n')[0], '<h2>This Is the title</h2>')
        self.assertEqual(html_out.split('\n')[1], '<ul>')
        self.assertIn(self.image_name, html_out.split('\n')[-2])
        self.assertIn('img', html_out.split('\n')[-2])
        self.assertIn('alt', html_out.split('\n')[-2])
        self.assertIn('title', html_out.split('\n')[-2])
        self.assertIn(self.image_name, html_out.split('\n')[-1])
        self.assertIn('</a>', html_out.split('\n')[-1])
        self.assertIn('href=', html_out.split('\n')[-1])

    def test_custom_parser(self):

        text = '[ABBR](/foo) and _ABBR_\n\n' + \
               '*[ABBR]: Abreviation\n' + \
               '\t# A Code Comment' + \
               '\n![This is is an image][{}]'.format(self.filer_image.pk)
        text += '\n\n[This is a link][{}]'.format(
            self.filer_image.pk)
        parser_method = load_path_attr(PARSER[0])
        html_out = parser_method(text, **PARSER[1])
        self.assertIn('Abreviation', html_out.splitlines()[0])
        self.assertIn('codehilite', html_out.splitlines()[1])
        self.assertIn('img', html_out.split('\n')[-2])
        self.assertIn('alt', html_out.split('\n')[-2])
        self.assertIn('title', html_out.split('\n')[-2])
        self.assertIn(self.image_name, html_out.split('\n')[-1])
        self.assertIn('</a>', html_out.split('\n')[-1])
        self.assertIn('href=', html_out.split('\n')[-1])