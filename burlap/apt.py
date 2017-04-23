from fabric.api import *
from fabric.contrib import files

from burlap import util

DEFAULT_APT_PATH = "/etc/apt/sources.list.d"

class Apt:

  def __init__(self, resource_path, remote_apt_path=DEFAULT_APT_PATH):
    self.resource_path = resource_path
    self.remote_apt_path = remote_apt_path

  def check_apt_repo(self, apt_repo_file):
    return files.exists(self.remote_apt_path + "/" + apt_repo_file)

  def check_apt_repo_task(self, apt_repo_file):
    if self.check_apt_repo(apt_repo_file):
      print("apt repo %s exists" % apt_repo_file)
      return True
    else:
      print("apt repo %s does not exist" % apt_repo_file)
      return False

  def install_apt_repo(self, apt_repo_file):
    remote_file = self.remote_apt_path + "/" + apt_repo_file
    util.remote_file(self.resource_path + "/" + apt_repo_file, \
        remote_file, use_sudo=True, owner="root", group="root")
    self.apt_update()

  def add_apt_repository(self, repo, auto=True):
    if auto:
      sudo("add-apt-repository -y %s" % repo)
    else:
      sudo("add-apt-repository %s" % repo)

  def apt_update(self):
    sudo("apt-get update")

  def apt_upgrade(self):
    sudo("apt-get upgrade -y")

  def apt_install(self, package, auto=True):
    if auto:
      sudo("apt-get install -y %s" % package)
    else:
      sudo("apt-get install %s" % package)

