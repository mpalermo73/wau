
class CurseAddon:

    # global debugme

    def __init__(self,config, ca):
        self.url_base = "https://wow.curseforge.com/projects"
        self.url_real = None
        self.title = None
        self.version = None
        self.url_download = None
        self.url_file_direct = None
        self.date_remote_utc = None
        self.size_remote = None
        self.date_local = None
        self.date_local_utc = None
        self.size_local = None

        self.name = str(ca.lower())
        self.url_project = str(self.url_base + "/" + str(ca))
        self.tank = config['addon_directory']
        self.stamp_file = str(self.tank) + "/." + str(self.name)

    def check_freshness(self):

        if self.date_remote_utc > self.date_local_utc:
            return True
        else:
            return False
