# greenhouse-giraffe-uploader
* For use on Windows
* Put the images in the `unprocesssed_dir`. They cannot be in subfolders.
* Important: Relies on the fact that the file creation timestamp in the Windows filesystem has millisecond (and microsecond) granularity. This chronology helps distinguish adjacent images which might be stitched together in the future.

# Installation 
## From a fresh Windows computer (overly detailed)
0. Install git https://git-scm.com/download/win
1. Install Python 3.9 from the Microsoft Store (just type Python in the Windows search bar). Pip will come with it.
2. `pip install -r requirements.txt`
3. `cp example_config.json config.json` using Powershell, and fill it out.
4. Install AWS CLI https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-windows.html
5. `aws configure` (You should have an AWS IAM user with the following policies):
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

If you see an ugly ``ImportError`` when importing ``pyzbar`` on Windows
you will most likely need the `Visual C++ Redistributable Packages for Visual
Studio 2013
<https://www.microsoft.com/en-US/download/details.aspx?id=40784>`__.
Install ``vcredist_x64.exe`` if using 64-bit Python, ``vcredist_x86.exe`` if
using 32-bit Python.