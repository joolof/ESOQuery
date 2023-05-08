import json
import pyvo
import requests
import numpy as np
from astropy.io import ascii
from datetime import datetime
import eso_programmatic as eso
from PyQt5.QtCore import pyqtSignal, QObject
# ------------------------------------------------------------
cds_url = 'http://cdsweb.u-strasbg.fr/cgi-bin/nph-sesame/-oI/?'
eso_url = "http://archive.eso.org/tap_obs"
# ------------------------------------------------------------
class DoQuery(QObject):
    """
    docstring for DoQuery
    """
    changedStatus = pyqtSignal(str)
    changedLog = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, parent = None):
        """
        Query the ESO raw data archive
        """
        super(DoQuery, self).__init__(parent)
        self._ignorekey = ['tpl_id', 'release_date', 'date_obs', 'datalink_url']
        # self._ignorekey = ['access_url', 'tpl_id', 'release_date', 'date_obs', 'dp_id', 'datalink_url']
        self.starname = None
        self.instrument = None
        self.user = None
        self.password = None
        self.raw = False
        self.pref_insts = None
        self.obinfo = []

    def _set_status(self, text):
        self.changedStatus.emit(text)

    def _set_log(self, text):
        self.changedLog.emit(text)

    def _echo(self, message):
        self._set_log(message)
        self._set_status(message)

    def _get_tap(self):
        """
        Get the TAP service, with or without the token
        """
        token = eso.getToken(self.user, self.password)
        """
        Define the tap service
        """
        if token is None:
            self._echo('Not logged in the ESO Archive. Will continue anonymously.')
            tap = pyvo.dal.TAPService(eso_url)
        else:
            self._echo('Logged in the ESO archive ...')
            session = requests.Session()
            session.headers['Authorization'] = "Bearer " + token
            tap = pyvo.dal.TAPService(eso_url, session=session)
        return tap

    def _resolve_name(self):
        """
        Query the cds to get the right ascension
        and declination
        """
        self._echo('Getting the coordinates from CDS for: {}'.format(self.starname))
        query_url = '{}{}'.format(cds_url, self.starname.replace(' ','%20'))
        getoutput = requests.get(query_url)
        query_output = getoutput.text
        if 'Nothing found' in query_output:
            self._echo('Name {} not resolved in CDS ... Stopping.'.format(self.starname))
            self._ra, self._dec = None, None
        else:
            query_output = query_output.split('\n')
            self._echo('{} resolved in Simbad'.format(self.starname))
            for i in range(len(query_output)):
                if (query_output[i].split(' ')[0] == '%J'):
                    self._ra = query_output[i].split(' ')[1]
                    self._dec = query_output[i].split(' ')[2]

    def start_query(self):
        """
        Define the keywords
        """
        if self.raw:
            self._keywords = ['object', 'ra', 'dec', 'prog_id', 'pi_coi', 'date_obs',
                              'instrument', 'dp_tech', 'dp_type', 'filter_path', 
                              'ins_mode', 'ob_id', 'ob_name', 'release_date', 'tpl_id', 'dp_id', 
                              'datalink_url', 'access_url']
        else:
            self._keywords = ['target_name', 's_ra', 's_dec', 'proposal_id', 'obstech',
                              'instrument_name', 'obs_creator_name', 'access_url', 
                              'filter', 'dp_id', 'dataproduct_type', 'obs_id', 'obs_release_date']
        """
        Query a star
        """
        self._ra, self._dec = None, None
        self.obinfo = []
        """
        Get the coordinates from the CDS
        """
        self._resolve_name()
        if ((self._ra is None) or (self._dec is None)):
            self.finished.emit()
            return
        """
        Try to authentify on the eso archive
        """
        tap = self._get_tap()
        """
        Prepare the query
        """
        insquery = None
        self._echo('Querying the ESO archive for: {}'.format(self.starname))
        query = "SELECT "
        for i in range(len(self._keywords)):
            query += " {}".format(self._keywords[i])
            if i != len(self._keywords) - 1:
                query += ","
            else:
                query += " "
        if self.raw:
            query += "from dbo.raw where "
            if self.instrument != 'All above':
                query += "instrument {} and ".format(self._inst_format(self.instrument))
            else:
                query += "("
                for i in range(len(self.pref_insts)):
                    query += "instrument {}".format(self._inst_format(self.pref_insts[i]))
                    # query += "instrument = '{}'".format(self.pref_insts[i])
                    if i != len(self.pref_insts)-1:
                        query += " or ".format(self.pref_insts[i])
                query += ") and "
            query += "dp_cat='SCIENCE' and contains(point('', ra, dec), "
            query += "circle('J2000',{}, {}, 20./3600.))=1 ".format(self._ra, self._dec)
            query += "AND dec BETWEEN -90 and 90"
        else:
            query += "from ivoa.obscore where "
            query += "intersects(circle('J2000',{},{}, 20./3600.),s_region)=1 ".format(self._ra, self._dec)
        self._set_log(query)
        # print(query)
        """
        Do the query
        """
        offline = False
        if offline:
            if self.raw:
                insquery = ascii.read('testing/HD61005_all.csv', delimiter = ';')
            else:
                insquery = ascii.read('testing/HD61005_phase3.csv', delimiter = ';')
        else:
            job = tap.submit_job(query)
            job.execution_duration = 300 # max allowed: 3600s
            job.run()
            try:
                job.wait(phases=["COMPLETED", "ERROR", "ABORTED"], timeout=600.)
            except pyvo.DALServiceError:
                self._set_log('Exception on JOB {id}: {status}'.format(id=job.job_id, status=job.phase))
            if job.phase == 'COMPLETED':
                insquery = job.fetch_result().to_table()
            job.delete()
        """
        Parse the results
        """
        if insquery is None:
            self._echo('No results for: {}'.format(self.starname))
        else:
            if self.raw:
                self._prep_raw(insquery)
            else:
                self._prep_p3(insquery)
            self._set_status('Found {} entries for: {} ({} individual files)'.format(len(self.obinfo), self.starname, len(insquery)))
        self.finished.emit()

    def _inst_format(self, inst):
        """
        Reformat a few things to account for different 
        instruments names
        """
        if inst == 'APEX':
            return "in ('APEXBOL', 'APEXHET')"
        elif inst == 'CRIRES':
            return "like 'CRIRE%'"
        elif inst == 'EFOSC2':
            return "like 'EFOSC%'"
        elif inst == 'FORS1/2':
            return "in ('FORS1', 'FORS2')"
        elif inst == 'GIRAFFE':
            return "like 'GIRAF%'"
        elif inst == 'NACO':
            return "like 'NAOS+CONICA%'"
        elif inst == 'SINFONI':
            return "like 'SINFO%'"
        elif inst == 'SPECULOOS':
            return "like 'SPECU%'"
        elif inst == 'TIMMI2':
            return "like 'TIMMI%'"
        elif inst == 'XSHOOTER':
            return "in ('SHOOT', 'XSHOOTER')"
        else:
            return "like '{}%'".format(inst)

    def _prep_p3(self, insquery):
        """
        Massage a bit the phase 3 query output

        Group by instrument and then by proposal id
        """
        for i in range(len(insquery)):
            insquery[i]['obs_release_date'] = str(insquery[i]['obs_release_date'].split('T')[0].replace('-','/'))
        for inst in np.unique(insquery['instrument_name']):
            sel = np.where(insquery['instrument_name'] == inst)[0]
            for io in np.unique(insquery[sel]['proposal_id']):
                selid = np.where(insquery[sel]['proposal_id'] == io)[0]
                self.obinfo.append(self.parse(insquery[sel[selid]]))

    def _prep_raw(self, insquery):
        """
        Massage a bit the raw query output
        """
        self._echo('Query finished. Parsing the data.')
        obsnight = np.zeros(len(insquery), dtype = 'U10')
        insquery.add_column(obsnight, name = 'obsnight')
        for i in range(len(insquery)):
            insquery[i]['obsnight'] = str(insquery[i]['date_obs'].split('T')[0].replace('-','/'))
            insquery[i]['release_date'] = str(insquery[i]['release_date'].split('T')[0].replace('-','/'))
        insquery.sort('date_obs')
        groups = np.zeros(len(insquery))
        insquery.add_column(groups, name = 'groups')
        gid = 0
        for inst in np.unique(insquery['instrument']):
            sel = np.where(insquery['instrument'] == inst)[0]
            insquery[sel[0]]['groups'] = gid
            for ig in range(1,len(insquery[sel])):
                day1 = self._get_time(insquery[sel[ig]]['date_obs'])
                prev = self._get_time(insquery[sel[ig-1]]['date_obs'])
                deltah = divmod((day1 - prev).total_seconds(), 3600)[0]
                if deltah > 3.:
                    gid += 1
                insquery[sel[ig]]['groups'] = gid
            gid += 1
                
        for ir, io in enumerate(np.unique(insquery['groups'])):
            self.obinfo.append(self.parse(insquery[(insquery['groups'] == io)]))


    def _get_time(self, dobs):
        """
        Check the format of the date_obs
        and return a datetime object
        """
        if len(dobs.split('.')) == 2:
            dt = datetime.strptime(dobs, '%Y-%m-%dT%H:%M:%S.%f')
        else:
            dt = datetime.strptime(dobs, '%Y-%m-%dT%H:%M:%S')
        return dt

    def parse(self, q):
        """
        Parse the entries per "group"
        """
        d = {}
        d['nfiles'] = len(q)
        kw = self._keywords.copy()
        kw.append('obsnight')
        for key in kw:
            if key in q.colnames:
                tmp = np.unique(q[key].data)
                d[key] = self._format(tmp, key)
        return d

    def _format(self, entry, key):
        """
        Try to format things a bit better
        """
        text = ''
        if key == 'object':
            if '' in entry: entry = np.delete(entry, np.where(entry == ''))
            if 'OBJECT' in entry: entry = np.delete(entry, np.where(entry == 'OBJECT'))
            if 'OBJECT NAME NOT SET' in entry: entry = np.delete(entry, np.where(entry == 'OBJECT NAME NOT SET'))
        if key == 'ra' or key == 'dec' or key == 's_ra' or key == 's_dec':
            text += '{:.4f}'.format(np.mean(entry))
        else:
            if len(entry) ==0:
                text = '--'
            for i in range(len(entry)):
                text += str(entry[i])
                if i != len(entry) - 1:
                    text += '\n'
        return text




