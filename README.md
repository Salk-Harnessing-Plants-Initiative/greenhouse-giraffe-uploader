# greenhouse-giraffe-uploader
* For use on Windows
* Put the images in the `unprocesssed_dir`. They cannot be in subfolders.
* Uses at most one `process()` thread at any given time to react to images added to `unprocessed_dir`.
	* Starts a single `process()` thread on startup. 
	* If a new image is added to `unprocessed_dir` and `process()` isn't already running, then `process()` will run after a countdown of 10 seconds. Adding another image during this countdown will reset the coundown timer. (Thus a dump of images will not be processed until all of them are added to the folder).
	* If a new image is added to `unprocessed_dir` and `process()` is already running, then waits for `process()` to finish and then initiates a new `process()` thread (with the same 10 second countdown).
* `process()` looks at all the images present in `unprocessed_dir` at the time of calling and processes them by their filenames in alphabetical order. This ordering is how we distinguish the order for the "queue" or "stream" of images: a temporal cutoff for all images present, and then that batch processed in alphabetical order. 
	* The reason for this ordering logic is because we expect there to be a "stream" of images such that an image without a QR code will be designated the QR code of the image with a QR code most recently in front of it. E.g., `queue batch: A* <- B <- C <- D* <- E`, where the images with a `*` represent those with QR codes. `A`, `B`, and `C` will all be assigned `A`'s QR code, and `D`, `E` will be assigned `D`'s QR code. If the next batch (happening much later in time) is `apple <- banana* <- cookie`, then `apple` will be assigned `D`'s QR code, and `banana`, `cookie` will be assigned `banana`'s QR code. The full image stream is `A* <- B <- C <- D* <- E <- apple <- banana* <- cookie`, and it still manages to work even though the image names aren't even in alphabetical order in the macro sense. 
* Important: Relies on the fact that the file creation timestamp in the Windows filesystem has millisecond (and microsecond) granularity. This chronology helps distinguish adjacent images which might be stitched together in the future.

# Installation 
You should use Windows Powershell during this installation.

## Part 1: Dependencies
0. Install git https://git-scm.com/download/win
1. Install Python 3.6.2 https://www.python.org/downloads/release/python-362/. Pip will come with it.
2. Clone the repo
3. `pip install -r requirements.txt` in the directory

## Part 2: Configure
4. `cp example_config.json config.json`, and begin to fill it out. 
5. You should have a Postgres user with at least read access. 
6. AWS VPC should have IP added to whitelist for Postgres access
7. Create the AWS Cloudwatch log group if you want to track the service remotely.
8. You should have an AWS IAM user with the following policies:
```
s3:PutObject
s3:ListAllMyBuckets
sts:AssumeRole
logs:CreateLogStream
logs:CreateLogGroup
logs:PutLogEvents
Access to the S3 bucket
Access to the cloudwatch log group
```
9. Put all the login information into `config.json`. The region is `us-west-2`. 
10. Make sure to specify the `unprocessed`, `error`, and `done` folders.
11. Test that the Python script works: `python main.py` and put some images into your `unprocessed` directory.

## Part 3: Run automatically as a service
We use the Non-Sucking Service Manager (https://stackoverflow.com/a/46450007/14775744). Ensure you are running Windows Powershell as administrator.

12. Get the python path:
```
python get_path_to_python.py
```

13. Install 
```
.\nssm install PythonGiraffeService "C:\Users\russe\AppData\Local\Programs\Python\Python36\python.exe" "C:\Users\russe\Desktop\code\greenhouse-giraffe-uploader\main.py"
```

Note/quirk: If there are spaces in the path to `main.py`, instead of one set of quotes, you need to use 5 double-quotes on each side:
```
.\nssm install PythonGiraffeService "C:\Users\weird user\AppData\Local\Programs\Python\Python36\python.exe" """""C:\Users\weird user\Desktop\code\greenhouse-giraffe-uploader\main.py"""""
```


14. Set outputs to a log file:
```
.\nssm set PythonGiraffeService AppStdout C:\Users\russe\Desktop\code\greenhouse-giraffe-uploader\service.log
.\nssm set PythonGiraffeService AppStderr C:\Users\russe\Desktop\code\greenhouse-giraffe-uploader\service.log
```

15. Start and stop:
```
.\nssm start PythonGiraffeService
```
```
.\nssm stop PythonGiraffeService
```
NSSM configures the service to be `automatic` by default, which means that if the computer is rebooted it'll start the script up again.

16. Update Windows power/battery settings so takes longer to fall asleep (or not at all). 

## Hints
* On Windows you have to open a new command prompt/shell after installing a CLI application for it to recognize it in path.
* If you see an ugly ``ImportError`` when importing ``pyzbar`` on Windows
you will most likely need the `Visual C++ Redistributable Packages for Visual
Studio 2013
<https://www.microsoft.com/en-US/download/details.aspx?id=40784>`. Install ``vcredist_x64.exe`` if using 64-bit Python, ``vcredist_x86.exe`` if
using 32-bit Python. --Quoted from the pyzbar github repo
* If the `nssm.exe` I've provided doesn't work, you can try to get one that matches your computer at http://nssm.cc/download
