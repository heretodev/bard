import os,os.path
import datetime
import platform
import json

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
"""

pform=platform.system()
mount2uuid={}
if(pform=='Linux'):
	def _get_all_uuids():
		presult=subprocess.run(["lsblk","-J","-o","partuuid,ptuuid,uuid,mountpoint"],capture_output=True,check=True)
		jresult=json.loads(presult.stdout)
		for 

def _canonical
	pass

def compute_modtuple(path):
	pass

def compute_modhash(path):
	canonical_device_id=""#TODO: identify_hard_drive_hardware_device_identifier #bard/path_identifier.py ...the windows code isn't finished but I rmemeber it was possible to find one that worked cross platform.
	canonical_path_in_device = path  #(but remove any leading prefix like "C:" or "/media/steven" and also turn all "\" into "/"]
	mtime = os.path.getmtime(path)
	mtime_utc = datetime.datetime.utcfromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
	modstr = canonical_device_id+"|"+canonical_path_in_device+"|"+mtime_utc
	modhash = bard.hash.secure_hash(modstr.encode('utf-8'))
	return modhash
