import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from django.core.files.storage import default_storage
from PIL import Image
from django.conf import settings
import os


def draw_svg_on_canvas(canvas, svg_file_url, x, y, width, height):
    # Construct the absolute path to the SVG file
    svg_file_path = os.path.join(settings.BASE_DIR, svg_file_url.strip("/"))

    # Open the SVG file
    with open(svg_file_path, 'r') as f:
        drawing = svg2rlg(f)

    # Calculate the scaling factors to fit the image within the available width and height
    scale_x = width / drawing.width
    scale_y = height / drawing.height
    scale_factor = min(scale_x, scale_y)

    # Calculate the adjusted width and height after scaling
    adjusted_width = drawing.width * scale_factor
    adjusted_height = drawing.height * scale_factor

    # Calculate the new x and y coordinates to center the image within the given width and height
    new_x = x + (width - adjusted_width) / 2
    new_y = y + (height - adjusted_height) / 2

    # Scale the SVG and render it on the canvas
    drawing.width = adjusted_width
    drawing.height = adjusted_height
    drawing.scale(scale_factor, scale_factor)
    renderPDF.draw(drawing, canvas, new_x, new_y)


def generate_pdf(project_id):
    # Import the models to avoid circular imports
    from file_storage.models import Project
    from stats.models import ResponseEntry

    # Get the project and the associated response entries
    project = Project.objects.get(pk=project_id)
    response_entries = ResponseEntry.objects.filter(experimental_response__project=project)

    # Prepare a byte stream to hold the PDF file in memory until it's ready to be saved
    buffer = io.BytesIO()

    # Create a canvas that will hold the PDF contents
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setTitle(f'{project.name} List')
    width, height = letter  # get the size of the page

    # Draw the table headers
    c.setFont('Helvetica-Bold', 12)  # Set the font to bold
    c.drawString(1 * cm, height - 1.9 * cm, 'Index')
    c.drawString(4.8 * cm, height - 1.9 * cm, 'Image')
    c.drawString(9 * cm, height - 1.9 * cm, 'Name')
    c.drawString(15 * cm, height - 1.9 * cm, 'Notes')

    # Draw a horizontal line under the headers
    c.line(1 * cm, height - 2 * cm, width - 1 * cm, height - 2 * cm)

    entry_y = height - 3 * cm  # Initial Y position
    entry_height = 3 * cm  # Height of each entry
    new_page_threshold = 3 * cm  # Threshold for creating a new page

    for i, entry in enumerate(response_entries, start=1):
        if entry_y < new_page_threshold:
            # End the current page and start a new one
            c.showPage()

            # Draw a bold line at the top of the new page
            c.setLineWidth(2)
            c.line(1 * cm, height - 2 * cm, width - 1 * cm, height - 2 * cm)

            # Reset the Y position for the new page
            entry_y = height - 3 * cm
    
        # Draw the index
        c.setFont('Helvetica-Bold', 12)  # Set the font to bold
        c.setFillColor('red')  # Set the font color to red
        c.drawString(1.4 * cm, entry_y - 0.6 * cm, str(entry.ensemble_index))  # Adjust the y coordinate for spacing

        # Draw the molecule image
        svg_file_url = entry.conformational_ensemble.svg_file.name
        draw_svg_on_canvas(c, svg_file_url, 3 * cm, entry_y - 1.7 * cm, 5 * cm, entry_height - 0.4 * cm)  # Adjust the positioning and size

        # Draw the molecule name
        c.setFont('Helvetica', 8)
        c.setFillColor('black')  # Set the font color to black
        c.drawString(9 * cm, entry_y + 0.25 * cm, entry.conformational_ensemble.molecule_name)  # Adjust the y coordinate for spacing

        # Draw a solid line below the entry
        c.setLineWidth(0.5)
        c.setStrokeColor('black')
        c.line(1 * cm, entry_y - 2 * cm, width - 1 * cm, entry_y - 2 * cm)

        # Update the y position for the next entry
        entry_y -= entry_height

    # Save the canvas contents into the buffer
    c.save()

    # Get the PDF contents from the buffer
    pdf = buffer.getvalue()

    # Close the buffer as we don't need it anymore
    buffer.close()

    # Return the PDF contents
    return pdf
