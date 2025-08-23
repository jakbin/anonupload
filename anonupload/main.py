import os
import sys
import json
import requests
from tqdm import tqdm
from typing import List
from pathlib import Path
import requests_toolbelt
import urllib.parse as urlparse
from requests.exceptions import MissingSchema
from requests import get, ConnectionError, head

from anonupload import __version__


class ProgressBar(tqdm):
	def update_to(self, n: int) -> None:
		"""Update the bar in the way compatible with requests-toolbelt.

		This is identical to tqdm.update, except ``n`` will be the current
		value - not the delta as tqdm expects.
		"""
		self.update(n - self.n)  # will also do self.n = n

def upload(url: str, filename: str, verbose: bool=False):

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

	try:
		resp = json.loads(r.text)

		if resp['status']:
			urlshort = resp['data']['file']['url']['short']
			urlfull = resp['data']['file']['url']['full']
			if verbose:
				print(f'[SUCCESS] Short URL: {urlshort}\nFull URL: {urlfull}')
				with open('urls.txt', 'a+') as f:
					f.write(f"{urlshort}\n")
				print('url saved in urls.txt file')
			return urlshort
		else:
			error = resp['error']
			message = resp['message']
			if verbose:
				print(f'[ERROR]: {error}\n{message}')
			return message
	except json.decoder.JSONDecodeError:
		if verbose:
			print(f'[ERROR]: {r.text}')
		return r.text
	except KeyError:
		if verbose:
			print(r.text)
		return r.text
	except ConnectionError:
		if verbose:
			print("[Error]: No internet")
		return "[Error]: No internet"

def multi_upload(url: str, filenames: List[str], verbose: bool=False):
	for filename in filenames:
		res = upload(url, filename, verbose)
		print(res)

def changefile_and_upload(filenames: List[str], expiry: str):
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

		if expiry == None:
			url = 'https://file.io'
			upload(url, filename)
		else:
			url = f'https://file.io/?expires={expiry}'
			upload(url, filename)
	

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

def download(url: str, custom_filename: str=None, path: Path=Path.cwd()):
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
		return 0

	return full_filename

def download_and_upload(url: str, server_url: str, custom_filename: str=None, path: Path=Path.cwd(), delete: bool=False):
	full_filename = download(url=url, custom_filename=custom_filename, path=path)
	res_url = upload(server_url, full_filename, verbose=True)
	if delete:
		remove_file(full_filename)
	return res_url

def downloads(urls: List[str], server_url: str, path: Path=Path.cwd(), delete: bool=False):
	for url in urls:
		res_url = download_and_upload(url=url, server_url=server_url, path=path, delete=delete)
		print(res_url)
