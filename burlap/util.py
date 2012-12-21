import hashlib
import os
import time

from fabric.api import *

def _md5_for_file(path, block_size=2**20):
  md5 = hashlib.md5()
  with open(path,'r') as f:
    while True:
      data = f.read(block_size)
      if not data:
        break
      md5.update(data)
    return md5.hexdigest()

def md5_for_file(path, block_size=2**2):
  key = path + "_md5"
  if not key in env:
    env[key] = _md5_for_file(path, block_size)

  return env[key]


def initd_control(script, cmd):
  if cmd == "status":
    run("/etc/init.d/%s status" % script)
  else:
    sudo("/etc/init.d/%s %s" % (script, cmd))

def run_cmd(cmd):
  run(cmd)

def sudo_cmd(cmd):
  sudo(cmd)

def file_exists(path):
  with settings(warn_only=True):
    return not run("test -f %s" % path).return_code

def dir_exists(path):
  with settings(warn_only=True):
    return not run("test -d %s" % path).return_code

def _perms(cmd, path, setting, recursive=False, use_sudo=False):
  run_func = sudo if use_sudo else run
  if recursive:
    run_func("%s -R %s %s" % (cmd, setting, path))
  else:
    run_func("%s %s %s" % (cmd, setting, path))

def chown(path, owner, recursive=False, use_sudo=False):
  _perms("chown", path, owner, recursive, use_sudo)

def chgrp(path, group, recursive=False, use_sudo=False):
  _perms("chgrp", path, group, recursive, use_sudo)

def chmod(path, permissions, recursive=False, use_sudo=False):
  _perms("chmod", path, permissions, recursive, use_sudo)

def path_props(path, owner=None, group=None, permissions=None, recursive=False, use_sudo=False):
  if owner:
    chown(path, owner, recursive, use_sudo)
  
  if group:
    chgrp(path, group, recursive, use_sudo)

  if permissions:
    chgrp(path, permissions, recursive, use_sudo)


def mv(src, dest, use_sudo=False):
  run_func = sudo if use_sudo else run
  run_func("mv %s %s" % (src, dest))

# kwargs owner, group, permissions
def alt_put(src_file, destination, use_sudo=False, remote_tmp="/tmp", **kwargs):
  md5 = md5_for_file(src_file)
  basename = os.path.basename(src_file)
  remote_name = remote_tmp + "/" + md5
  put(src_file, remote_name)
  
  final_destination = None

  if file_exists(destination):
    bkup_name = destination + "." + str(int(time.time()))
    final_destination = destination
    print "backing up original file"
    mv(destination, bkup_name, use_sudo)
    mv(remote_name, destination, use_sudo)
  elif dir_exists(destination):
    final_destination = destination + "/" + basename
    mv(remote_name, final_destination, use_sudo)
  else:
    final_destination = destination
    mv(remote_name, destination, use_sudo)

  file_properties = {k: kwargs[k] if k in kwargs else None for k in ('owner', 'group', 'permissions')}
  path_props(final_destination, use_sudo=use_sudo, **file_properties)
