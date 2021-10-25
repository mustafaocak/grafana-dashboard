Backup/restore grafana dashboard
===================================

This script uses Grafana http-api to get organizations and dashboards within organizations. It can be used to backup all the dashboards for all organizations in grafana. It can also restore a given dashboards to a given organization. 

usage:

    usage: grafana-dashboard.py [-h] [-list_org] [-list_dbs] [-grafana_folder GRAFANA_FOLDER] [-v] [-backup] [-backup_folder BACKUP_FOLDER]
                                [-restore_folder RESTORE_FOLDER] [-restore] [-org_name ORG_NAME] [-restore_file RESTORE_FILE] [-pwd_file PWD_FILE]
                                [-grafana_url GRAFANA_URL]
    
    optional arguments:
      -h, --help            show this help message and exit
      -list_org             List organizations defined in grafana.
      -list_dbs             List dashboards defined in grafana.
      -grafana_folder GRAFANA_FOLDER
                            When used together with -restore, it defines destination grafana folder for restore. if grafana folder does not exist under given
                            organisation, it will be created automatically.
      -v                    Output verbose information.
      -backup               Backup either all dashboards in grafana to backupfolder or dashboards of a given organization.
      -backup_folder BACKUP_FOLDER
                            Backup folder for grafana dashboards. Default is $HOME/grafana-backup/
      -restore_folder RESTORE_FOLDER
                            Restore folder where grafana dashboards will be restored from. Default is ""
      -restore              Restore dashboards from a backup file or folder to a given organization. requires that grafana_folder is given.
      -org_name ORG_NAME    Organisation name where dashboards will be backed up and restored to.
      -restore_file RESTORE_FILE
                            Backup file from which dashboard will be restored.
      -pwd_file PWD_FILE    Grafana pwd file location. It is default set to $HOME/.grafanapwd
      -grafana_url GRAFANA_URL
                            Grafana url.
example usage:

    to backup all dashboards from all grafana org.
    python grafana-dashboard.py -grafana_url https://test-grafana -backup
    
    to backup all dashboards from a given grafana org.
    python grafana-dashboard.py -grafana_url https://test-grafana -backup -org_name <org_name>

    to restore dashboard from a given file
    python grafana-dashboard.py -grafana_url https://test-grafana -restore -restore_file ~/grafana-backup/<org_name>/<org_name>-test-dashboard.json -org_name <org_name> -grafana_folder <grafana_folder_name>
    
