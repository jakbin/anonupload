import argparse
from pathlib import Path

from anonupload import __version__
from anonupload.main import multi_upload, downloads
from anonupload.config import setup_config, load_config

package_name = "anon"

config = load_config()
if config['custom_url']:
	url = config['custom_url']
else:
	url = 'https://anonymfile.com/api/v1/upload'

example_uses = '''example:
   anon up {files_name}
   anon d {urls}'''

def main(argv = None):
	parser = argparse.ArgumentParser(prog=package_name, description="upload your files on anonfile server", epilog=example_uses, formatter_class=argparse.RawDescriptionHelpFormatter)
	subparsers = parser.add_subparsers(dest="command")

	setup_parser = subparsers.add_parser("setup", help="setup custom url")
	setup_parser.add_argument("url", type=str, help="custom url to upload files")  

	upload_parser = subparsers.add_parser("up", help="upload files to")
	upload_parser.add_argument("files", type=str, nargs='+', help="one or more files to upload")
	# upload_parser.add_argument('-ex', '--expiry', type=str, default=None, help="Time to expire file. Like :- 3m, 2h, 4d, 1w, 2M, 1y etc.")

	download_parser = subparsers.add_parser("d", help="download files and upload directly to anonfiles")
	download_parser.add_argument("files", nargs='+', type=str, help="one or more URLs to download")
	download_parser.add_argument('-p', '--path', type=Path, default=Path.cwd(), help="download directory (CWD by default)")
	download_parser.add_argument('-del', '--delete', action="store_true", dest="delete", help="Delete file after upload, default : False")

	parser.add_argument('-v',"--version", action="store_true", dest="version", help="check version of anonupload")

	args = parser.parse_args(argv)

	if args.command == "setup":
		setup_config(args.url)
	elif args.command == "up":
		# return changefile_and_upload(args.files, args.expiry)
		if args.expiry == None:
			multi_upload(url, args.files, verbose=True)
		else:
			ex_url = f'{url}/?expires={args.expiry}'
			multi_upload(ex_url, args.files, verbose=True)
	elif args.command == "d":
		return downloads(args.files, url,  args.path, args.delete)
	elif args.version:
		return print(__version__)
	else:
		parser.print_help()

if __name__ == '__main__':
	raise SystemExit(main())
