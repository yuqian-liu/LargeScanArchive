import os
import subprocess
import re
import datetime
import struct
import zipfile
from shutil import copyfile, copytree, rmtree
import xml.etree.ElementTree as et
from . import scanner_db

# par/rec directories 
par_rec_dir = 'G:\patch\pride\\tempinputseries\\'
img_out_dir = 'G:\patch\pride\\tempoutputseries\\'
xmlleacher = '"c:\Program Files (x86)\PMS\Mipnet91x64\pridexmlleacher_win_cs.exe"'
dicomleacher = '"c:\Program Files (x86)\PMS\Mipnet91x64\prideimportexport_win_cs.exe"'

# folders and temporary files
export_dir = 'E:\\export\\classic_series\\'

# default log file name
default_log_file = 'G:\log\logcurrent.log'

# string search term for the start of each exam
exam_start_string = "LoadExamCard\(EXAMINATION_\d+_\d+\) operation started"

log_start_line = 'SingleScan members:'
log_stop_line = 'Performance Logging \[ScanExec\] 0 end'

def export_exam(exam):
    """Interface to export all series in an exam"""
    series = exam.extract_all_series()
    
    for series_id in series:
        print(" ")
        print("Collecing all files for: ", series_id)
        export_series(exam,series_id)

def export_series(exam,series_id):
    """Interface to a single series"""
    file_list,name = exam.collect_series_files(series_id)
    zip_and_clean(file_list,name)
    
def zip_and_clean(file_list,name):
    """Adds all files in `file_list` to a zip file, `name` """

    zip_name = os.path.join(export_dir,name)
    
    print('Writing zip file to: ' + zip_name)
    zf = zipfile.ZipFile(zip_name + '.zip', 'w')
    for file in file_list:
        try:
            #zf.write(file,arcname=os.path.basename(file))
            zf.write(file,arcname=file)
        except:
            warning('skipping file not found: %s' % file)
    zf.close()
    print('done!')
    print(' ')
    
    for file in file_list:
        try:
            os.remove(file)
        except:
            pass
    
# easy function to write files
def write_file(filename,lines):
    """safely opens and writes a list of strings to a file"""
    with open(filename,'w') as fil:
        fil.writelines(lines)

# make warnings show up in color
def warning(line):
    """make warnings show up in yellow on the command prompt"""
    before = '\033[93m'
    after = '\033[0m'
    print(before + line + after)

class FileOutput:
    XMLREC = False
    DATALIST = False
    LOG = False
    LABRAW = False
    DICOM = True
    SIN = False

        
db = scanner_db.PatientDB()

class PhilipsLogFile:
    """A class that loads and parses any Philips log file"""

    def __init__(self,log_filename=default_log_file):
        self.log_filename = log_filename 
        self.log_lines = []
    
    def extract_exam(self,exam_id):
        """Search the current log file for the start and end of a given exam id. 
        A PhilipsExam object is returned"""

        # the first thing to do is to read in the log file if it hasn't already
        if not self.log_lines:
            with open(self.log_filename, encoding="latin-1") as fil:
                self.log_lines = fil.readlines()
            fil.close()
        
        reg_ex = re.compile(exam_start_string)
        # next, find the line index in the log file of the start of each exam
        exam_start_indexes = [i for i,line in enumerate(self.log_lines) if reg_ex.search(line)]
        
        # find the end of the exam index
        exam_end_indexes = exam_start_indexes[1:] + [len(self.log_lines)-1]
        
        # parse the exam ids from each exam
        eids = [reg_ex.findall(self.log_lines[idx])[0].split('_')[1] for idx in exam_start_indexes]
        
        # next: get only the log lines that match this exam_id
        exam_log_lines = []
        for i,id in enumerate(eids):
            if id == exam_id:
                exam_log_lines.extend(self.log_lines[exam_start_indexes[i]:exam_end_indexes[i]])
        
        return PhilipsExam(exam_id, exam_log_lines)

