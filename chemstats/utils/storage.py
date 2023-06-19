"""storage.py: Functions for storing files and data in the database."""
__author__ = "Eli Jones"

import random
import tempfile
from django.conf import settings
import boto3, os, io
from botocore.exceptions import ClientError


s3_client = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, 
                         aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                         region_name=settings.AWS_S3_REGION_NAME)


def __get_molecule_subpath(unique_id, file_extension):
    """
    Given the UUID of a .LOG, .MOL, or .SVG (e.g., '123e4567-e89b-12d3-a456-426614174000'), 
    returns the subpath based on alphanumeric hashing.
    EXAMPLE: _get_molecule_id('123e4567-e89b-12d3-a456-426614174000', 'log')
             returns '12/3e/123e4567-e89b-12d3-a456-426614174000.log'
    """
    full_file_name = f"{unique_id}.{file_extension}"
    
    # Create subdirectories based on segments of the UUID
    subdir1 = full_file_name[:2]
    subdir2 = full_file_name[2:4]

    return f'{subdir1}/{subdir2}/{full_file_name}'


def s3_molecule_store(file_name, content):
    """
    Uploads a molecule file to S3, organizing it into appropriate subdirectories
    based on file type and molecule number.
    
    EXAMPLE USAGE:
    file_name = "123e4567-e89b-12d3-a456-426614174000.svg"
    content = "<svg>....</svg>"  # Some SVG content
    s3_molecule_store(file_name, content.encode())  # Content must be bytes
    """
    molecule_id, file_extension = file_name.split('.', 1)
    print("FILE EXTENSION: " + file_extension)

    # Convert content to bytes if it's not already
    if not isinstance(content, bytes):
        content = content.encode()

    if file_extension == 'xyz':
        print("Now in xyz")
        # Create an in-memory bytes buffer
        in_memory_file = io.BytesIO(content)
        
        # Upload the in-memory file to the 'temp' directory in S3
        s3_key = f'media/temp/{molecule_id}.xyz'
        print(s3_key)
        s3_client.upload_fileobj(in_memory_file, settings.AWS_STORAGE_BUCKET_NAME, s3_key)

        return s3_key
    
    # Determine the file type
    elif file_extension == 'log':
        file_type_directory = 'log_files'
        content_type = 'text/plain'
    elif file_extension == 'svg':
        file_type_directory = 'svg_files'
        content_type = 'image/svg+xml'
    elif file_extension == 'mol':
        file_type_directory = 'mol_files'
        content_type = 'chemical/x-mdl-molfile'
    else:
        raise ValueError(f"Unsupported file type for the file: {file_name}. Only .LOG, .SVG, and .MOL files " +
                         "are supported for storage in the Amazon S3 bucket.")
    
    # Get the subpath based on the molecule number
    molecule_subpath = __get_molecule_subpath(molecule_id, file_extension)
    
    # Construct the full path for uploading to the S3 media folder
    s3_key = f'media/molecules/{file_type_directory}/{molecule_subpath}'

    # Create a file-like object from content
    content_file = io.BytesIO(content)

    # Upload the content to S3 with the appropriate content type
    s3_client.upload_fileobj(content_file, settings.AWS_STORAGE_BUCKET_NAME, s3_key,
                             ExtraArgs={'ContentType': content_type})

    return s3_key


def s3_molecule_retrieve(file_name, as_path=True):
    """
    Retrieves the actual file from S3 for a given molecule file based on its filename.
    """
    print("Now in s3_molecule_retrieve")
    molecule_id, file_extension = file_name.split('.', 1)

    if file_extension == 'xyz':
        s3_key = f'media/temp/{molecule_id}.xyz'
    elif file_extension == 'log':
        file_type_directory = 'log_files'
    elif file_extension == 'svg':
        file_type_directory = 'svg_files'
    elif file_extension == 'mol':
        file_type_directory = 'mol_files'
    else:
        raise ValueError(f"Unsupported file type for the file: {file_name}. Only .LOG, .SVG, and .MOL files are supported for retrieval from the Amazon S3 bucket.")
    
    if file_extension != 'xyz':
        molecule_subpath = __get_molecule_subpath(molecule_id, file_extension)
        print(molecule_subpath)
        s3_key = f'media/molecules/{file_type_directory}/{molecule_subpath}'

    file_obj = io.BytesIO()
    s3_client.download_fileobj(settings.AWS_STORAGE_BUCKET_NAME, s3_key, file_obj)

    # Reset the file pointer to the beginning of the file-like object
    file_obj.seek(0)

    # Read and decode the contents
    contents = file_obj.read().decode('utf-8')

    if as_path:
        return contents
    else:
        return contents


