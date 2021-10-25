from requests import Request, Session
from glob import glob
import os
import json
import argparse
import sys
import hashlib
import shutil

def argsv_config():

    parser = argparse.ArgumentParser()
    parser.add_argument('-list_org', action='store_true', default=False, dest='list_orgs', \
            help='List organizations defined in grafana.')
    parser.add_argument('-list_dbs', action='store_true', default=False, dest='list_dashboards', \
            help='List dashboards defined in grafana.')
    parser.add_argument('-grafana_folder', action='store', default=False, dest='grafana_folder', \
            help='When used together with -restore, it defines destination grafana folder for restore. \
                        if grafana folder does not exist under given organisation, it will be created automatically.')
    parser.add_argument('-v', action='store_true', default=False, dest='verbose', \
            help='Output verbose information.')
    parser.add_argument('-backup', action='store_true', default=False, dest='backup', \
            help='Backup either all dashboards in grafana to backupfolder or dashboards \
            of a given organization.')
    parser.add_argument('-backup_folder', action='store',default='$HOME/grafana-backup/',\
            dest='backup_folder', \
            help='Backup folder for grafana dashboards. Default is $HOME/grafana-backup/')
    parser.add_argument('-restore_folder', action='store',default='',\
            dest='restore_folder', \
            help='Restore folder where grafana dashboards will be restored from.  Default is ""')
    parser.add_argument('-restore', action='store_true', default=False, dest='restore',\
            help='Restore dashboards from a backup file or folder to a given organization. requires that grafana_folder is given.')
    parser.add_argument('-org_name', action='store',dest='org_name', default="",\
            help='Organisation name where dashboards will be backed up and restored to.')
    parser.add_argument('-restore_file', action='store',dest='restore_file', default="",\
            help='Backup file from which dashboard will be restored.')
    parser.add_argument('-pwd_file', action='store',default='$HOME/.grafanapwd',dest='pwd_file',\
            help='Grafana pwd file location. It is default set to $HOME/.grafanapwd')
    parser.add_argument('-grafana_url', action='store',default='',dest='grafana_url', help='Grafana url.')
    argvs = parser.parse_args()
    return argvs

def read_pwd(pwd_file):
    #
    # Reading password file
    # password file format
    # username=<username>
    # password=<password>
    #

    try:

        if (pwd_file.startswith("$HOME")):
            pwd_file = os.getenv('HOME') + pwd_file[5:]

        if (os.path.isfile(pwd_file) and os.access(pwd_file,os.R_OK)):
            fh= open(pwd_file,'r')
            lines = fh.readlines()
            pwd=(lines.pop().strip("\n")).split("=")[1]
            user=(lines.pop().strip("\n")).split("=")[1]
        else:
            raise Exception("File doesn't exists or is not accessible!")

    except Exception as e:
        print(f'Error with reading grafanapwd file: {str(e)}')
        print("Grafana pwd file format: \nusername=<username>\npassword=<password>")
        sys.exit(1)
    return user, pwd

def create_session(grafana_url,pwd_file):
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    #proxies = {
    #        'http' : "socks5://127.0.0.1:9999",
    #        'https' : "socks5://127.0.0.1:9999"
    #    }
    user, pwd = read_pwd(pwd_file)
    session = Session()
    session.auth = (user,pwd)
    session.headers.update(headers)
    #session.proxies.update(proxies)
    return session

def connect_grafana(session,api_url,method="get",jsondata=None):

    try:
        if method=="get":
            req = Request('GET', api_url, data=jsondata)
        elif method=="post":
            req = Request('POST', api_url, data=jsondata)

        prepped = session.prepare_request(req)

        resp = session.send(prepped)
    except:
        print(resp)
        print("Error with connection grafana.")
        sys.exit(1)

    return resp

def change_current_org(session, grafana_url, change_org_api, org_id):
    change_org_url = grafana_url + change_org_api + str(org_id)
    resp = connect_grafana(session, change_org_url, method="post")

