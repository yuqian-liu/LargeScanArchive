import subprocess

class PatientDB:
    """A class that queries the Patient Database"""

    def __init__(self):
        self.input_file = os.path.join(temp_folder, input_file)
        self.output_file = os.path.join(temp_folder, output_file)

    def _query(self, query_str):
        """a wrapper to query the patient database"""

        # add prefix and postfix to query string
        query_str = 'use patientdb\r\ngo\r\n' + query_str
        query_str = query_str + '\r\ngo'

        # create input file
        with open(self.input_file, "w") as file:
            file.write(query_str)

        osql_query = 'osql -S "LOCALHOST\SQLEXPRESS" -E -n -s "|" -w 65536 -i "' + self.input_file + '" -o "' + self.output_file + '" '

        # actually query the patient database
        subprocess.call(osql_query, shell=True)

        # read in the output file
        with open(self.output_file, "r") as file:
            output_query = file.readlines()

        # split and trim the results
        table = [[item.strip(" \n") for item in line.split("|")] for line in output_query]

        # lose the first two and last two lines
        table = table[2:-2]

        return table

    def get_all_large_scans(self):
        series_list = []
        return series_list

    def get_series_frame_number_scanner(self, series_iuid):
        frameNumber = 0
        return frameNumber

    def get_series_OID(self, series_iuid):
        series_OID = ''
        return series_OID

    def extract_exams(self):
        """Extract a list of all the exams in the patient database"""

        # query_str = "select OBJECT_OID, DICOM_PATIENT_NAME from patient" # old query_str
        query_str = "select examination.OBJECT_OID, patient.OBJECT_OID, patient.DICOM_PATIENT_NAME from patient, examination where examination.Patient_OID=patient.OBJECT_OID"

        table = self._query(query_str)

        # first column is the exam number, second is the patient name
        eoid, poid, name = zip(*table)

        return eoid, poid, name

    def extract_series(self, exam_id):
        """Extract a list of series id associated with an exam in the patient database"""

        query_str = 'select OBJECT_OID, PIIM_MR_SERIES_ACQUISITION_NUMBER, PIIM_MR_SERIES_RECONSTRUCTION_NUMBER, DICOM_SERIES_DESCRIPTION from mrseries where PARENT_OID=%s AND PIIM_MR_SERIES_DATA_TYPE="PIXEL"' % exam_id

        table = self._query(query_str)

        # series id, acquisition number, reconstruction number, and name of the acquisition
        sid, acqn, recn, name = zip(*table)

        names = []
        for i, n in enumerate(name):
            names.append(acqn[i] + '_' + recn[i] + '_' + name[i].replace(" ", "_"))

        return sid, names

    def extract_bulk_files(self, exam_id, series_id):
        """Extract a list of bulk files associated with an exam and series id in the patient database"""

        query_str = 'select token from roidandtoken where object_oid=%s and parent_oid=%s and FileType="Bulk"' % (
        series_id, exam_id)

        table = self._query(query_str)

        # first column is the exam number, second is the patient name
        bulk_files = table
        fpath = 'D:\\MIPIRC\\Localhost_SQLEXPRESS_patientdb'

        names = []
        for file in list(bulk_files):
            names.append(file[0].replace('FSM1', fpath))

        return names
