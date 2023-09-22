import os
import sys
import json
import argparse
import requests
from tqdm import tqdm
from typing import List
from pathlib import Path
import requests_toolbelt
import urllib.parse as urlparse
from requests.exceptions import MissingSchema
from requests import get, ConnectionError, head

from anonupload import __version__

package_name = "anon"
url = 'https://anonymfile.com/api/v1/upload'

class ProgressBar(tqdm):
	def update_to(self, n: int) -> None:
		"""Update the bar in the way compatible with requests-toolbelt.

		This is identical to tqdm.update, except ``n`` will be the current
		value - not the delta as tqdm expects.
		"""
		self.update(n - self.n)  # will also do self.n = n

def upload(filename):

	data_to_send = []
	session = requests.session()

	with open(filename, "rb") as fp:
		data_to_send.append(
			("file", (os.path.basename(filename), fp))
		)
		encoder = requests_toolbelt.MultipartEncoder(data_to_send)
		with ProgressBar(
			total=encoder.len,
			unit="B",
			unit_scale=True,
			unit_divisor=1024,
			miniters=1,
			file=sys.stdout,
		) as bar:
			monitor = requests_toolbelt.MultipartEncoderMonitor(
				encoder, lambda monitor: bar.update_to(monitor.bytes_read)
			)

			r = session.post(
				url,
				data=monitor,
				allow_redirects=False,
				headers={"Content-Type": monitor.content_type},
			)

	resp = json.loads(r.text)
	if resp['status']:
		urlshort = resp['data']['file']['url']['short']
		urllong = resp['data']['file']['url']['full']
		print(f'[SUCCESS]: Your file has been succesfully uploaded:\nFull URL: {urllong}\nShort URL: {urlshort}')
		with open('urls.txt', 'a+') as f:
			f.write(f"{urllong}\n")
		print('url saved in urls.txt file')
		return urlshort, urllong
	else:
		message = resp['error']['message']
		errtype = resp['error']['type']
		print(f'[ERROR]: {message}\n{errtype}')
		return message, errtype

def changefile_and_upload(filenames: List[str]):
	for filename in filenames:
		if os.path.isdir(filename):
			print('[ERROR] You cannot upload a directory!')
			break
		else:
			yes = {'yes','y','ye',''}
			choice = input(f"Do you want change filename {filename} [Y/n]: ").lower()
			if choice in yes:
				input_name = input("Enter new file name with extension: ")
				try:
					os.rename(filename, input_name)
				except FileNotFoundError:
					print(f'[ERROR]: The file "{filename}" doesn\'t exist!')
					break

				try:
					files = {'file': (open(input_name, 'rb'))}
				except FileNotFoundError:
					print(f'[ERROR]: The file "{input_name}" doesn\'t exist!')
					break
			else:
				try:
					files = {'file': (open(filename, 'rb'))}
				except FileNotFoundError:
					print(f'[ERROR]: The file "{filename}" doesn\'t exist!')
					break

		if (os.path.isfile(filename)==False):
			print("[UPLOADING]: ", input_name)
			filename = input_name
		else:
			print("[UPLOADING]: ", filename)
		
		upload(filename)
	

def filename_from_url(url):
    fname = os.path.basename(urlparse.urlparse(url).path)
    if len(fname.strip(" \n\t.")) == 0:
        return None
    return fname

def filename_from_headers(headers):
    if type(headers) == str:
        headers = headers.splitlines()
    if type(headers) == list:
        headers = dict([x.split(':', 1) for x in headers])
    cdisp = headers.get("Content-Disposition")
    if not cdisp:
        return None
    cdtype = cdisp.split(';')
    if len(cdtype) == 1:
        return None
    if cdtype[0].strip().lower() not in ('inline', 'attachment'):
        return None
    # several filename params is illegal, but just in case
    fnames = [x for x in cdtype[1:] if x.strip().startswith('filename=')]
    if len(fnames) > 1:
        return None
    name = fnames[0].split('=')[1].strip(' \t"')
    name = os.path.basename(name)
    if not name:
        return None
    return name

def detect_filename(url=None, headers=None):
    names = dict(out='', url='', headers='')
    if url:
        names["url"] = filename_from_url(url) or ''
    if headers:
        names["headers"] = filename_from_headers(headers) or ''
    return names["out"] or names["headers"] or names["url"]

def remove_file(filename: Path):
	try:
		os.remove(filename)
	except FileNotFoundError:
		print(f'[ERROR]: The file "{filename}" doesn\'t exist!')

def download(url: str, custom_filename: str=None, path: Path=Path.cwd(), delete: bool=False):
	try:
		filesize = int(head(url).headers["Content-Length"])
	except ConnectionError:
		print("[Error]: No internet")
		return 1
	except MissingSchema as e:
		sys.exit(str(e))
	except KeyError:
		filesize = None

	if not os.path.isdir(path):
		os.mkdir(path)
	
	if custom_filename == None:
		filename = detect_filename(url, head(url).headers)
		full_filename = os.path.join(path, filename)
	else:
		filename = custom_filename
		full_filename = os.path.join(path, filename)
	
	chunk_size = 1024

	try:
		with get(url, stream=True) as r, open(full_filename, "wb") as f, tqdm(
				unit="B",  # unit string to be displayed.
				unit_scale=True,  # let tqdm to determine the scale in kilo, mega..etc.
				unit_divisor=1024,  # is used when unit_scale is true
				total=filesize,  # the total iteration.
				file=sys.stdout,  # default goes to stderr, this is the display on console.
				desc=filename  # prefix to be displayed on progress bar.
		) as progress:
			for chunk in r.iter_content(chunk_size=chunk_size):
				datasize = f.write(chunk)
				progress.update(datasize)
	except ConnectionError:
		return 1

	first_msg, second_msg = upload(full_filename)
	if delete:
		remove_file(full_filename)
	return first_msg, second_msg

def downloads(urls: List[str], path: Path=Path.cwd(), delete: bool=False):
	for url in urls:
		download(url=url, path=path, delete=delete)
	
example_uses = '''example:
   anon up {files_name}
   anon d {urls}'''

def main(argv = None):
	parser = argparse.ArgumentParser(prog=package_name, description="upload your files on anonfile server", epilog=example_uses, formatter_class=argparse.RawDescriptionHelpFormatter)
	subparsers = parser.add_subparsers(dest="command")

	upload_parser = subparsers.add_parser("up", help="upload files to https://anonfiles.com")
	upload_parser.add_argument("filename", type=str, nargs='+', help="one or more files to upload")

	download_parser = subparsers.add_parser("d", help="download files and upload directly to anonfiles")
	download_parser.add_argument("filename", nargs='+', type=str, help="one or more URLs to download")
	download_parser.add_argument('-p', '--path', type=Path, default=Path.cwd(), help="download directory (CWD by default)")
	download_parser.add_argument('-del', '--delete', action="store_true", dest="delete", help="Delete file after upload, default : Falses")

	parser.add_argument('-v',"--version", action="store_true", dest="version", help="check version of anonupload")

	args = parser.parse_args(argv)

	if args.command == "up":
		return changefile_and_upload(args.filename)
	elif args.command == "d":
		return downloads(args.filename, args.path, args.delete)
	elif args.version:
		return print(__version__)
	else:
		parser.print_help()

if __name__ == '__main__':
	raise SystemExit(main())