def get_organizations(session,grafana_url,org_api):
    org_dict = {}
    org_url = grafana_url + org_api
    jsondata = connect_grafana(session,org_url).json()
    for data in jsondata:
        if (data['name'] not in org_dict):
            org_dict[data['name']] = data['id']
    return org_dict

def list_organizations(org_dict):
    for org in org_dict.keys():
        print(org)

def get_dashboard_settings(session, grafana_url, db_settings_api, uid):
    db_settings_url = grafana_url + db_settings_api + "uid/" + uid
    jsondata =  connect_grafana(session, db_settings_url).json()
    return jsondata

def get_dashboards(session, grafana_url, db_search_api):

    db_url = grafana_url + db_search_api
    resp = connect_grafana(session,db_url).json()

    return resp

def save_dashboards_settings(backup_folder, org_name, dashboard_name, dashboard_settings, verbose):
    filename = "{0}-{1}.json".format(str(org_name),str(dashboard_name))

    if (backup_folder.startswith("$HOME")):
        backup_folder = os.getenv('HOME') + '/grafana-backup/'

    if (not os.path.exists(backup_folder)):
        try:
            os.mkdir(backup_folder)
        except:
            print(f'Error with creating backup_folder {backup_folder}')

    org_sub_folder = os.path.join(backup_folder,str(org_name))

    if (not os.path.exists(org_sub_folder)):
        try:
            os.mkdir(org_sub_folder)
        except:
            print("Error with creating organisasjons subfolder.")

    absolute_file_name = os.path.join(org_sub_folder,filename)

    if (not os.path.exists(absolute_file_name)):

        if verbose == True:
            print(f'Backing up dashboard {dashboard_name} from organization {org_name} to backup file \
                    {filename}')
        with open(absolute_file_name, 'w') as outfile:
            json.dump(dashboard_settings,outfile)
    else:
        tmpfile = "/tmp/{0}".format(filename)
        with open(tmpfile,'w', encoding="utf-8") as outfile:
            json.dump(dashboard_settings,outfile)
        tmpfilehash = hashlib.md5()
        tmpfilehash.update(open(tmpfile,"r", encoding="utf-8").read().encode("utf-8"))

        filenamehash = hashlib.md5()
        filenamehash.update(open(absolute_file_name,"r",encoding="utf-8").read().encode("utf-8"))
        if tmpfilehash.hexdigest() == filenamehash.hexdigest():
            if verbose == True:
                print(f'Dashboard {dashboard_name} from organization {org_name} has not changed. \
                        Backup file {filename} for dashboard already exist.')
            #remove tmp file
            try:
                os.remove(tmpfile)
            except:
                print("Error with deleting tmpfile.")
        else:
            if verbose == True:
                print(f'Backing up dashboard {dashboard_name} from organization {org_name} to backup file\
                        {filename}')
            shutil.move(tmpfile,absolute_file_name)

def create_grafana_folder(session, grafana_url, folder_api, grafana_folder):
    folder_url = grafana_url + folder_api
    jsondata = json.dumps({ 'title' : grafana_folder })
    resp = connect_grafana(session, folder_url, method="post", jsondata=jsondata).json()
    return resp

def grafana_folder_exists(session, grafana_url, db_search_api, grafana_folder):
    search_url = "{}{}?query={}".format(grafana_url, db_search_api, grafana_folder)
    resp = connect_grafana(session, search_url, method="get").json()

    if len(resp) == 0:
        return False

    for folder in resp:
        if grafana_folder == folder["title"] and folder["type"] == "dash-folder":
            return True
        else:
            return False

def get_folder_id(session, grafana_url, db_search_api, grafana_folder):
    search_url = "{}{}?query={}".format(grafana_url, db_search_api, grafana_folder)
    resp = connect_grafana(session, search_url, method="get").json()
    if len(resp) < 1:
        # there are two folders with the same name
        return -1
    else:
        return resp[0]["id"]

