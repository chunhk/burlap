from fabric.api import *
from fabric.contrib import files

from burlap.util import *

DEFAULT_APT_PATH = "/etc/apt/sources.list.d"

def check_apt_repo(apt_repo_file):
  return files.exists(DEFAULT_APT_PATH + "/" + apt_repo_file)

def check_apt_repo_task(apt_repo_file):
  if check_apt_repo(apt_repo_file):
    print "apt repo %s exists" % apt_repo_file
  else:
    print "apt repo %s does not exist" % apt_repo_file

def install_apt_repo(apt_repo_file):
  remote_file = DEFAULT_APT_PATH + "/" + apt_repo_file
  alt_put("resources/" + apt_repo_file, remote_file, use_sudo=True, owner="root", group="root")
  apt_update()

def add_apt_repository(repo, auto=True):
  if auto:
    sudo("add-apt-repository -y %s" % repo)
  else:
    sudo("add-apt-repository %s" % repo)

def apt_update():
  sudo("apt-get update")

def apt_install(package, auto=True):
  if auto:
    sudo("apt-get install -y %s" % package)
  else:
    sudo("apt-get install %s" % package)

