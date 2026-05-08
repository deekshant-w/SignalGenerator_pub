# Convert static folder to zip file with .htaccess files in each folder
# Location: public_html/signalGenerator/static

from pathlib import Path
import shutil
import requests
from PIL import Image
import logging
import json
import hashlib
import traceback
import subprocess
from io import BytesIO
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info('Starting static bundler...')

argv = os.sys.argv[1:]
if "--compress" not in argv:
    # No compression only zip
    COMPRESS = {
        'css': False,
        'js': False,
        'html': False,
        'images': False,
    }
else:
    COMPRESS = {
        'css': True,
        'js': True,
        'html': False,
        'images': False,
    }
logger.info(f'Compression settings: {COMPRESS}')

current_path = Path(__file__).resolve().parent
static_folder = current_path / 'static'
dummy_static_folder = current_path / 'dummy_static'
output_zip = current_path / 'static.zip'

# delete dummy_static folder if it exists
if dummy_static_folder.exists():
    shutil.rmtree(dummy_static_folder)
    logger.info('Deleted dummy_static folder')

# Copy static folder to dummy_static folder
shutil.copytree(static_folder, dummy_static_folder)
logger.info('Copied static folder to dummy_static folder')

# remove unwanted files and folders from dummy_static folder
logger.info('Removing unwanted files and folders...')
for file in dummy_static_folder.rglob('*'):
    if file.is_file():
        if file.suffix in ['.py', '.ppt', '.pptx']:
            file.unlink()
    elif file.is_dir():
        if file.name.startswith('__') or file.name.startswith('.'):
            shutil.rmtree(file)
logger.info('Removed unwanted files and folders')

logger.info('Compressing files...')
# Compress files in dummy_static folder
if COMPRESS['css']:
    logger.info('Compressing css files...')
    for file in dummy_static_folder.rglob('*.css'):
        # compress css file
        original_css = file.read_text()
        compressed_css = requests.post('https://www.toptal.com/developers/cssminifier/api/raw', data={'input': original_css})
        if compressed_css.status_code == 200:
            file.write_text(compressed_css.text)
        else:
            logger.error(f"Failed to compress {file.name} css file")
            logger.error(compressed_css.text)
            raise Exception(f"Failed to compress {file.name} css file")
    logger.info('Successfully compressed css files')

# Terser can be used to compress js files
if COMPRESS['js']:
    logger.info('Compressing js files...')
    for file in dummy_static_folder.rglob('*.js'):
        # compress js file
        original_js = file.read_text()
        compressed_js = requests.post('https://www.toptal.com/developers/javascript-minifier/api/raw', data={'input': original_js})
        if compressed_js.status_code == 200:
            file.write_text(compressed_js.text)
        else:
            logger.error(f"Failed to compress {file.name} js file")
            logger.error(compressed_js.text)
            raise Exception(f"Failed to compress {file.name} js file")
    logger.info('Successfully compressed js files')
        
# Compress images using pillow
API_URL = 'https://api.tinify.com/shrink'
API_KEY = json.loads(open('.dkdev').read())['tinypng']
class IMAGES_CACHE:
    cache = {}
    @staticmethod
    def get_hash(file_data):
        return hashlib.sha256(file_data).hexdigest()
    @classmethod
    def in_cache(cls, file_data):
        return cls.cache.get(cls.get_hash(file_data))
    @classmethod
    def to_cache(cls, file_data, url):
        cls.cache[cls.get_hash(file_data)] = url
    def __str__(self):
        return str(self.cache)

def tinyfy_no_depedency(file):
    RETRIES = 1
    # Get compressed image URL
    for _ in range(RETRIES):
        try:
            if url:=IMAGES_CACHE.in_cache(file.read_bytes()):
                break
            send_file = subprocess.check_output(['curl', API_URL, '--user', f'api:{API_KEY}', '--data-binary', f'@{file}'])
            logger.info(f"recieved: {send_file}")
            send_file = json.loads(send_file.decode())
            logger.info(send_file)
            url = send_file['output']['url']
            IMAGES_CACHE.to_cache(file.read_bytes(), url)
            break
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Compression failed for {file.name} image file. Retrying...")
    else:
        raise Exception(f"Failed to compress {file.name} image file")
    logger.info(f"URL recieved: {url}")
    for _ in range(RETRIES):
        try:
            bFile = BytesIO()
            image_request = requests.get(url)
            bFile.write(image_request.content)
            image = Image.open(bFile)
            return image
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Retrieving failed for {file.name} image file. Retrying...")
            continue
    raise Exception(f"Failed to retrieve {file.name} image file")
if COMPRESS['images']:
    logger.info('Compressing images...')
    for file in dummy_static_folder.rglob('*'):
        if file.suffix in ['.jpg', '.jpeg', '.png',]:
            # compress image files with gradient
            if file.stem in ['sphere', 'ellipsoid']:
                with open(file, 'rb') as f:
                    image = tinyfy_no_depedency(file)
            else:
                image = Image.open(file)
                image = image.convert('P', palette=Image.ADAPTIVE, colors=16)
            image.save(file, pnginfo=None, optimize=True, quality=95)
    logger.info('Successfully compressed images')

logger.info("Adding .htaccess files...")
# iterate through all folders in dummy_static folder recursively
for folder in dummy_static_folder.rglob('*'):
    if folder.is_dir():
        # create a .htaccess file in each folder
        (folder / '.htaccess').touch()
# create a .htaccess file in dummy_static folder
(dummy_static_folder / '.htaccess').touch()

# delete output_zip if it exists
if output_zip.exists():
    shutil.rmtree(output_zip, ignore_errors=True)
logger.info("Cleaning up...")

# create a zip file of dummy_static folder
shutil.make_archive(output_zip.with_suffix(''), 'zip', dummy_static_folder)
logger.info('Created static.zip file')

# remove dummy_static folder
shutil.rmtree(dummy_static_folder)
logger.info("Bundling complete!")