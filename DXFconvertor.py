import aspose.cad as cad
import os


def convertor(path, format):
    for file in os.listdir(path):
        if file.split('.')[1] == 'dxf':
            cadImage = cad.Image.load(f"{path}{file}")

            if format == 'pdf':
                options = cad.imageoptions.PdfOptions()
            elif format == 'png':
                options = cad.imageoptions.PngOptions()
            elif format == 'svg':
                options = cad.imageoptions.SvgOptions()

            cadImage.save(f"{path}{file.split('.')[0]}.{format}", options)


path = "decomposed/"
convertor(path, 'svg')
