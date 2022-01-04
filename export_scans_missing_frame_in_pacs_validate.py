from PhilipsSeriesExport import scanner_db, export, pacs_utils
from shutil import rmtree
import os
import logging
from datetime import datetime

export_dir = 'E:\\export\\classic_series\\'
logging.basicConfig(filename = "G:\\Site\\LargeScanArchive-main\\" + "{:%Y-%m-%d}.log".format(datetime.now()), format='%(asctime)s %(message)s', filemode='w')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG) 

db = scanner_db.PatientDB()

# get series_iuid, pkg_name tuple list of series in local drive
series_exported = {}
series_pkgs = [ f for f in os.listdir(export_dir) if f.endswith(".zip")]

for pkg in series_pkgs:
    pkg_name = os.path.join(export_dir,pkg)
    os.remove(pkg_name)

# get series, frame number, patient name triple from patientDB in scanner
frame_num_scanner, s_oid = db.get_all_series_frame_number()

# if not complete in PACS, export to G://Export folder,
# if ready in PACS, delete the package
logger.debug("large series in scanner:")
for i, oid in enumerate(s_oid):
    fnum_s = frame_num_scanner[i]
    if int(fnum_s) > 16384:
        s_iuid, s_desc, patient_name = db.get_series_by_oid(s_oid[i])
        fnum_pacs = pacs_utils.check_frame_number_pacs(s_iuid[0])
        if fnum_pacs == '':
            fnum_pacs = '0'
        logger.debug("Series: " + patient_name[0] + ", series: " + s_desc[0] + ", frame number in scanner and PACS: " + fnum_s + "/" + fnum_pacs)
        # export series lacking frames and not in local drive
        if int(fnum_pacs) < int(fnum_s) and s_iuid[0] not in series_exported.keys():
            logger.debug("PACS missing frames, exporting...")
            seriesid, examid, patientid = db.get_OIDs_by_iuid(s_iuid[0])
            plf = export.PhilipsLogFile()
            pe = plf.extract_exam(examid[0])
            file_list, name = pe.collect_series_files(seriesid[0])
            export.zip_and_clean(file_list, s_iuid[0])