def dashboard_exits(session, grafana_url, db_search_api, db_name, db_uid, grafana_folder=None):
    search_url = "{}{}?query={}".format(grafana_url, db_search_api, db_name)
    resp = connect_grafana(session, search_url, method="get").json()

    if len(resp) == 0:
        return False

    for db in resp:
        if grafana_folder == None:
            if db_name == db["title"] and db["type"] == "dash-db":
                return True
            else:
                return False
        else:
            if not "folderTitle" in db.keys():
                db['folderTitle'] = "general"
            if db["title"] == db_name and db["type"] == "dash-db" and db['folderTitle'] == grafana_folder\
                    and db["uid"] == db_uid:
                return True
            else:
                return False
def restore_dashboard(session, grafana_url, db_settings_api, db_json, grafana_folder=None):
    restore_url = grafana_url + db_settings_api + "db"
    postdata = {}

    if grafana_folder != None:
        db_json['folderTitle'] = grafana_folder
    postdata['Dashboard'] = db_json["dashboard"]
    postdata['folderId'] = db_json["folderId"]
    postdata['overwrite']=True
    postdata['Dashboard']['id']="null"
    #postdata['Dashboard']['title']="restored-{0}".format(postdata['Dashboard']['title'])
    postdata['Dashboard']['title']="{0}".format(postdata['Dashboard']['title'])
    postdata['message']='restoring from backup'

    jsondata=json.dumps(postdata)
    resp = connect_grafana(session, restore_url, method="post", jsondata=jsondata).json()
    return resp

def read_json_files(restore_folder):
    # reading all dashboards backup files from restore_folder
    db_list = []
    glob_pattern = "{}/*.json".format(restore_folder)
    for f_name in glob(glob_pattern):
        with open(f_name,'r') as jsonfile:
            jsondata = json.load(jsonfile)
            db_list.append(jsondata)
    return db_list

