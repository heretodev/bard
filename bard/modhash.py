import subprocess
import platform
import os,os.path
import datetime
import bard.hash

pform = platform.system()

def _call(args):
	return subprocess.run(args,text=True,check=True,capture_output=True).stdout


_mapping=None

if(pform == 'Windows'):
	import re
	import urllib.parse
	def _getmapping():
		output=_call("mountvol")
		lines=output.splitlines()
		 
		for i,l in enumerate(lines):
			if("Possible values for" in l):
				linesout=lines[(i+1):]
			break
		else:
			return {}
		
		mapout={}
		linesout=[l.strip() for l in linesout if len(l) > 1]
		for i in range(0,len(linesout),2):
			v=linesout[i].strip()
			k=linesout[i+1].strip().strip('\\')
			if("NO MOUNT POINTS" not in k):
				m=re.search("\{([0-9a-zA-Z\-]+)\}",v)
				if(m):
					v='disk:'+m.groups(1)
				else:
					v='unc:'+urllib.parse.quote_plus(v)
				mapout[k]=v
			
		return mapout

	def _device_from_path(path):
		global _mapping
		if(_mapping==None):
			_mapping=_getmapping()
		path=os.path.abspath(path)
		drive,pth=os.path.splitdrive(path)
		pth=os.path.normpath(pth)
		pth=pth.replace('\\','/')
		if(drive in _mapping):
			return _mapping[drive],pth
		else:
			return 'unc:'+drive,pth

elif(pform == 'Linux'):
	import json
	def _getmapping():
		output=_call(["lsblk","-J","-o","partuuid,mountpoint"])
		output=json.loads(output)
		mapout={}
		for b in output["blockdevices"]:
			k=b["mountpoint"]
			v=b["partuuid"]
			if(k is not None and v is not None):
				v='disk:'+b["partuuid"]
				mapout[k]=v
		output=_call(["mount","-l"]).splitlines()
		linesout=[l.strip() for l in output]
		for l in linesout:
			mountdata=l.split()
			value=mountdata[0]
			typeof=mountdata[4]
			key=mountdata[2]
			if(typeof[:5]=='fuse.'):
				typeof=typeof[5:]
			if(typeof != value):
				value=typeof+':'+value
			if(key not in mapout):		#only if it's not mounted as a hard drive
				mapout[key]=value
			
		return sorted(list(mapout.items()),key=lambda x: len(x[0]),reverse=True)

	def _device_from_path(path):
		global _mapping
		if(_mapping==None):
			_mapping=_getmapping()
		path=os.path.abspath(path)
		for k,v in _mapping:
			ksplit=k.split(os.sep)
			psplit=path.split(os.sep)
			if(psplit[:len(ksplit)]==ksplit):
				return v,'/'+os.sep.join(psplit[len(ksplit):])
		else:
			return 'unknown',path
else:
	raise NotImplementedError
#elif(pform == 'Darwin'):
 #   raise Exception("MacOSX not supported for partuuid")
    #$ diskutil info /dev/disk0s2 | egrep -om1 "([A-Z0-9]{8}.[A-Z0-9]{4}.+$)"

def compute_modtuple(path):
	device_id,truncpath=_device_from_path(path)
	mtime=os.path.getmtime(path)
	mtime_utc = datetime.datetime.utcfromtimestamp(mtime).strftime('%Y-%m-%d.%H:%M:%S')
	return device_id,truncpath,mtime_utc

def compute_modhash(path):
	device_id,truncpath,mtime_utc=compute_modtuple(path)
	modstr = device_id+"|"+truncpath+"|"+mtime_utc
	modhash = bard.hash.secure_hash(modstr.encode('utf-8'))
	return modhash


if(__name__=='__main__'):
	import sys
	print(compute_modtuple(sys.argv[1]))



