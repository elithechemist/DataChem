import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from svglib.svglib import svg2rlg
from django.core.files.storage import default_storage
from PIL import Image

print("Imported")