def s3_profile_image_retrieve(file_name, as_path=True):
    """
    Retrieves the profile image file from S3 based on its filename.
    """
    print("Now in s3_profile_image_retrieve")
    print(f'Bucket Name: {settings.AWS_STORAGE_BUCKET_NAME}')
    print(f'File Name: {file_name}')

    # Construct the S3 key based on the provided file_name
    s3_key = f"media/profile_pics/{file_name}"
    print(f'S3 Key: {s3_key}')
    
    # Create a file-like object to store the retrieved file
    file_obj = io.BytesIO()

    # Download the file from S3 into the file-like object
    s3_client.download_fileobj(settings.AWS_STORAGE_BUCKET_NAME, s3_key, file_obj)

    # Reset the file pointer to the beginning of the file-like object
    file_obj.seek(0)
    
    # Return file object for further processing or returning as HTTP response
    if as_path:
        return file_obj
    else:
        return file_obj.read()

def s3_profile_image_store(file_name, image):
    """
    Uploads a profile image to S3.
    """
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")

    # Always store custom images in the profile_pics directory
    s3_key = f"media/profile_pics/{file_name}"

    s3_client.put_object(
        Body=buffer.getvalue(),
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=s3_key
    )

def s3_get_random_default_image():
    """
    Fetches a random default image from S3 and returns the sub_url relative
    to the profile_pics directory.
    """
    try:
        default_images_path = f'{settings.S3_DEFAULT_PROFILE_PICS_LOCATION}'
        print("DEFAULT IMAGES PATH: " + default_images_path)
        
        objects = s3_client.list_objects_v2(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Prefix=default_images_path)
        
        # Only keep the file names, not the full paths and filter out empty strings
        files = [obj['Key'].split('/')[-1] for obj in objects['Contents'] if obj['Key'] != default_images_path and obj['Key'].split('/')[-1]]
        
        print("FILES without prefix: " + str(files))
        
        # Randomly select one of the file names
        selected_file = random.choice(files)
        
        print("Selected File: " + selected_file)

        sub_url = f'default_profile_pics/{selected_file}'
        return sub_url
    except Exception as e:
        print(f"An error occurred while fetching a random default image from S3: {e}")
        return None

def s3_generate_presigned_url(file_name):
    """
    Generate a presigned URL for the file stored in S3.
    """
    print("In s3_generate_presigned_url")
    molecule_id, file_extension = file_name.split('.', 1)

    if file_extension == 'svg':
        file_type_directory = 'svg_files'
    else:
        raise ValueError(f"Unsupported file type for the file: {file_name}. Only .SVG files are supported for generating pre-signed URL from the Amazon S3 bucket.")

    molecule_subpath = __get_molecule_subpath(molecule_id, file_extension)
    
    s3_key = f'media/molecules/{file_type_directory}/{molecule_subpath}'
    
    # Generate a presigned URL for the S3 object
    # Note: The following line is removed as s3_client has been defined at the beginning of this module
    # s3_client = boto3.client('s3')
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                                                            'Key': s3_key},
                                                    ExpiresIn=3600)
    except ClientError as e:
        print("Error generating presigned URL.")
        print(e)
        return None
    
    # The response contains the presigned URL
    print("Presigned URL: " + response)
    return response

def s3_molecule_delete(file_name):
    """
    Deletes the molecule file from S3 based on its filename.
    """
    try:
        molecule_id, file_extension = file_name.split('.', 1)
        file_type_directory = ''
        if file_extension == 'mol':
            file_type_directory = 'mol_files'
        elif file_extension == 'svg':
            file_type_directory = 'svg_files'
        else:
            raise ValueError(f"Unsupported file type for the file: {file_name}. Only .MOL and .SVG files are supported for deletion from the Amazon S3 bucket.")

        molecule_subpath = __get_molecule_subpath(molecule_id, file_extension)
        s3_key = f'media/molecules/{file_type_directory}/{molecule_subpath}'
        
        # Deleting the file from S3
        s3_client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=s3_key)
        print(f'Successfully deleted {s3_key} from S3')
    
    except ClientError as e:
        print(f'An error occurred while trying to delete the file {file_name} from S3: {e}')
