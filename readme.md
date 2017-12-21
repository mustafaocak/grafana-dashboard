Backup/restore grafana dashboard
===================================

This script uses Grafana http-api to get organizations and dashboards within organizations. It can be used to backup all the dashboards for all organizations in grafana. It can also restore a given dashboards to a given organization. 

usage::




    usage: grafana-dashboard.py [-h] [-lo] [-ld] [-v] [-backup]
                                [-backupfolder BACKUPFOLDER] [-restore]
                                [-orgname ORGNAME] [-backupfile BACKUPFILE]
                                [-pwdfile PWDFILE] [-grafanaurl GRAFANAURL]

    optional arguments:
      -h, --help            show this help message and exit
      -lo                   List organizations defined in grafana.
      -ld                   List dashboards defined in grafana.
      -v                    Output verbose information.
      -backup               Backup either all dashboards in grafana to
                            backupfolder or dashboards of a given organization.
      -backupfolder BACKUPFOLDER
                            Backup folder for grafana dashboards. Default is $HOME
                            /grafana-backup/
      -restore              Restore a dashboard from backup file to a given
                            organization.
      -orgname ORGNAME      Organisation name where dashboards will be
                            backuped/restored.
      -backupfile BACKUPFILE
                            Backup file from which dashboard will be restored.
      -pwdfile PWDFILE      Grafana pwd file location. It is default set to
                            $HOME/.grafanapwd
      -grafanaurl GRAFANAURL
                            Grafana url.

example usage::

    to backup
    python grafana-dashboard.py -grafanaurl https://test-grafana -backup
    
    to restore
    python grafana-dashboard.py -grafanaurl https://test-grafana -restore -backupfile ~/grafana-backup/<org_name>/<org_name>-test-dashboard.json -orgname <org_name>    
    