class PhilipsExam:
    
    def __init__(self, exam_id, log_lines):
        self.exam_id = exam_id
        self.log_lines = log_lines
        
    def extract_series_name(self,series_id):
        """Generates a common filename from series information"""

        eid,pid,enames = db.extract_exams()
        sid,snames = db.extract_series(self.exam_id)
        
        exams = dict(zip(eid,enames))
        series = dict(zip(sid,snames))
        
        return exams[self.exam_id].replace(" ","_") + '_' + series[series_id].replace(" ","_")
    
    def extract_all_series(self):
        # find the set of series in this exam with rec data
        
        # raw_ex = re.compile('Identification of \.RAW series is MRSERIES_(\d*)_' + self.exam_id)
        rec_ex = re.compile('Identification of \.REC series is MRSERIES_(\d*)_' + self.exam_id)
        
        series = [rec_ex.search(line).group(1) for line in self.log_lines if rec_ex.search(line)]
        
        return series

    
    def extract_sin(self,series_id):
        """extracts the sin file of a given `series_id` from the lines of the log file"""

        # use only log lines relevant to the current series
        log_lines = self.extract_log(series_id)
        
        # remove log entries that are not from the reconstructor
        reg_ex = re.compile('RECON')
        recon_lines = [line for line in log_lines if reg_ex.search(line)]
        
        # find the MRSERIES statements before the sin file output, and find the recon id number
        series_start_string = '(\[\s*\d+\]) Created Series with ROID:MRSERIES_' + series_id + '_' + self.exam_id; 
        reg_ex = re.compile(series_start_string)
        recon_id = [reg_ex.search(line).group(1) for line in recon_lines if reg_ex.search(line)]
        if len(recon_id) is not 1:
            Exception("Something went wrong reading the sin file from log")
        
        # remove lines with other recon ids
        reg_ex = re.compile(re.escape(recon_id[0]))
        id_lines = [line for line in recon_lines if reg_ex.search(line)]
        
        # use only lines that start with three digits or other texts
        reg_ex = re.compile('((\d+\s\d+\s\d+|Reconstruction para|Derived value)[\s\S]*)')
        sin_lines = []
        for line in id_lines:
            result = reg_ex.search(line)
            if result:
                if re.search('Reconstruction para|Derived value',line):
                    sin_lines.append('\n' + result.group(1) + '\n')
                else:
                    sin_lines.append(result.group(1))
        
        
        return sin_lines

    def extract_raw_series(self,series_id):
        
        # save time by only looking in recon log lines
        reg_ex = re.compile('RECON')
        recon_lines = [line for line in self.log_lines if reg_ex.search(line)]
        
        # the .RAW has a different series roid than the .REC. First, we must find the matching roid
        rec_series = 'rec MRSERIES_' + series_id + '_' + self.exam_id
        
        rec_ex_r53 = re.compile('created new series for exam-roid EXAMINATION_(\d*)_(\d*) containing  raw MRSERIES_(\d*)_(\d*) ' + rec_series) # R5.3
        rec_ex_r55 = re.compile('created new series for exam-roid EXAMINATION_(\d*)_(\d*) containing  raw MRSERIES_(\d*)_(\d*) cpx MRSERIES_(\d*)_(\d*) ' + rec_series) # R5.5
        
        rec_line_idx = [idx for idx,line in enumerate(recon_lines) if (rec_ex_r53.search(line) or rec_ex_r55.search(line)) ]

        raw_sid = None
        if len(rec_line_idx) > 0:
            result = rec_ex_r53.search(recon_lines[rec_line_idx[-1]])
            if not result:
                result = rec_ex_r55.search(recon_lines[rec_line_idx[-1]])

            try:
                raw_sid = result.group(3)
            except: 
                pass
            
        return raw_sid
    
    def extract_datalist(self,series_id):
        """Parses the log file to find an exported data/list"""
        
        # save time by only looking in recon log lines
        reg_ex = re.compile('RECON')
        recon_lines = [line for line in self.log_lines if reg_ex.search(line)]
        
        # the .RAW has a different series roid than the .REC. First, we must find the matching roid
        raw_sid = self.extract_raw_series(series_id)
        if not raw_sid:
            return # nothing to do here
        
        # find .list output lines
        reg_ex = re.compile('Creating file (.*)\.list as export list file')
        list_idx = [i for i,line in enumerate(recon_lines) if reg_ex.search(line)]
        
        # iterate backwards to see if this .list file matches the current series
        raw_ex = re.compile('Identification of .RAW series is MRSERIES_' + raw_sid + '_' + self.exam_id)
        filename = None
        prev_fname_list = []
        for i in reversed(list_idx):
            # the current file name is:
            reg_result = reg_ex.search(recon_lines[i])
            fname = reg_result.group(1)
            
            # assume the roid isn't found until it is
            found = False
            
            j = 1
            while j < 1000:
                result = None
                try:
                    result = raw_ex.search(recon_lines[i+j])
                except:
                    pass
                if result:
                    found = True
                    break
                j += 1
            
            if found:
                if fname in prev_fname_list:
                    warning('.data/.list has not been exported')
                    warning('filename has been overriden: ' + fname)
                    break
                else:
                    filename = fname
                    break
            
            prev_fname_list.append(fname)
         
        return filename
    
    def extract_log(self,series_id):
        """Extract from the log file only lines between the start and end of a given series id"""

        # loop over the log lines, looking for the start string
        start_ex = re.compile(log_start_line)
        stop_ex = re.compile(log_stop_line)
        found_ex = re.compile('MRSERIES_' + series_id + "_" + self.exam_id)
        
        start_line = 0
        stop_line = 0
        found = False
        
        for i,line in enumerate(self.log_lines):
            if start_ex.search(line):
                start_line = i
            
            if found_ex.search(line):
                found = True
            
            if stop_ex.search(line):
                stop_line = i+1
                if found:
                    break
        
        log = []
        if found:
            log = self.log_lines[start_line:stop_line]
        
        return log

    def extract_dicom(self,series_id):
        """Uses the classic dicom leacher to extract dicom files"""

        series_roid = 'MRSERIES_' + series_id + '_' + self.exam_id
        
        # first, clean up the par/rec directory
        #command = 'del /Q "' + par_rec_dir + '*"'
        #subprocess.run(command,shell=True)
        rmtree(par_rec_dir,ignore_errors=True)
        os.makedirs(par_rec_dir)
        
        command = dicomleacher + ' ' + series_roid + ' ' + 'DICOM'
        #print(command)
        subprocess.run(command)
        
        dir_filename = os.path.join(par_rec_dir,'DICOMDIR')
        if not os.path.exists(dir_filename):
            dir_filename = None
        
        dcm_filedir = os.path.join(par_rec_dir,'DICOM')
        if not os.path.exists(dcm_filedir):
            dcm_filedir = None
        
        return dcm_filedir,dir_filename

    def extract_parrec(self,series_id):
        """Uses the par/rec leacher to extract par/rec files"""

        series_roid = 'MRSERIES_' + series_id + '_' + self.exam_id
        default_filename = os.path.join(export_dir,series_roid)
        
        # first, clean up the par/rec directory
        #command = 'del /Q "' + par_rec_dir + '*"'
        #subprocess.run(command,shell=True)
        rmtree(par_rec_dir,ignore_errors=True)
        os.makedirs(par_rec_dir)
        
        command = xmlleacher + ' ' + series_roid
        #print(command)
        subprocess.run(command)
        
        base_filename = 'DBIEX'
        xml_filename = os.path.join(par_rec_dir,base_filename + '.XML')
        if not os.path.exists(xml_filename):
            xml_filename = None
        
        rec_filename = os.path.join(par_rec_dir,base_filename + '.REC')
        if not os.path.exists(rec_filename):
            rec_filename = None
        
        return rec_filename,xml_filename
        
    def extract_labraw(self,series_id):
        """Probes the patient DB to look for lab/raw files of a given series id.
        Returns the lab and raw filenames"""

        # the .RAW has a different series roid than the .REC. First, we must find the matching roid
        raw_sid = self.extract_raw_series(series_id)
        if not raw_sid:
            return None,None # nothing to do here
        files = db.extract_bulk_files(self.exam_id,raw_sid)
        
        lab_file = None
        raw_file = None
        for file in files:
            with open(file, "rb") as f:
                bytes = f.read(512)
                
                lab_result = bytes[14:16].hex()
                if lab_result == "017f" or lab_result == "057f":
                    lab_file = file
                    continue
                    
                raw_result = bytes[20:22].hex()
                if ( (lab_result == "0000") and 
                        ((raw_result == "0a00") or
                        ( raw_result == "0900") or 
                        ( raw_result == "0800") or 
                        ( raw_result == "0700") or 
                        ( raw_result == "0600") )):
                    raw_file = file
                    continue

        return lab_file,raw_file

    def collect_series_files(self,series_id):
        """Look for and collect all possible data files associated with a given series id"""

        file_list = []
        
        default_filename = self.extract_series_name(series_id)
        
        print('Collecting: '  + default_filename)
        
        if FileOutput.XMLREC:
            rec,xml = self.extract_parrec(series_id)
            if rec:
                copyfile(rec,default_filename + '.REC')
                file_list.append(default_filename + '.REC')
                print('.REC:  found')
            else:
                warning('.REC:  not found')
            if xml:
                copyfile(xml,default_filename + '.XML')
                file_list.append(default_filename + '.XML')
                print('.XML:  found')
            else:
                warning('.XML:  not found')
                
            rmtree(par_rec_dir,ignore_errors=True)
            os.makedirs(par_rec_dir)
            
        #file_list.extend([default_filename + '.REC',default_filename + '.XML'])
        
        # extract and write the sin file
        if FileOutput.SIN:
            sin = self.extract_sin(series_id)
            if sin:
                write_file(default_filename + '.SIN',sin)
                file_list.append(default_filename + '.SIN')
                print('.SIN:  found')
            else:
                warning('.SIN:  not found')
        
        # extract and write the log file
        if FileOutput.LOG:
            log = self.extract_log(series_id)
            if log:
                write_file(default_filename + '.LOG',log)
                file_list.append(default_filename + '.LOG')
                print('.LOG:  found')
            else:
                warning('.LOG:  not found')

        # extract and write the DICOM file
        if FileOutput.DICOM:
            rmtree('DICOM',ignore_errors=True)
            dcm_filedir,dir_filename = self.extract_dicom(series_id)
            if dcm_filedir:
                copyfile(dir_filename,'DICOMDIR')
                file_list.append('DICOMDIR')
                copytree(dcm_filedir,'DICOM')
                
                rmtree(par_rec_dir,ignore_errors=True)
                os.makedirs(par_rec_dir)
                for folders,subfolders,files in os.walk('DICOM'):
                    for file in files:
                        if file not in file_list:
                            file_list.append(folders + "\\" + file)
                print('.DCM:  found')
            else:
                warning('.DCM:  not found')
        
        # parse and copy the .data .list file
        if FileOutput.DATALIST:
            name = self.extract_datalist(series_id)
            if name:
                copyfile(name + '.data',default_filename + '.DATA')
                file_list.append(default_filename + '.DATA')
                copyfile(name + '.list',default_filename + '.LIST')
                file_list.append(default_filename + '.LIST')
                print('.DATA: found')
                print('.LIST: found')
            else:
                warning('.DATA: not found')
                warning('.LIST: not found')
        
        # parse and copy the .lab .raw file
        if FileOutput.LABRAW:
            lab,raw = self.extract_labraw(series_id)
            if lab:
                copyfile(lab,default_filename + '.LAB')
                file_list.append(default_filename + '.LAB')
                print('.LAB:  found')
            else:
                warning('.LAB:  not found')
            if raw:
                copyfile(raw,default_filename + '.RAW')
                file_list.append(default_filename + '.RAW')
                print('.RAW:  found')
            else:
                warning('.RAW:  not found')
            
        return file_list, default_filename
