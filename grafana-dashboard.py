import requests
import os
import json
import argparse
import sys
import hashlib
import shutil

class grafanaDashboard:
    def __init__(self):
        self.argsv_config()
        self.readpwd()
        self.orgapi = "/api/orgs"
        self.dashboardsearchapi = "/api/search"
        self.dashboardsettingsapi = "/api/dashboards/"
        self.changeorgapi="/api/user/using/"
        self.dashboarddic={}
        self.org_dic={}

    def argsv_config(self):
         
        parser = argparse.ArgumentParser()
        parser.add_argument('-lo', action='store_true', default=False, dest='list_orgs', help='List organizations defined in grafana.')
        parser.add_argument('-ld', action='store_true', default=False, dest='list_dashboards', help='List dashboards defined in grafana.')
        parser.add_argument('-v', action='store_true', default=False, dest='verbose', help='Output verbose information.')
        parser.add_argument('-backup', action='store_true', default=False, dest='backup', help='Backup either all dashboards in grafana to backupfolder or dashboards of a given organization.')
        parser.add_argument('-backupfolder', action='store',default='$HOME/grafana-backup/',dest='backupfolder', help='Backup folder for grafana dashboards. Default is $HOME/grafana-backup/')
        parser.add_argument('-restore', action='store_true', default=False, dest='restore', help='Restore a dashboard from backup file to a given organization.')
        parser.add_argument('-orgname', action='store',dest='orgname', default="",help='Organisation name where dashboards will be backuped/restored.')
        parser.add_argument('-backupfile', action='store',dest='backupfile', default="", help='Backup file from which dashboard will be restored.')
        parser.add_argument('-pwdfile', action='store',default='$HOME/.grafanapwd',dest='pwdfile', help='Grafana pwd file location. It is default set to $HOME/.grafanapwd')
        parser.add_argument('-grafanaurl', action='store',default='',dest='grafanaurl', help='Grafana url.')
        self.argvs = parser.parse_args()

    def readpwd(self):
        #
        # Reading password file  
        # password file format
        # username=<username>
        # password=<password>
        #

        try:
            tmpfile = str(self.argvs.pwdfile)
            
            if (tmpfile.startswith("$HOME")):
                pwdfile = os.getenv('HOME') + '/.grafanapwd'
            else:
                pwdfile = tmpfile 

            if (os.path.isfile(pwdfile) and os.access(pwdfile,os.R_OK)):
                fh= open(pwdfile,'r')
                lines = fh.readlines()
                self.pwd=(lines.pop().strip("\n")).split("=")[1]
                self.user=(lines.pop().strip("\n")).split("=")[1]
            else:
                raise Exception("File doesn't exists or is not accessible!")

        except Exception as e:
            print "Error with reading grafanapwd file: {0}".format(str(e))
            print "Grafana pwd file format: \nusername=<username>\npassword=<password>"
            sys.exit(1)            

    def connect_grafana(self,apiurl,method="get",jsondata=None):
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

        try:
            if method=="get":
                rq=requests.get(apiurl,auth=(self.user,self.pwd))
            elif method=="post":
                rq=requests.post(apiurl,auth=(self.user,self.pwd),data=jsondata,headers=headers)
        except:
            print "Error with connection grafana."
            sys.exit(1)

        return rq

    def get_organizations(self):

        orgurl=self.argvs.grafanaurl+self.orgapi
        jsondata=self.connect_grafana(orgurl).json()
        for data in jsondata:
            if (not self.org_dic.has_key(data['name'])):
                self.org_dic[data['name']]=data['id']

    def list_organizations(self):
        for org in self.org_dic.keys():
            print org

    def get_dashboard_settings(self,uri):
        dashboard_settings_url=self.argvs.grafanaurl+self.dashboardsettingsapi+uri
        jsondata=self.connect_grafana(dashboard_settings_url).json()
        return jsondata

    def get_dashboards(self,org):

        dshurl = self.argvs.grafanaurl + self.dashboardsearchapi
        jsondata= self.connect_grafana(dshurl).json()

        #
        # Check whether given org. has any dashboards defined.
        #
        if len(jsondata)== 0:
            if (not self.dashboarddic.has_key(org)):
                self.dashboarddic[org]=[]
        else:
            for data in jsondata:
                if (not self.dashboarddic.has_key(org)):
                    self.dashboarddic[org]=[]
                    self.dashboarddic[org].append(data)
                else:
                    self.dashboarddic[org].append(data)

    def list_dashboards(self,org_name=None):
        if org_name==None:
            #list all dashboards for all organizations
            for org in self.dashboarddic:
                print "********************"
                print "*** {0} ***".format(org)
                print "********************"
                if (len(self.dashboarddic[org])) == 0:
                    print "Organization {0} has no dashboard defined.".format(org)
                else:
                    for dashboard in self.dashboarddic[org]:
                        print dashboard['title']
                
        else:
            print "********************"
            print "*** {0} ***".format(org_name)
            print "********************"
            if (len(self.dashboarddic[org_name])) == 0:
                print "Organization {0} has no dashboard defined.".format(org_name)
            else:
                for dashboard in self.dashboarddic[org_name]:
                    print dashboard['title']

    def change_current_org(self,orgid):
        change_org_url=self.argvs.grafanaurl+self.changeorgapi+str(orgid)
        self.connect_grafana(change_org_url,method="post")
        
    def save_dashboards_settings(self,org_name,dashboard_name,dashboard_settings):
        filename = "{0}-{1}.json".format(str(org_name),str(dashboard_name))

        foldername = str(self.argvs.backupfolder)
        
        if (foldername.startswith("$HOME")):
            backupfolder = os.getenv('HOME') + '/grafana-backup/' 
        else:
            backupfolder = foldername

        if (not os.path.exists(backupfolder)):
            try:
                os.mkdir(backupfolder)
            except:
                print "Error with creating backupfolder {0}".format(backupfolder)

        org_sub_folder = os.path.join(backupfolder,str(org_name))
        
        if (not os.path.exists(org_sub_folder)):
            try:
                os.mkdir(org_sub_folder)
            except:
                print "Error with creating organisasjons subfolder."
        
        absolute_file_name = os.path.join(org_sub_folder,filename)

        if (not os.path.exists(absolute_file_name)):                

            if self.argvs.verbose == True:
                print "Backing up dashboard \"{0}\" from organization \"{1}\" to backup file \"{2}\"".format(dashboard_name,org_name,filename)
            with open(absolute_file_name, 'w') as outfile:
                json.dump(dashboard_settings,outfile)
        else:
            tmpfile = "/tmp/{0}".format(filename)
            with open(tmpfile,'w') as outfile:
                json.dump(dashboard_settings,outfile)
            tmpfilehash = hashlib.md5()
            tmpfilehash.update(open(tmpfile).read())

            filenamehash = hashlib.md5()
            filenamehash.update(open(absolute_file_name).read())
            if tmpfilehash.hexdigest() == filenamehash.hexdigest():
                if self.argvs.verbose == True:
                    print "Dashboard \"{0}\" from organization \"{1}\" hasn't changed. Backup file \"{2}\" for dashboard already exist.".format(dashboard_name,org_name,filename)
                #remove tmp file
                try:
                    os.remove(tmpfile)
                except:
                    print "Error with deleting tmpfile."
            else:
                if self.argvs.verbose == True:
                    print "Backing up dashboard \"{0}\" from organization \"{1}\" to backup file \"{2}\"".format(dashboard_name,org_name,filename)
                shutil.move(tmpfile,absolute_file_name)

    def restore_dashboard(self,org_name,backupfile):
        postdata={}
        restoreapi = self.argvs.grafanaurl+self.dashboardsettingsapi+"db"

        if (self.org_dic.has_key(org_name)):
            self.change_current_org(self.org_dic[org_name])

            with open(backupfile,'r') as jsonfile:
                jsondata = json.load(jsonfile)
            
            postdata['Dashboard']=jsondata['dashboard']
            postdata['overwrite']=True
            postdata['Dashboard']['id']='null'
            postdata['Dashboard']['title']="restored-{0}".format(postdata['Dashboard']['title'])
            postdata['message']='restoring from backup'
            if self.argvs.verbose == True:
                print "Restoring dashboard \"{0}\" to organization \"{1}\" from backup file \"{2}\"".format(postdata['Dashboard']['title'],org_name,backupfile)

            jdata=json.dumps(postdata)
            res = self.connect_grafana(restoreapi,method="post",jsondata=jdata)
            jsondata=res.json()
            if res.status_code != 200:
                print "Error with restoring dashboard: {0}: {1}\nEnsure that all datasources needed for dashboard are defined for organization given.".format(res.status_code, jsondata['message'])
                sys.exit(1)
            elif res.status_code == 200:
                print "Dashboard {0} successfully restored to organization {1}. ".format(postdata['Dashboard']['title'],org_name)
                

