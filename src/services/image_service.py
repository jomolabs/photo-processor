from PIL import Image

class ImageService(object):
    def __init__(self):
        pass

    def resize(self, dimensions, input_path, output_path):
        img = Image.open(input_path)
        img.thumbnail(dimensions, Image.ANTIALIAS)
        img.save(output_path, 'JPEG')
