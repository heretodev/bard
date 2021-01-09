"""lsblk -J -o partuuid,ptuuid,uuid,mountpoint 
{
   "blockdevices": [
      {"partuuid":null, "ptuuid":"a8f29cb0-41f9-407b-98a7-16282c660d1b", "uuid":null, "mountpoint":null},
      {"partuuid":"3f322a36-9af4-45f8-b388-2fa39ba8b4d3", "ptuuid":"a8f29cb0-41f9-407b-98a7-16282c660d1b", "uuid":"7A41C01172156B5D", "mountpoint":null},
      {"partuuid":"c5e927bd-6dba-4811-b0e5-d1ff47217ee0", "ptuuid":"a8f29cb0-41f9-407b-98a7-16282c660d1b", "uuid":"3085a646-b317-4c23-98a9-266817d9b166", "mountpoint":"/home"},
      {"partuuid":null, "ptuuid":"c38ecfa0-05a2-4d7f-95ff-72de392ab6c3", "uuid":null, "mountpoint":null},
      {"partuuid":"fcce2cc5-e585-41a5-938a-bd44acda3011", "ptuuid":"c38ecfa0-05a2-4d7f-95ff-72de392ab6c3", "uuid":"A62C250B2C24D857", "mountpoint":null},
      {"partuuid":"4f647ee6-af4e-461e-b3e8-efe8ce522ce6", "ptuuid":"c38ecfa0-05a2-4d7f-95ff-72de392ab6c3", "uuid":"AC27-58ED", "mountpoint":"/boot/efi"},
      {"partuuid":"ad82efac-45af-457d-ba82-c5330eef8538", "ptuuid":"c38ecfa0-05a2-4d7f-95ff-72de392ab6c3", "uuid":null, "mountpoint":null},
      {"partuuid":"a8b62a0e-4f46-44ed-a4ae-16368e84c5ae", "ptuuid":"c38ecfa0-05a2-4d7f-95ff-72de392ab6c3", "uuid":"90162E23162E0AB4", "mountpoint":null},
      {"partuuid":"b06266c6-6f2d-4992-9868-bc0b5a95de6b", "ptuuid":"c38ecfa0-05a2-4d7f-95ff-72de392ab6c3", "uuid":"bd85f7e0-a1b0-4b97-be24-34d025b626d3", "mountpoint":"/"},
      {"partuuid":"9cf1d5cc-5198-4dfd-b05a-ce9db0411399", "ptuuid":"c38ecfa0-05a2-4d7f-95ff-72de392ab6c3", "uuid":"f5e827ec-6c8f-411e-bcd9-31c54e8383be", "mountpoint":"[SWAP]"},
      {"partuuid":null, "ptuuid":null, "uuid":null, "mountpoint":null}
   ]
}

    \\?\Volume{3f322a36-9af4-45f8-b388-2fa39ba8b4d3}\
	D:\

    \\?\Volume{fcce2cc5-e585-41a5-938a-bd44acda3011}\
	*** NO MOUNT POINTS ***

    \\?\Volume{a8b62a0e-4f46-44ed-a4ae-16368e84c5ae}\
	C:\

    \\?\Volume{4f647ee6-af4e-461e-b3e8-efe8ce522ce6}\
	*** NO MOUNT POINTS ***

    \\?\Volume{fd37600c-4440-11ea-bf0e-806e6f6e6963}\
	F:\
"""

import subprocess
import platform
import os,os.path

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
					v='unknown:'+urllib.parse.quote_plus(v)
				mapout[k]=v
			
		return mapout

	def device_from_path(path):
		global _mapping
		if(_mapping==None):
			_mapping=_getmapping()
		path=os.path.abspath(path)
		drive,pth=os.path.splitdrive(path)
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
			
		#TODO: do all fstab to do network mountings and ssh mountings
		return sorted(list(mapout.items()),key=lambda x: len(x[0]),reverse=True)

	def device_from_path(path):
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
			return None,path
else:
	raise NotImplementedError
#elif(pform == 'Darwin'):
 #   raise Exception("MacOSX not supported for partuuid")
    #$ diskutil info /dev/disk0s2 | egrep -om1 "([A-Z0-9]{8}.[A-Z0-9]{4}.+$)"

if(__name__=='__main__'):
	import sys
	print(device_from_path(sys.argv[1]))

