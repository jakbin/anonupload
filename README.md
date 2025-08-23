# 📁 anonfiles-script

🚀 An python tool to upload file to anonymus sever. Supports multiple files.

 [![Publish package](https://github.com/jakbin/anonupload/actions/workflows/publish.yml/badge.svg)](https://github.com/jakbin/anonupload/actions/workflows/publish.yml)
 [![PyPI version](https://badge.fury.io/py/anonupload.svg)](https://pypi.org/project/anonupload/)
 [![Downloads](https://pepy.tech/badge/anonupload/month)](https://pepy.tech/project/anonupload)
 [![Downloads](https://static.pepy.tech/personalized-badge/anonupload?period=total&units=international_system&left_color=green&right_color=blue&left_text=Total%20Downloads)](https://pepy.tech/project/anonupload)
 ![GitHub Contributors](https://img.shields.io/github/contributors/jakbin/anonupload)
 ![GitHub commit activity](https://img.shields.io/github/commit-activity/m/jakbin/anonupload)
 ![GitHub last commit](https://img.shields.io/github/last-commit/jakbin/anonupload)
 ![Python 3.6](https://img.shields.io/badge/python-3.6-yellow.svg)


## ✨ Features
- 📊 Progress bar for upload/download tracking
- 💾 Upload URLs are automatically saved to a file
- 🏷️ Rename files before uploading to server
- 📦 Support for multiple file uploads
- ⬇️ Direct download functionality


## 🚀 Installation

```sh
pip3 install anonupload
```

## 💻 Usage 
```sh
anon up {path-to-file_1} {path-to-file_2} ...  # 📤 upload files to anonfile server
anon d {url1} {url2} ...                       # 📥 download and upload directly to anonfiles 
```

# 🔧 API Reference

The anonupload client provides a comprehensive API for programmatic file upload and download operations.


### anonupload.upload(filename)

```py
from anonupload import upload

upload(filename)
```

```py
from anonupload import changefile_and_upload
changefile_and_upload([file1, file2])
```

### anonupload.download(url)

```py
from anonupload import download

download(url)
```

### anonupload.downloads([url1, url2])

```py
from anonupload import downloads

downloads([url1, url2])
```