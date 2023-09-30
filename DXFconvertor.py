import aspose.cad as cad
import os


path = "decomposed/"

for file in os.listdir(path):
    cadImage = cad.Image.load(f"{path}{file}")

    rasterizationOptions = cad.imageoptions.CadRasterizationOptions()

    pdfOptions = cad.imageoptions.PdfOptions()
    cadImage.save(f"{path}{file.split('.')[0]}.pdf", pdfOptions)

    # pngOptions = cad.imageoptions.PngOptions()
    # cadImage.save("1.png", pngOptions)

    # dxfOptions = cad.imageoptions.DxfOptions()
    # cadImage.save("1.dxf", dxfOptions)