if __name__ == '__main__':
    
    gd = grafanaDashboard()
    
    if gd.argvs.grafanaurl != '': 
        # get all organizations
        gd.get_organizations()

        # get all dashboards for all organizations
        for org in gd.org_dic.keys():
            gd.change_current_org(gd.org_dic[org])
            gd.get_dashboards(org)

        if gd.argvs.list_orgs == True: 
            gd.list_organizations()

        elif gd.argvs.list_dashboards == True:
            if gd.argvs.orgname =='':
                gd.list_dashboards()
            else:
                gd.list_dashboards(org_name=gd.argvs.orgname)

        elif gd.argvs.backup == True:
            print "Backup started..."
            for org in gd.org_dic.keys():
                gd.change_current_org(gd.org_dic[org])

                # if org. has no dashboards defined
                if len(gd.dashboarddic[org]) ==0:
                    if gd.argvs.verbose == True:
                        print "Organisation {0} has no dashboards defined!".format(org)
                else:

                    for dashboard in gd.dashboarddic[org]:
                        org_name=str(org).lower()
                        dashboard_name="-".join(map(str,str(dashboard['title']).lower().replace("/","-").replace("-"," ").split()))
                        dashboard_settings = gd.get_dashboard_settings(dashboard['uri'])
                        gd.save_dashboards_settings(org_name,dashboard_name,dashboard_settings)
            print "Backup ended."

        elif gd.argvs.restore == True:
            if gd.argvs.backupfile == "":
                print "Backup file is not given!"
            else:
                backupfile = gd.argvs.backupfile
                if gd.argvs.orgname == "":
                    print "Organisation name is not given!"
                else:
                    org_name = gd.argvs.orgname
                    print "Restore started."
                    gd.restore_dashboard(org_name,backupfile) 
                    print "Restore ended."
        else:
            print "For help python grafana-dashboard.py -h"


    else:
        print "Grafana url is not given."
        sys.exit(1)


