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
## From a fresh Windows computer (overly detailed)
0. Install git https://git-scm.com/download/win
1. Install Python 3.6.2 https://www.python.org/downloads/release/python-362/. Pip will come with it.
2. `pip install -r requirements.txt`
3. `cp example_config.json config.json` using Powershell, and fill it out. (You should have a Postgres user with at least read access). (VPC should have IP added to whitelist).
4. Install AWS CLI https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-windows.html
5. `aws configure` with `Default region name` as `us-west-2` and `Output format` `None`. (You should have an AWS IAM user with the following policies):
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
6. `python main.py`
7. Follow the steps while running PowerShell as administrator: https://gist.github.com/guillaumevincent/d8d94a0a44a7ec13def7f96bfb713d3f. As of January 2021, doesn't work with Python 3.9 so that's why we have to use 3.6.2
8. Windows Button > Services > `Giraffe Uploader Service` > `Properties` > `Startup type` > Change from `Manual` to `Automatic`
9. Update Windows Power settings so takes longer to fall asleep (or not at all). 

* Hints: Windows PowerShell will make your life easier if you're coming from Linux/Mac. Also, on Windows you have to open a new command prompt/shell after installing a CLI application for it to recognize it in path.
* If you see an ugly ``ImportError`` when importing ``pyzbar`` on Windows
you will most likely need the `Visual C++ Redistributable Packages for Visual
Studio 2013
<https://www.microsoft.com/en-US/download/details.aspx?id=40784>`. Install ``vcredist_x64.exe`` if using 64-bit Python, ``vcredist_x86.exe`` if
using 32-bit Python. --Quoted from the pyzbar github repo

# Other
Get the python path:
```
python get_path_to_python.py
```
Install 
```
.\nssm install PythonGiraffeService "C:\Users\russe\AppData\Local\Programs\Python\Python36\python.exe" "C:\Users\russe\Desktop\code\greenhouse-giraffe-uploader\main.py"
```

Set outputs to a log file:
```
.\nssm set PythonGiraffeService AppStdout C:\Users\russe\Desktop\code\greenhouse-giraffe-uploader\service.log
```
```
.\nssm set PythonGiraffeService AppStderr C:\Users\russe\Desktop\code\greenhouse-giraffe-uploader\service-error.log
```
