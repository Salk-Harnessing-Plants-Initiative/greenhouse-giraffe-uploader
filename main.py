import time
from datetime import datetime
import logging
import json
import threading
# Path-related
import os
import shutil
import ntpath
# For decoding QR
from PIL import Image
from pyzbar.pyzbar import decode
# For getting file creation timestamp
import platform
# For detecting new files
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
# For AWS S3
import boto3
from botocore.exceptions import ClientError
import uuid
# For logging remotely to AWS CloudWatch
from boto3.session import Session
import watchtower

def creation_date(file_path):
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See http://stackoverflow.com/a/39501288/1709587 for explanation.
    """
    if platform.system() == 'Windows':
        return os.path.getctime(file_path)
    else:
        stat = os.stat(file_path)
        try:
            return stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return stat.st_mtime

def get_file_created(file_path):
    """Gets the file's creation timestamp from the filesystem and returns it as a string
    Errors upon failure
    """
    return datetime.fromtimestamp(creation_date(file_path)).astimezone().isoformat()

def get_metadata(file_path):
    metadata = {"Metadata": {}}
    metadata["Metadata"]["user_input_filename"] = os.path.basename(file_path)
    try:
        metadata["Metadata"]["file_created"] = get_file_created(file_path)
    except:
        pass
    return metadata

def upload_file(s3_client, file_name, bucket, object_name, print_progress=False):
    """Upload a file to an S3 bucket and include special metadata
    :param s3_client: Initialized S3 client to use
    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. Also known as a "Key" in S3 bucket terms.
    :param print_progress: Optional, prints upload progress if True
    """
    s3_client.upload_file(file_name, bucket, object_name, 
        Callback=ProgressPercentage(file_name) if print_progress else None,
        ExtraArgs=get_metadata(file_name))


def generate_bucket_key(file_path, s3_directory):
    """Keep things nice and random to prevent collisions
    "/Users/russell/Documents/taco_tuesday.jpg" becomes "raw/taco_tuesday-b94b0793-6c74-44a9-94e0-00420711130d.jpg"
    Note: We still like to keep the basename because some files' only timestamp is in the filename
    """
    root_ext = os.path.splitext(ntpath.basename(file_path));
    return s3_directory + root_ext[0] + "-" + str(uuid.uuid4()) + root_ext[1];

def move(src_path, dst_path):
    """ Move file from src_path to dst_path, creating new directories from dst_path 
    along the way if they don't already exist.     
    Avoids collisions if file already exists at dst_path by adding "(#)" if necessary
    (Formatted the same way filename collisions are resolved in Google Chrome downloads)
    """
    root_ext = os.path.splitext(dst_path)
    i = 0
    while os.path.isfile(dst_path):
        # Recursively avoid the collision
        i += 1
        dst_path = root_ext[0] + " ({})".format(i) + root_ext[1]

    # Finally move file, make directories if needed
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    shutil.move(src_path, dst_path)

def make_parallel_path(src_dir, dst_dir, src_path, add_date_subdir=True):
    """Creates a parallel path of src_path using dst_dir instead of src_dir
    as the prefix. If add_date_subdir is True, uses dst_dir/(today's date in "YYYY-MM-DD" format)/
    as the new prefix instead.

    src_dir should be a prefix of src_path, else error
    """
    # Remove prefix
    prefix = src_dir
    if src_path.startswith(prefix):
        suffix = src_path[len(prefix)+1:]
    else:
        raise Exception("src_dir {} was not a prefix of src_path {}".format(src_dir, src_path))

    # Add prefix
    result = dst_dir
    if add_date_subdir:
        result = os.path.join(result, datetime.today().strftime('%Y-%m-%d'))
    result = os.path.join(result, suffix)
    return result

class ProgressPercentage(object):
    """Callback used for boto3 to sporadically report the upload progress for a large file
    """

    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0

    def __call__(self, bytes_amount):
        """Callback that logs how many bytes have been uploaded so far for a particular file
        """
        self._seen_so_far += bytes_amount
        percentage = (self._seen_so_far / self._size) * 100
        # Print instead of log because this gets kind of spammy
        print("Uploading status for {}: {} / {} ({}%)".format(self._filename, self._seen_so_far, self._size, percentage))

class S3EventHandler(FileSystemEventHandler):
    """Handler for what to do if watchdog detects a filesystem change
    """

    def __init__(self, s3_client, s3_bucket, s3_bucket_dir, unprocessed_dir, done_dir, error_dir):
        self.s3_client = s3_client
        self.s3_bucket = s3_bucket
        self.s3_bucket_dir = s3_bucket_dir
        self.unprocessed_dir = unprocessed_dir
        self.done_dir = done_dir
        self.error_dir = error_dir

    def on_created(self, event):
        is_file = not event.is_directory
        if is_file:
            process(event.src_path, self.s3_client, self.s3_bucket, self.s3_bucket_dir, 
                self.done_dir, self.error_dir, self.unprocessed_dir)
        else:
            # Crawl the new directory and process everything in it
            file_paths = get_preexisting_files(event.src_path)
            for file_path in file_paths:
                process(file_path, s3_client, bucket, bucket_dir, done_dir, error_dir, unprocessed_dir)

# Global
SECONDS_DELAY = 10.0
last_reference = {}
try:
    with open('persist.json') as f:
        last_reference = json.load(f)
except:
    pass
lock = threading.Lock()
t = None
auth = boxsdk.JWTAuth.from_settings_file('box_config.json')
client = boxsdk.Client(auth)
with open('config.json') as f:
    config = json.load(f)
unprocessed_dir = config['unprocessed_dir']
error_dir = config['error_dir']
done_dir = config['done_dir']
postgres = config['postgres']
cloudwatch = config['cloudwatch']

# Fail on startup if something's wrong
print("Checking the connections...")
# None of the dirs should be the same as another
assert (len([unprocessed_dir, error_dir, done_dir]) == len(set([unprocessed_dir, error_dir, done_dir])))
# Check Box connection
client.user().get()
# Check postgres connection
psycopg2.connect(user=postgres['user'],
    password=postgres['password'],
    host=postgres['host'],
    port=postgres['port'],
    database=postgres['database']
).cursor().execute("SELECT version();")
# Setup remote logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
"""
watchtower_handler = watchtower.CloudWatchLogHandler(
    log_group=cloudwatch["log_group"],
    stream_name=cloudwatch["stream_name"],
    send_interval=cloudwatch["send_interval"],
    create_log_group=False
)
logger.addHandler(watchtower_handler)
"""

def process():
    logger = logging.getLogger(__name__)
    files = sorted([file for file in os.listdir(unprocessed_dir) if not file[0] == '.'])
    if len(files) > 0:
        logger.warning("Processing files in the order: {}".format(files))
    for file in files:
        path = os.path.join(unprocessed_dir, file)
        # QR code if present
        try:
            qr_codes = [qr_object.data.decode() for qr_object in decode(Image.open(path))]
            for qr_code in qr_codes:
                update_reference(qr_code)
        except Exception as e:
            logger.error(e)
        # Process
        try:
            for match in last_reference['matches']:
                upload_to_box(path, match['box_folder_id'], match['section_name'])
            # upload_to_s3(path)
            done_path = desktop_uploader.make_parallel_path(unprocessed_dir, done_dir, path)
            desktop_uploader.move(path, done_path)
        except Exception as e:
            logger.error(e)
            error_path = desktop_uploader.make_parallel_path(unprocessed_dir, error_dir, path)
            desktop_uploader.move(path, error_path)

def update_reference(qr_code):
    print("qr = {}".format(qr_code))
    global last_reference
    try:
        # Connect to database
        connection = psycopg2.connect(user=postgres['user'],
            password=postgres['password'],
            host=postgres['host'],
            port=postgres['port'],
            database=postgres['database']
        )
        # Create a cursor to perform database operations
        cursor = connection.cursor()
        # Executing a SQL query
        query = (
            "SELECT box_folder_id, experiment_id, section_name FROM greenhouse_box\n"
            "INNER JOIN section USING (section_name)\n"
            "WHERE section_id = '{value}' OR section_name = '{value}';".format(value=qr_code)
        )
        cursor.execute(query)
        results = cursor.fetchall()
        print(results)
        try:
            if results is not None:
                print("uh hello")
                last_reference = {'matches' : []}
                for result in results:
                    print("hi")
                    match = {}
                    match['box_folder_id'] = result[0]
                    match['experiment_id'] = result[1]
                    match['section_name'] = result[2]
                    last_reference['matches'].append(match)

                print("Updated to {}".format(last_reference)) # Temporary 
                with open('persist.json', 'w') as f:
                    json.dump(last_reference, f, indent = 4)
        except Exception as e:
            print(e)

    except (Exception, Error) as error:
        raise Exception("Error while connecting to PostgreSQL: ", error)
    finally:
        if (connection):
            cursor.close()
            connection.close()

def get_subfolder(box_folder, subfolder_name):
    subfolders = [item for item in box_folder.get_items() if type(item) == boxsdk.object.folder.Folder]
    subfolder_names = [subfolder.name for subfolder in subfolders]
    if subfolder_name not in subfolder_names:
        subfolder = box_folder.create_subfolder(subfolder_name)
        return subfolder
    else:
        for subfolder in subfolders:
            if subfolder.name == subfolder_name:
                return subfolder

def upload_to_box(file, box_folder_id, section_name, use_date_subfolder=True, use_section_subfolder=True):
    root_folder = client.folder(folder_id=box_folder_id).get()
    current_folder = root_folder

    if use_date_subfolder:
        file_creation_timestamp = desktop_uploader.creation_date(file)
        file_creation_date = datetime.fromtimestamp(file_creation_timestamp).strftime('%Y-%m-%d')
        current_folder = get_subfolder(current_folder, file_creation_date)

    if use_section_subfolder:
        current_folder = get_subfolder(current_folder, section_name)

    current_folder.upload(file)

class GiraffeEventHandler(FileSystemEventHandler):
    """Handler for what to do if watchdog detects a filesystem change
    """
    def on_created(self, event):
        is_file = not event.is_directory
        if is_file:
            # Attempt to cancel the thread if in countdown mode
            with lock:
                t.cancel()

def main():
    global t

    logger.warning("Running Greenhouse Giraffe Uploader...")
    # process() will run after the countdown if not interrupted during countdown
    with lock:
        t = threading.Timer(SECONDS_DELAY, process)
    # Setup the watchdog handler for new files that are added while the script is running
    observer = Observer()
    observer.schedule(GiraffeEventHandler(), unprocessed_dir, recursive=True)
    observer.start()
    # run process() with countdown indefinitely
    try:
        while True:
            with lock:
                t = threading.Timer(SECONDS_DELAY, process)
                t.start()
            t.join()
    except KeyboardInterrupt:
        logger.warning("KeyboardInterrupt: shutting down...")
        observer.stop()
        observer.join()
        t.join()
        # todo: t.stop equivl

if __name__ == "__main__":
    main()
