import subprocess, logging, shutil, os, stat, errno
from sys import exit

##############################
#   CONFIG
##############################
#Location to use for logfile
logfile = r''
#Command to call rsync
rsync_command = r'C:\cygwin\bin\rsync.exe'
#Number of backups to keep
max_backups = 5

##############################
#   HELPER FUNCTIONS
##############################
def cygwin_format(dir):
    """Format a windows directory to format usable by cygwin."""
    split_dict = dir.split(':\\')
    drive = split_dict[0].lower()
    path = split_dict[1].replace('\\', '/')
    cygwin_path = '/cygdrive/' + drive + '/' + path
    return cygwin_path

def remove_readonly(func, path, exc):
    #Function shamelessly stolen from StackOverflow
    """Error function for shutil.rmtree. Will chmod 777 the offending file and then try again."""
    excvalue = exc[1]
    if func in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
        os.chmod(path, stat.S_IRWXU| stat.S_IRWXG| stat.S_IRWXO) # 0777
        func(path)
    else:
        raise

##############################
#   MAIN BACKUP SCRIPT
##############################
if __name__ == "__main__":
    #Setup logging
    logging.basicConfig(filename=logfile, level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

    #Make sure max_backups is an int!
    try:
        int(max_backups)
    except ValueError, e:
        print "Invalid value for maximum number of backups. Exiting."
        logging.error("Invalid value for maximum number of backups. Exiting.")
        exit()

    #Dictionary of backup locations--source folder as key, destination folder as value
    dirs = {
            r'/cygdrive/c/Users/ravenel/Documents/EA Games': r'/cygdrive/c/Users/ravenel/Documents/test',
            #r'C:\Users\ravenel\Documents\EA Games': r'C:\Users\ravenel\Documents\test',
            #r'C:\Users\ravenel\Documents\EA Games': r'Y:\backups\test',
    }

    for src, dst in dirs.items():
            #Delete the oldest backup
            try:
                os.chmod(os.path.join(dst, "backup.%s" % ((max_backups - 1))), stat.S_IRWXG| stat.S_IRWXU| stat.S_IRWXO)
                #os.system('attrib -R %s' % os.path.join(dst, "backup.%s" % ((max_backups - 1))))
                #os.remove(os.path.join(dst, "backup.%s" % ((max_backups - 1))))
                shutil.rmtree(os.path.join(dst, "backup.%s" % ((max_backups - 1))), ignore_errors=False, onerror=remove_readonly)
            except OSError, e:
                print "Unable to delete oldest backup: %s" %e
                logging.error("Unable to delete oldest backup: %s" %e)
            
            #Move the old backups back one
            print "Moving old backups...",
            for backup_num in range(max_backups -1, -1, -1):
                old_filename = os.path.join(dst, "backup.%s" % backup_num)
                new_filename = os.path.join(dst, "backup.%s" % (backup_num + 1))
                if os.path.isdir(old_filename): #Make sure it exists--could be first time running
                    logging.info("Moving backup %s to %s..." % (old_filename, new_filename)),
                    print "Moving backup %s to %s..." % (old_filename, new_filename),
                    try:
                        shutil.move(old_filename, new_filename)
                        print "Done."
                        logging.info("Done.")
                    except IOError, e:
                        print "Unable to move backup %s to %s: %s" % (old_filename, new_filename, e)
                        logging.error("Unable to move backup %s to %s: %s" % (old_filename, new_filename, e))
                else:
                    continue
            print "Done."

            #Do the backup
            link_dest_string = '--link-dest="%s/backup.0" "%s" "%s/incomp-backup.0"' % (cygwin_format(dst), cygwin_format(src), cygwin_format(dst))
            #Make empty dir so rsync doesn't complain
            os.mkdir(os.path.join(dst, "backup.0"))
            rsync = subprocess.Popen('%s -azP --delete %s' % (rsync_command, link_dest_string), stdout=subprocess.PIPE, shell=True).communicate()[0]
            logging.info("rsync complete.")

            #Rename the now completed backup
            #The name of the incomplete backup
            incomp_back_str = '%s/incomp-backup.0' % (dst)
            #The name of the complete backup
            comp_back_str = '%s/backup.0' % (dst)
            try:
                shutil.move(incomp_back_str, comp_back_str)
            except IOError, e:
                print "Unable to move backup %s to %s: %s" % (incomp_back_str, comp_back_str, e)
                logging.error("Unable to move backup %s to %s: %s" % (incomp_back_str, comp_back_str, e))