class DataDownloader(QObject):
    """
    docstring for DataDownloader
    """
    changedStatus = pyqtSignal(str)
    changedLog = pyqtSignal(str)
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def __init__(self, parent = None):
        """
        Query the ESO raw data archive
        """
        super(DataDownloader, self).__init__(parent)
        self.user, self.password, self.dpath = None, None, None
        self.access_url, self.datalink_url, self.obs_id, self.selector = [], [], [], None
        self.raw = False

    def _set_status(self, text):
        self.changedStatus.emit(text)

    def _set_log(self, text):
        self.changedLog.emit(text)

    def _echo(self, message):
        self._set_log(message)
        self._set_status(message)

    def _get_data(self):
        token = eso.getToken(self.user, self.password)
        session = None
        if token:
            session = requests.Session()
            session.headers['Authorization'] = "Bearer " + token

        if self.raw:
            urls = self._urls_raw()
        else:
            urls = self._urls_phase3()

        nf = len(urls)
        if nf > 0:
            self._echo('Will download {} files in {}'.format(nf, self.dpath))
        for i in range(nf):
            status, filename = eso.downloadURL(urls[i], dirname = self.dpath, session = session)
            if status != 200:
                self._echo('Could not download the following file: {}'.format(filename))
            self.progress.emit(int(100.*(i+1)/nf))
        self.finished.emit()

    def _urls_phase3(self):
        """
        Get the urls for the phase3 data
        """
        urls = []
        self._echo('Searching for products and preview files.')
        for i in range(len(self.access_url)):
            if 'almascience' in self.access_url[i]:
                print(self.access_url[i])
                self._echo('Downloading of ALMA data is not yet supported.')
            else:
                datalink = pyvo.dal.adhoc.DatalinkResults.from_result_url(self.access_url[i])
                product_url = next(datalink.bysemantics('#this'), None)
                if product_url is not None:
                    urls.append(product_url.access_url)
                product_url = next(datalink.bysemantics('#preview'), None) # Might as well get a preview
                if product_url is not None:
                    urls.append(product_url.access_url)
        return np.unique(urls)

    def _urls_raw(self):
        """
        Get the urls for the raw data
        """
        urls = self.access_url
        if self.selector != 'sci':
            """
            Get the calibration files
            """
            self._echo('Running the calibration cascade.')
            semantics = 'http://archive.eso.org/rdf/datalink/eso#calSelector_{}'.format(self.selector)
            for i in range(len(self.datalink_url)):
                """
                Following the notebook at:
                http://archive.eso.org/programmatic/HOWTO/jupyter/authentication_and_authorisation/programmatic_authentication_and_authorisation.html
                """
                datalink = pyvo.dal.adhoc.DatalinkResults.from_result_url(self.datalink_url[i])
                raw2master_url = next(datalink.bysemantics(semantics), None)
                if raw2master_url is not None:
                    raw2master_url = raw2master_url.access_url
                    associated_calib_files = pyvo.dal.adhoc.DatalinkResults.from_result_url(raw2master_url)
                    calibrator_mask = associated_calib_files['semantics'] == '#calibration'
                    calibs = associated_calib_files.to_table()[calibrator_mask]['access_url']
                    for calib in calibs:
                        urls.append(calib)
            if urls == self.access_url:
                self._echo('No calibration files were found. ')
        return np.unique(urls)

