#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 19 20:08:39 2025

@author: ciko
"""

import os
import sys
import subprocess
import random
import shutil
import time
from waldur_api_client.api.users import users_me_retrieve
from waldur_api_client import AuthenticatedClient
from waldur_api_client.api.keys import keys_create, keys_list
from waldur_api_client.api.marketplace_offering_users import marketplace_offering_users_list
import configparser
# from waldur_api_client.types import Response

config_params = configparser.ConfigParser()

# Read the config file
config_params.read('config.ini')

waldur_host = config_params.get('General', 'waldur_host')
login_node = config_params.get('General', 'login_node')
offering_uuid = config_params.get('General', 'offering_id')

print(f"Copy API token from WALDUR ({waldur_host}) user Deshboard")
api_token = input("ENTER API token:").strip()
client = AuthenticatedClient(base_url=waldur_host, token=api_token)

homedir=os.environ.get("HOME")
pub_key = f"{homedir}/.ssh/id_rsa"
# pub_key = "./id_rsa"

class Color:
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'

def print_separator(symbol='#'):
    width = shutil.get_terminal_size().columns
    print("\n" + symbol * width)

def get_my_user_id(client):
    
    try:
        me = users_me_retrieve.sync(client=client)
    except Exception as e:
        print("An error occurred: ", e)
        sys.exit(0)
        # print(me.uuid)
    
    return me.uuid

def get_my_cluster_login(client,user_uuid,offering_uuid):

    remote_accounts = marketplace_offering_users_list.sync(
            
        client=client,
        user_uuid=user_uuid,
        offering_uuid=[offering_uuid],
        
    )
    # print(remote_accounts)
    if remote_accounts:
        cluster_account = remote_accounts[0].username
    else:
        cluster_account = ''
    
    return cluster_account

def list_my_waldur_keys(client, user_uuid):
    waldur_keys = []
    keys = keys_list.sync(client=client,user_uuid=user_uuid)
    print("\nKeys uploaded to waldur:")
    for k in keys:
        print(k.name, k.fingerprint_sha256)
        waldur_keys.append(k.fingerprint_sha256)
    
    return waldur_keys
        
def upload_my_public_key(client, pub_key, name='my-ssh-key'):
    from waldur_api_client.models import SshKey
    # The public_key should be the content of your `id_rsa.pub` (or other .pub file)
    public_key_str = open(pub_key+".pub").read().strip()

    req = SshKey(
        name=name,
        public_key=public_key_str
    )

    resp = keys_create.sync(client=client, body=req)
    print(resp)



def get_local_key_fingerpint(pub_key):
    
    line = subprocess.check_output(
        ["ssh-keygen", "-lf", pub_key+".pub"],
        text=True
    ).strip()
    key_name = line.split()[2]
    fingerprint = line.split()[1]
    print("\nLocal key:", fingerprint)
    print("Local key name:", key_name, "\n")
    
    return fingerprint, key_name

def generate_new_key(key_path):
    
    subprocess.run([
            "ssh-keygen",
            "-t", "rsa",
            "-b", "4096",
            "-f", key_path,
            "-N", ""
            ], check=True)
    
    print("Key generated at:", key_path)

def create_desktop_file(username, login_node, path):
    content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=SSH to HPC ({username})
Comment=
Exec=ssh -X {username}@{login_node}
Icon=org.gnome.Terminal
Path=
Terminal=true
StartupNotify=false
"""

    with open(path, "w") as f:
        f.write(content)
    
    os.chmod(path, 0o755)

def is_mounted(path):
    return subprocess.run(
        ["mountpoint", "-q", path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    ).returncode == 0


def mount_HPC_folder(username,login_node, mount_dir):

    print("Mounting cluster directory on your Desktop...")
    os.makedirs(mount_dir, exist_ok=True)

    try:
        if not is_mounted(mount_dir):
            print(f"Mounting cluster directory to {mount_dir}")
            subprocess.run([
                "sshfs",
                f"{username}@{login_node}:",
                mount_dir,
                "-o", "nonempty,reconnect"
            ], check=True)
    
        else:
            print("Cluster directory already mounted")
    except:
        print("SSH mount not supported")
        

def passwordless_ssh_ok(username, host):
    result = subprocess.run(
        [
            "ssh",
            #"-v",
            #"-i /home/user/.ssh/id_rsa",
            "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=5",
            f"{username}@{host}",
            "true"
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    # print(result)
    return result.returncode == 0
    

def main():
    
    user_uuid = get_my_user_id(client)
    
    login_name = get_my_cluster_login(client,user_uuid,offering_uuid)
    if not login_name:
        
        print(f"\nYou don't have account on RUDENS.\nPlease request an allocation through WALDUR Marketplace!!!\n")
        print(f"\nPublic key not uploaded\n")
        sys.exit(0)
        
    waldur_keys = list_my_waldur_keys(client, user_uuid)
    
    if os.path.exists(pub_key):
        fingerprint, key_name = get_local_key_fingerpint(pub_key)
    else:
        generate_new_key(pub_key)
        fingerprint, key_name = get_local_key_fingerpint(pub_key)

    if fingerprint in waldur_keys:
        print(f"Public key ({key_name}) exists in WALDUR")
    else:
        
        new_key_name = key_name + "-" + str(random.randint(0, 9))
        print(f"Uploading new key {new_key_name} to WALDUR")
        upload_my_public_key(client, pub_key, name=new_key_name)
        
        
    
    
    desktop_filepath=f"{homedir}/Desktop/ssh-hpc.desktop"
    
    if os.path.exists(desktop_filepath):
        print(f"\nDesktop icon exists. To re-generate - DELETE {desktop_filepath}")
    else:
        create_desktop_file(login_name, login_node, desktop_filepath)
    
    desktop_share_filepath=f"{homedir}/Desktop/HPC data"

    k = 0
    while not passwordless_ssh_ok(login_name, login_node):
        print("Synhronizing your SSH key with HPC cluster. Please wait...")
        time.sleep(20)
        k += 1
        if k > 300/20:
            print("Problem synhronizing the key. Please re-try configuration scricpt later.")
            sys.exit(0)

    
    mount_HPC_folder(login_name, login_node, desktop_share_filepath)
    print("HPC connection ready!!!")
    
    time.sleep(1)    
    print_separator()   
    print(f"\nYour cluster login name: {Color.RED}{login_name}{Color.RESET}")
    
    print("\nConnect to the cluster by:")
    print(f"{Color.RED}1. clicking on 'SSH to HPC' on the Desktop or")
    print(f"2. executing in Terminal: ssh {login_name}@{login_node}{Color.RESET}")
    
    print_separator()   

    
if __name__ == "__main__":
    main()
    
    
