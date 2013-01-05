import hashlib
import os
import time

from fabric.api import *
from jinja2.environment import Template


def initd_control(script, cmd):
  if cmd == "status":
    run("/etc/init.d/%s status" % script)
  else:
    sudo("/etc/init.d/%s %s" % (script, cmd))


def upstart_control(service, cmd):
  if cmd == "status":
    run("status %s" % service)
  else:
    sudo("%s %s" % (cmd, service))


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
    chmod(path, permissions, recursive, use_sudo)


def mv(src, dest, use_sudo=False):
  run_func = sudo if use_sudo else run
  run_func("mv %s %s" % (src, dest))


def tar_top_level_dir(tar_file):
  return run("tar -tf %s | grep -o '^[^/]\+' | sort -u" % tar_file)


def http_get(url, dest_file, use_sudo=False):
  cmd = "wget %s -O %s"
  run_func = sudo if use_sudo else run
  run_func(cmd % (url, dest_file))


# kwargs owner, group, permissions
def remote_file(src_file, dest_file, use_sudo=False, \
    tmp_dir="/tmp", **kwargs):

  basename = os.path.basename(src_file)

  if src_file.startswith("http://") or src_file.startswith("https://"):
    md5 = string_md5(src_file)
    remote_name = tmp_dir + "/" + md5
    http_get(url=src_file, dest_file=remote_name, use_sudo=use_sudo)
  else:
    md5 = file_md5(src_file)
    remote_name = tmp_dir + "/" + md5
    put(src_file, remote_name)

  final_destination = None

  if file_exists(dest_file):
    bkup_name = dest_file + "." + str(int(time.time()))
    final_destination = dest_file
    print "backing up original file"
    mv(dest_file, bkup_name, use_sudo)
    chmod(bkup_name, "a-x")
    mv(remote_name, dest_file, use_sudo)
  elif dir_exists(dest_file):
    final_destination = dest_file + "/" + basename
    mv(remote_name, final_destination, use_sudo)
  else:
    final_destination = dest_file
    mv(remote_name, dest_file, use_sudo)

  file_properties = {k: kwargs[k] if k in kwargs else None \
      for k in ('owner', 'group', 'permissions')}
  path_props(final_destination, use_sudo=use_sudo, **file_properties)


def remote_archive(src_file, dest_path, use_sudo=False, \
    tmp_dir="/tmp", **kwargs):

  basename = os.path.basename(src_file)
  remote_name = tmp_dir + "/" + basename

  remote_file(src_file, remote_name, use_sudo=use_sudo, tmp_dir=tmp_dir)
  run_func = sudo if use_sudo else run

  if basename.endswith("tar.gz") or basename.endswith(".tgz") or \
      basename.endswith(".tar"): 
    if dir_exists(dest_path) or file_exists(dest_path):
      raise RuntimeError("destination path already exists: " + dest_path)
    else:
      run_func("mkdir %s" % dest_path)
      run_func("tar --strip-components 1 -xf %s -C %s" % \
          (remote_name, dest_path))
  else:
    raise NotImplementedError("file format not supported: " + basename)

  file_properties = {k: kwargs[k] if k in kwargs else None \
      for k in ('owner', 'group', 'permissions')}
  path_props(dest_path, use_sudo=use_sudo, recursive=True, \
      **file_properties)


def run_remote_file(src_file, dest_file=None, use_sudo=False, \
    tmp_dir="/tmp"):

  if not dest_file:
    dest_file = tmp_dir + "/" + string_md5(template_file + str(variables))

  remote_file(src_file, dest_file, use_sudo=use_sudo)
  chmod(dest_file, permissions="+x", use_sudo=use_sudo)

  if use_sudo:
    sudo(dest_file)
  else:
    run(dest_file)


def remote_template(template_file, variables, dest_file, \
    use_sudo=False, **kwargs):

  with open(template_file, 'r') as f:
    template_content = f.read()

  template = Template(template_content)
  content = template.render(**variables)
  local_file = "/tmp/" + string_md5(content) + ".template"

  with open(local_file, 'w') as f:
    f.write(content)

  remote_file(local_file, dest_file, use_sudo=use_sudo, **kwargs)
  local("rm %s" % local_file)

  
def run_remote_template(template_file, variables, dest_file=None, \
    use_sudo=False, **kwargs):

  if not dest_file:
    dest_file = "/tmp/" + string_md5(template_file + str(variables))

  remote_template(template_file, variables, dest_file, use_sudo, **kwargs)
  chmod(dest_file, permissions="+x", use_sudo=use_sudo)

  if use_sudo:
    sudo(dest_file)
  else:
    run(dest_file)


def env_var(var):
  return run("echo %s" % var)


def home_path():
  return env_var("$HOME")


def string_md5(s):
  h = hashlib.md5()
  h.update(s)
  return h.hexdigest()


def _file_md5(path, block_size=2**20):
  md5 = hashlib.md5()
  with open(path,'r') as f:
    while True:
      data = f.read(block_size)
      if not data:
        break
      md5.update(data)
    return md5.hexdigest()


def file_md5(path, block_size=2**2):
  key = path + "_md5"
  if not key in env:
    env[key] = _file_md5(path, block_size)

  return env[key]