if __name__ == "__main__":

    orgs_dbs = {}
    org_api = "/api/orgs"
    db_search_api = "/api/search"
    db_settings_api = "/api/dashboards/"
    change_org_api = "/api/user/using/"
    folder_api = "/api/folders"

    argvs = argsv_config()

    if not argvs.grafana_url:
        print("grafana url must be given.")
        sys.exit(1)

    grafana_url = argvs.grafana_url
    pwd_file = argvs.pwd_file
    backup_folder = argvs.backup_folder

    session = create_session(grafana_url, pwd_file)

    # get all organizations
    org_dict = get_organizations(session,grafana_url,org_api)

    # get all dashboards for all organizations
    for org_name, org_id in org_dict.items():
        change_current_org(session, grafana_url, change_org_api, org_id)
        resp = get_dashboards(session, grafana_url, db_search_api)
        if len(resp) > 0:
            if org_name not in orgs_dbs:
                orgs_dbs[org_name] = [db for db in resp if db['type'] == "dash-db"]

    if argvs.list_orgs == True:
        list_organizations(org_dict)

    if argvs.list_dashboards == True:
        if not argvs.org_name:
            # printing list of dashboards for all grafana organisations
            for org_name in orgs_dbs:
                print("*"*50)
                print(org_name)
                print("*"*50)
                for db in orgs_dbs[org_name]:
                    print(db['title'])
        else:
            # printing list of dashboards for a given grafana organisation
            for db in orgs_dbs[argvs.org_name]:
                print(db['title'])

    if argvs.backup == True:
        # backup all dashboards from all grafana organisation
        if not argvs.org_name:
            for org_name, org_id in org_dict.items():
                change_current_org(session, grafana_url, change_org_api, org_id)
                if org_name in orgs_dbs:
                    for dashboard in orgs_dbs[org_name]:
                        org_name=str(org_name).lower()
                        dashboard_name="-".join(map(str,str(dashboard['title'])\
                                .lower().replace("/","-").replace("-"," ").split()))
                        dashboard_settings = get_dashboard_settings(session, grafana_url, \
                                db_settings_api, dashboard['uid'])
                        save_dashboards_settings(backup_folder, org_name, dashboard_name, \
                                dashboard_settings, argvs.verbose)
        else:
            # backup dashboards from a given grafana organisation
            org_name = argvs.org_name
            org_id = org_dict[org_name]
            if not argvs.org_name in orgs_dbs:
                print("Given grafana organisation has no dashboard to backup.")
                sys.exit(1)
            else:
                change_current_org(session, grafana_url, change_org_api, org_id)

                for dashboard in orgs_dbs[org_name]:
                    org_name=str(org_name).lower()
                    dashboard_name="-".join(map(str,str(dashboard['title'])\
                            .lower().replace("/","-").replace("-"," ").split()))
                    dashboard_settings = get_dashboard_settings(session, grafana_url, \
                            db_settings_api, dashboard['uid'])
                    save_dashboards_settings(backup_folder, org_name, dashboard_name, \
                            dashboard_settings, argvs.verbose)

                print("Backup ended.")

    if argvs.restore:

        if not argvs.org_name:
            print("Grafana organisation name not given!")
            sys.exit(1)

        if not argvs.grafana_folder:
            print("A grafana folder is not given!")
            sys.exit(1)

        grafana_folder = argvs.grafana_folder
        org_name = argvs.org_name

        try:
            org_id = org_dict[org_name]
        except:
            print("Grafana org. not found")

        change_current_org(session, grafana_url, change_org_api, org_id)

        if not grafana_folder_exists(session, grafana_url, db_search_api, grafana_folder):
            print("Folder not found under grafana org. Creating the folder...")
            resp = create_grafana_folder(session, grafana_url, folder_api, grafana_folder)

        # restoring dashboard from a backup file.
        if argvs.restore_file:
            with open(argvs.restore_file,'r') as jsonfile:
                db = json.load(jsonfile)

            db_name = db["dashboard"]["title"]
            db_uid = db["dashboard"]["uid"]
            folder_id = get_folder_id(session,grafana_url, db_search_api, grafana_folder)
            db["folderId"] = folder_id
            # check dashboard exists in the folder
            if dashboard_exits(session, grafana_url, db_search_api, db_name, db_uid, grafana_folder):
                print("dashboard exits in the folder")
            else:
                resp = restore_dashboard(session, grafana_url, db_settings_api, \
                        db, grafana_folder)
                print(f'{db_name} is restored to {org_name}\{grafana_folder}')

        if argvs.restore_folder:

            db_list = read_json_files(argvs.restore_folder)

            for db in db_list:
                db_json = {}
                tags = []
                if db["meta"]["isFolder"]:
                    continue
                db_name = db["dashboard"]["title"]
                db_uid = db["dashboard"]["uid"]

                ## if exported db was under a folder in grafana-org.
                ## this foldername of exported db will be added as a tag of db
                ## folder name where the db will be moved is going to replace
                ## folderTitle attribute.
                #if "tags" in db["dashboard"].keys():
                #    tags = db["dashboard"]["tags"]

                #if db["meta"]["folderTitle"] == "General":
                #    pass
                #else:
                #    tags.append(db["meta"]["folderTitle"])
                #    db["dashboard"]["tags"] = tags

                db_json["dashboard"] = db["dashboard"]

                folder_id = get_folder_id(session,grafana_url, db_search_api,grafana_folder)
                db_json["folderId"] = folder_id

                # check dashboard exists in the folder
                if dashboard_exits(session, grafana_url, db_search_api, db_name, db_uid, grafana_folder):
                    print("dashboard exits in the folder")
                else:
                    resp = restore_dashboard(session, grafana_url, db_settings_api, \
                            db_json, grafana_folder)
                    print(f'{db_name} is restored to {org_name}\{grafana_folder}')

